"""
Main application window for Previewless Insight Viewer.
"""
from pathlib import Path
from typing import Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QStatusBar, QMenuBar, QMenu, QPushButton,
    QListWidget, QTableWidget, QTableWidgetItem, QProgressBar,
    QFileDialog, QGroupBox, QHeaderView, QLineEdit, QMessageBox,
    QComboBox, QDialog, QDialogButtonBox, QRadioButton, QButtonGroup,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QSize, QTimer, QThread, QMetaObject, Q_ARG, Signal, QUrl
from PySide6.QtGui import QAction, QColor, QBrush, QFont, QDesktopServices

from src.core.config import ConfigManager
from src.models.database import Database
from src.services.file_watcher import FileWatcherService
from src.services.queue_manager import QueueManager, QueueItemStatus, DEFAULT_QUEUE_PRIORITY
from src.services.ocr_adapter import OCRAdapter
from src.services.llm_adapter import OllamaAdapter
from src.services.processing_orchestrator import ProcessingOrchestrator, ProcessingState
from src.ui.review_dialog import ReviewDialog
from src.ui.ai_model_dialog import AIModelDialog
from src.utils.logging_utils import get_logger
from src.ui.menu_handlers import (
    _refresh_all_views, _toggle_always_on_top, _manage_watch_folders,
    _add_watch_folder_from_dialog, _remove_watch_folder_from_dialog,
    _manage_tags, _add_files_to_queue, _show_processing_options,
    _show_db_maintenance, _show_help_center, _show_quickstart,
    _check_for_updates, _show_about, _view_processed_files
)
from src.ui.widgets import ProcessingControlsWidget, ProcessingControlsIntegration, ProcessingState


logger = get_logger("ui.main_window")


class PrioritySelectionDialog(QDialog):
    """Dialog prompting the user to choose a priority level."""

    def __init__(self, palette: dict, options: list, default_value: int, parent=None):
        super().__init__(parent)
        self._palette = palette
        self._options = options
        self._default_value = default_value
        self.setModal(True)
        self.setWindowTitle("Choose Priority")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        self.header_label = QLabel("How should these files be prioritized?")
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)

        self.button_group = QButtonGroup(self)

        for index, option in enumerate(self._options):
            icon = option.get("icon", "")
            label = option["label"]
            description = option.get("description", "")
            value = option["value"]

            radio = QRadioButton(f"{icon} {label}".strip())
            radio.setProperty("priorityValue", value)
            if value == self._default_value:
                radio.setChecked(True)
            elif index == 0 and self.button_group.checkedButton() is None:
                radio.setChecked(True)

            self.button_group.addButton(radio)
            layout.addWidget(radio)

            if description:
                description_label = QLabel(description)
                description_label.setObjectName("priorityDescription")
                description_label.setWordWrap(True)
                layout.addWidget(description_label)

        layout.addSpacing(8)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Add to Queue")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancel")
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self._apply_stylesheet()

    def selected_priority(self) -> int:
        """Return the selected priority value."""
        for button in self.button_group.buttons():
            if button.isChecked():
                return button.property("priorityValue")
        return self._default_value

    def set_message(self, message: str) -> None:
        """Update the dialog header message."""
        self.header_label.setText(message)

    def _apply_stylesheet(self):
        """Apply dialog styling based on the shared palette."""
        palette = self._palette
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {palette['surface']};
                color: {palette['text_primary']};
            }}
            QLabel {{
                color: {palette['text_secondary']};
            }}
            QLabel#priorityDescription {{
                font-size: 11px;
                margin-left: 24px;
            }}
            QRadioButton {{
                color: {palette['text_primary']};
                spacing: 8px;
                padding: 6px 4px;
            }}
            QRadioButton:hover {{
                background-color: {palette['hover']};
                border-radius: 6px;
            }}
            QRadioButton:focus-visible {{
                outline: 2px solid {palette['focus']};
                outline-offset: 2px;
            }}
            QDialogButtonBox QPushButton {{
                background-color: {palette['accent']};
                color: {palette['text_primary']};
                border: 1px solid {palette['accent']};
                border-radius: 6px;
                padding: 6px 16px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {palette['selected_hover']};
            }}
            QDialogButtonBox QPushButton:pressed {{
                background-color: {palette['pressed']};
            }}
            QDialogButtonBox QPushButton:focus-visible {{
                outline: 2px solid {palette['focus']};
                outline-offset: 2px;
            }}
            QDialogButtonBox QPushButton:disabled {{
                background-color: {palette['surface_alt']};
                border-color: {palette['dividers']};
                color: {palette['text_disabled']};
            }}
            """
        )


class MainWindow(QMainWindow):
    """Main application window."""
    
    APP_PALETTE = {
        "canvas": "#0B1220",
        "surface": "#0F1B2D",
        "surface_alt": "#12233B",
        "hover": "#16304B",
        "pressed": "#183454",
        "selected": "#183C73",
        "selected_hover": "#1B447F",
        "accent": "#2563EB",
        "focus": "#60A5FA",
        "text_primary": "#E6F0FF",
        "text_secondary": "#ADC2E8",
        "text_disabled": "#7A8AAA",
        "dividers": "#24314A",
        "alert_success": "#22C55E",
        "alert_warning": "#F97316",
        "alert_error": "#EF4444",
    }

    # Backwards compatibility while migrating existing queue styling helpers
    QUEUE_PALETTE = APP_PALETTE

    STATUS_COLORS = {
        "info": APP_PALETTE["accent"],
        "success": APP_PALETTE["alert_success"],
        "warning": APP_PALETTE["alert_warning"],
        "error": APP_PALETTE["alert_error"],
    }

    QUEUE_PRIORITY_LEVELS = [
        {"label": "High Priority", "value": 10, "icon": "🔥", "description": "Process these files first."},
        {"label": "Normal Priority", "value": DEFAULT_QUEUE_PRIORITY, "icon": "●", "description": "Balanced throughput for most batches."},
        {"label": "Low Priority", "value": 0, "icon": "⏳", "description": "Handle after higher priority work."},
    ]

    PRIORITY_LABELS = {
        10: ("🔥 High", "Process next"),
        DEFAULT_QUEUE_PRIORITY: ("● Normal", "Standard flow"),
        0: ("⏳ Low", "Background"),
    }

    # Signals to control processing on worker thread
    start_processing_signal = Signal()
    pause_processing_signal = Signal()
    resume_processing_signal = Signal()
    stop_processing_signal = Signal()
    retry_failed_signal = Signal()
    
    # Signal for AI status updates (thread-safe)
    ai_status_changed = Signal(bool)
    
    # Menu handler methods (imported from menu_handlers.py)
    _refresh_all_views = _refresh_all_views
    _toggle_always_on_top = _toggle_always_on_top
    _manage_watch_folders = _manage_watch_folders
    _add_watch_folder_from_dialog = _add_watch_folder_from_dialog
    _remove_watch_folder_from_dialog = _remove_watch_folder_from_dialog
    _manage_tags = _manage_tags
    _add_files_to_queue = _add_files_to_queue
    _show_processing_options = _show_processing_options
    _show_db_maintenance = _show_db_maintenance
    _show_help_center = _show_help_center
    _show_quickstart = _show_quickstart
    _check_for_updates = _check_for_updates
    _show_about = _show_about
    _view_processed_files = _view_processed_files
    
    def __init__(self, portable_root: Path, config_manager: ConfigManager, database: Database):
        """
        Initialize main window.
        
        Args:
            portable_root: Path to portable root directory
            config_manager: Configuration manager instance
            database: Database instance
        """
        super().__init__()
        
        self.portable_root = portable_root
        self.config = config_manager
        self.db = database
        
        # Glow animation state for queue badge
        self._glow_intensity = 0
        self._glow_direction = 1
        self._glow_timer = QTimer()
        self._glow_timer.timeout.connect(self._animate_queue_glow)
        self._base_tab_bar_style = ""
        
        # AI model status
        self._ai_status_ok = False
        self._ai_status_timer = QTimer()
        self._ai_status_timer.timeout.connect(self._check_ai_status)
        self._ai_status_timer.start(30000)  # Check every 30 seconds
        
        # Processing performance tracking
        self._processing_start_time = None
        self._pause_time = None  # Track when processing was paused
        self._paused_elapsed_seconds = 0  # Track total elapsed time when paused
        self._last_progress_time = None
        self._processing_speed = 0.0  # Files per second
        self._files_processed_in_batch = 0
        
        # Current file processing tracking
        self._current_processing_file = None
        self._file_progress_bars = {}  # Maps file_path to progress bar widget
        
        # Processing activity indicator
        self._activity_frame = 0
        self._activity_timer = QTimer()
        self._activity_timer.timeout.connect(self._animate_processing_activity)
        
        # Worker thread for processing
        self._processing_thread = None

        # Queue priority controls
        self.priority_combo: Optional[QComboBox] = None
        self.priority_apply_btn: Optional[QPushButton] = None

        # Processing controls integration
        self.processing_controls_integration: Optional[ProcessingControlsIntegration] = None
        self.new_processing_controls: Optional[ProcessingControlsWidget] = None
        self._using_new_controls: bool = False
        self._last_progress_update: float = 0  # Throttle progress updates

        # Initialize services
        self._init_services()

        # Window properties
        self.setWindowTitle("Previewless Insight Viewer")
        self.setMinimumSize(QSize(1200, 800))

        # Initialize UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Start file watcher
        self.file_watcher.start_watching()

        logger.info("Main window initialized")
    
    def _init_services(self):
        """Initialize all services."""
        # File watcher
        self.file_watcher = FileWatcherService(self.config, self.db)
        
        # Queue manager
        self.queue_manager = QueueManager(self.db)
        
        # OCR adapter
        try:
            self.ocr_adapter = OCRAdapter(self.config)
        except RuntimeError as e:
            logger.warning(f"OCR adapter initialization failed: {e}")
            self.ocr_adapter = None
        
        # LLM adapter
        self.llm_adapter = OllamaAdapter(self.config)
        
        # Processing orchestrator
        if self.ocr_adapter and self.llm_adapter:
            self.orchestrator = ProcessingOrchestrator(
                self.config,
                self.db,
                self.queue_manager,
                self.ocr_adapter,
                self.llm_adapter
            )
            
            # Move orchestrator to worker thread
            self._processing_thread = QThread()
            self.orchestrator.moveToThread(self._processing_thread)
            self._processing_thread.start()
            
            logger.info("Processing orchestrator initialized on worker thread")
        else:
            logger.warning("Processing orchestrator not available (missing OCR or LLM)")
            self.orchestrator = None
        
        logger.info("Services initialized")
    
    def _init_ui(self) -> None:
        """Initialize user interface."""
        # Create menu bar
        self._create_menu_bar()
        
        # Create central widget with tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create prominent processing status bar at top
        self._create_processing_status_bar()
        main_layout.addWidget(self.processing_status_bar)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self._apply_tab_widget_theme()
        main_layout.addWidget(self.tabs)
        
        # Add tabs (removed Processing tab - now in top bar)
        self.tabs.addTab(self._create_watch_tab(), "📁 Watch")
        self.tabs.addTab(self._create_queue_tab(), "📋 Queue")
        self.tabs.addTab(self._create_results_tab(), "📊 Results")
        
        # Notification system now uses status bar, no separate banner needed
        
        # Create status bar
        self._create_status_bar()

        # Apply overarching styling once components are in place
        self._apply_global_theme()
        
        # Auto-refresh timer to prevent UI lockups
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh_ui)
        self._refresh_timer.start(1000)  # Refresh every second
    
    def _create_processing_status_bar(self) -> None:
        """Create prominent processing status bar at top of window."""
        colors = self.APP_PALETTE
        self.processing_status_bar = QWidget()
        self.processing_status_bar.setObjectName("processingStatusBar")
        self.processing_status_bar.setMinimumHeight(120)

        bar_layout = QVBoxLayout(self.processing_status_bar)
        bar_layout.setSpacing(12)
        bar_layout.setContentsMargins(16, 16, 16, 16)

        # Top row: Status and controls
        top_row = QHBoxLayout()

        status_container = QVBoxLayout()
        status_container.setSpacing(4)
        self.proc_status_label = QLabel("⚙️ IDLE")
        self.proc_status_label.setObjectName("processingStatusTitle")
        status_container.addWidget(self.proc_status_label)

        self.proc_current_file_label = QLabel("No file processing")
        self.proc_current_file_label.setObjectName("processingStatusSubtitle")
        status_container.addWidget(self.proc_current_file_label)

        top_row.addLayout(status_container, 1)

        # New modern processing controls
        self._setup_new_processing_controls(top_row)

        bar_layout.addLayout(top_row)

        # Progress bar with detailed format (prominent)
        self.proc_progress = QProgressBar()
        self.proc_progress.setMinimum(1)  # Start from 1 instead of 0
        self.proc_progress.setFormat("%v / %m files (%p%) • Processing...")
        self.proc_progress.setMinimumHeight(36)
        self.proc_progress.setTextVisible(True)
        self._set_progress_bar_style(
            self.proc_progress,
            chunk_color=colors['accent'],
            border_color=colors['accent'],
            text_color=colors['text_primary'],
        )

        self._progress_pulse_timer = QTimer()
        self._progress_pulse_timer.setInterval(800)
        self._progress_pulse_timer.timeout.connect(self._pulse_progress_bar)
        self._progress_pulse_effect = 0
        bar_layout.addWidget(self.proc_progress)

        # Processing speed and ETA row
        speed_row = QHBoxLayout()
        speed_row.setSpacing(16)

        self.proc_stage_label = QLabel("🔍 Stage: --")
        self.proc_stage_label.setProperty("role", "metric")
        speed_row.addWidget(self.proc_stage_label)

        self.proc_elapsed_label = QLabel("⏳ Elapsed: --")
        self.proc_elapsed_label.setProperty("role", "metric")
        speed_row.addWidget(self.proc_elapsed_label)

        self.proc_speed_label = QLabel("⚡ Speed: --")
        self.proc_speed_label.setProperty("role", "metric")
        speed_row.addWidget(self.proc_speed_label)

        self.proc_eta_label = QLabel("⏱️ ETA: --")
        self.proc_eta_label.setProperty("role", "metric")
        speed_row.addWidget(self.proc_eta_label)

        speed_row.addStretch()
        bar_layout.addLayout(speed_row)

        # Bottom row: Statistics
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self.proc_processed_label = QLabel("✓ Processed: 0")
        self.proc_processed_label.setProperty("role", "stat")
        self.proc_processed_label.setProperty("variant", "success")
        stats_row.addWidget(self.proc_processed_label)

        self.proc_failed_label = QLabel("✗ Failed: 0")
        self.proc_failed_label.setProperty("role", "stat")
        self.proc_failed_label.setProperty("variant", "danger")
        stats_row.addWidget(self.proc_failed_label)

        self.proc_skipped_label = QLabel("⊘ Skipped: 0")
        self.proc_skipped_label.setProperty("role", "stat")
        self.proc_skipped_label.setProperty("variant", "warning")
        stats_row.addWidget(self.proc_skipped_label)

        stats_row.addStretch()
        bar_layout.addLayout(stats_row)

        self._apply_processing_bar_theme()
    
    def _apply_processing_bar_theme(self) -> None:
        colors = self.APP_PALETTE
        self.processing_status_bar.setStyleSheet(
            f"""
            QWidget#processingStatusBar {{
                background-color: {colors['surface_alt']};
                border: 1px solid {colors['dividers']};
                border-radius: 12px;
            }}
            QLabel#processingStatusTitle {{
                color: {colors['text_primary']};
                font-size: 18pt;
                font-weight: 600;
            }}
            QLabel#processingStatusSubtitle {{
                color: {colors['text_secondary']};
                font-size: 11pt;
            }}
            QLabel[role="metric"] {{
                color: {colors['text_secondary']};
                font-size: 10pt;
                font-weight: 500;
            }}
            QLabel[role="stat"] {{
                color: {colors['text_secondary']};
                font-size: 10pt;
                font-weight: 600;
            }}
            QLabel[variant="success"] {{
                color: {colors['alert_success']};
            }}
            QLabel[variant="warning"] {{
                color: {colors['alert_warning']};
            }}
            QLabel[variant="danger"] {{
                color: {colors['alert_error']};
            }}
            """
        )

    def _apply_watch_theme(self, tab: QWidget) -> None:
        colors = self.APP_PALETTE
        tab.setStyleSheet(
            f"""
            QWidget#watchTab {{
                background-color: {colors['canvas']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
            }}
            QLabel#watchHeader {{
                color: {colors['text_primary']};
                font-size: 18px;
                font-weight: 600;
            }}
            QLabel[variant="warning"] {{
                color: {colors['alert_warning']};
                font-weight: 600;
            }}
            """
        )

    def _apply_results_theme(self, tab: QWidget) -> None:
        colors = self.APP_PALETTE
        tab.setStyleSheet(
            f"""
            QWidget#resultsTab {{
                background-color: {colors['canvas']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
            }}
            QLabel#resultsHeader {{
                color: {colors['text_primary']};
                font-size: 18px;
                font-weight: 600;
            }}
            QLabel#searchLabel {{
                color: {colors['text_secondary']};
            }}
            QLabel#countLabel {{
                color: {colors['text_secondary']};
                font-weight: 500;
            }}
            QLabel#countValue {{
                color: {colors['text_primary']};
            }}
            """
        )

    def _apply_global_theme(self) -> None:
        colors = self.APP_PALETTE
        if self.central_widget is not None:
            self.central_widget.setObjectName("mainViewport")
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {colors['canvas']};
                color: {colors['text_primary']};
            }}
            QWidget#mainViewport {{
                background-color: {colors['canvas']};
            }}
            QMenuBar {{
                background-color: {colors['surface']};
                color: {colors['text_secondary']};
            }}
            QMenuBar::item:selected {{
                background-color: {colors['hover']};
                color: {colors['text_primary']};
            }}
            QToolTip {{
                background-color: {colors['surface_alt']};
                color: {colors['text_primary']};
                border: 1px solid {colors['dividers']};
            }}
            """
        )

    def _apply_tab_widget_theme(self) -> None:
        colors = self.APP_PALETTE
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {colors['dividers']};
                border-radius: 10px;
                padding: 6px;
                background-color: {colors['surface']};
            }}
            """
        )
        self._base_tab_bar_style = (
            f"""
            QTabBar::tab {{
                background-color: {colors['surface']};
                color: {colors['text_secondary']};
                padding: 8px 16px;
                border: 1px solid {colors['surface']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin: 0 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['surface_alt']};
                color: {colors['text_primary']};
                border-color: {colors['accent']};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                background-color: {colors['hover']};
                color: {colors['text_primary']};
            }}
            """
        )
        self.tabs.tabBar().setStyleSheet(self._base_tab_bar_style)

    def _set_processing_status(self, text: str, variant: str = "primary") -> None:
        colors = self.APP_PALETTE
        color_map = {
            "primary": colors['text_primary'],
            "info": colors['accent'],
            "success": colors['alert_success'],
            "warning": colors['alert_warning'],
            "error": colors['alert_error'],
        }
        self.proc_status_label.setText(text)
        if variant == "primary":
            self.proc_status_label.setStyleSheet("")
        else:
            color = color_map.get(variant, colors['text_primary'])
            self.proc_status_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {color};
                    font-size: 18pt;
                    font-weight: 600;
                    background: transparent;
                }}
                """
            )

    def _auto_refresh_ui(self):
        """Auto-refresh UI elements to prevent lockups."""
        try:
            # Process pending events to keep UI responsive
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Refresh queue count if items exist
            if hasattr(self, 'queue_manager') and self.queue_manager:
                stats = self.queue_manager.get_statistics()
                pending_count = stats.get('pending', 0)
                if pending_count > 0 and not self._glow_timer.isActive():
                    self._glow_timer.start(50)
                elif pending_count == 0 and self._glow_timer.isActive():
                    self._glow_timer.stop()
        except Exception as e:
            # Silently ignore errors to prevent spam
            pass
    
    # Notification banner has been removed in favor of status bar notifications
    
    def _show_notification(self, message: str, notification_type: str = "info", auto_hide: int = 5000):
        """
        Show notification in the status bar.
        
        Args:
            message: Message to display
            notification_type: 'info', 'success', 'warning', or 'error'
            auto_hide: Auto-hide after milliseconds (0 = no auto-hide)
        """
        colors = self.STATUS_COLORS
        icon_map = {
            "success": "✓",
            "warning": "⚠",
            "error": "✕",
            "info": "ℹ",
        }
        status_color = colors.get(notification_type, colors["info"])
        icon = icon_map.get(notification_type, icon_map["info"])
        
        # Update status bar notification
        self.status_notification_icon.setText(icon)
        self.status_notification_message.setText(message)
        
        # Show close button if we're not auto-hiding
        self.status_notification_close.setVisible(auto_hide == 0)
        
        # Set colors for status bar notification
        background = self.APP_PALETTE['surface_alt']
        self.notification_area.setStyleSheet(
            f"""
            QWidget {{
                background-color: {background};
                border: 1px solid {status_color};
                border-radius: 6px;
                padding: 2px 6px;
            }}
            QLabel {{
                color: {status_color};
                font-weight: 600;
            }}
            """
        )
        
        # Auto-hide if requested
        if auto_hide > 0:
            QTimer.singleShot(auto_hide, self._hide_notification)
    
    def _hide_notification(self):
        """Clear notification from status bar."""
        self.status_notification_icon.setText("")
        self.status_notification_message.setText("")
        self.notification_area.setStyleSheet("")
        self.status_notification_close.setVisible(False)  # Hide close button
    
    def _setup_new_processing_controls(self, parent_layout: QHBoxLayout) -> None:
        """Setup new modern processing controls."""
        try:
            logger.info("Setting up new processing controls...")
            
            # Create integration helper
            self.processing_controls_integration = ProcessingControlsIntegration(self)
            
            # Create container for new controls
            controls_container = QWidget()
            controls_layout = QVBoxLayout(controls_container)
            controls_layout.setContentsMargins(0, 0, 0, 0)
            
            # Install new controls widget
            self.new_processing_controls = self.processing_controls_integration.install_new_controls(controls_container)
            
            # Hide old buttons since we have new controls
            self.processing_controls_integration.hide_old_buttons()
            
            # Add to parent layout
            parent_layout.addWidget(controls_container)
            
            # Connect state changes from orchestrator (will be connected later in _connect_signals)
            logger.info("New processing controls installed successfully")
            
            # Set a flag to indicate we're using new controls
            self._using_new_controls = True
            
        except Exception as e:
            logger.error(f"Failed to setup new processing controls: {e}", exc_info=True)
            # Fallback to create old controls if new ones fail
            self._using_new_controls = False
            self._create_fallback_controls(parent_layout)
            
    def _create_fallback_controls(self, parent_layout: QHBoxLayout) -> None:
        """Create fallback controls if new controls fail to load."""
        logger.info("Creating fallback processing controls")
        
        # Create simple fallback controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)

        self.proc_start_btn = QPushButton("▶ Start")
        self.proc_start_btn.clicked.connect(self._start_processing)
        self.proc_start_btn.setMinimumHeight(36)
        self._style_button(self.proc_start_btn, variant="primary")
        controls_layout.addWidget(self.proc_start_btn)

        self.proc_pause_btn = QPushButton("⏸ Pause")
        self.proc_pause_btn.clicked.connect(self._pause_processing)
        self.proc_pause_btn.setEnabled(False)
        self.proc_pause_btn.setMinimumHeight(36)
        self._style_button(self.proc_pause_btn, variant="warning")
        controls_layout.addWidget(self.proc_pause_btn)

        self.proc_stop_btn = QPushButton("⏹ Stop")
        self.proc_stop_btn.clicked.connect(self._stop_processing)
        self.proc_stop_btn.setEnabled(False)
        self.proc_stop_btn.setMinimumHeight(36)
        self._style_button(self.proc_stop_btn, variant="danger")
        controls_layout.addWidget(self.proc_stop_btn)

        self.proc_retry_btn = QPushButton("🔄 Retry")
        self.proc_retry_btn.clicked.connect(self._retry_failed)
        self.proc_retry_btn.setMinimumHeight(36)
        self._style_button(self.proc_retry_btn, variant="secondary")
        controls_layout.addWidget(self.proc_retry_btn)

        parent_layout.addLayout(controls_layout)
    
    def _update_control_buttons_safe(self, start_enabled=None, pause_enabled=None, 
                                   stop_enabled=None, retry_enabled=None):
        """Safely update control button states for both new and old control systems."""
        if self._using_new_controls:
            # New controls handle their own state through the orchestrator
            # No manual button state updates needed
            pass
        else:
            # Update old control buttons if they exist
            if start_enabled is not None and hasattr(self, 'proc_start_btn') and self.proc_start_btn:
                self.proc_start_btn.setEnabled(start_enabled)
            if pause_enabled is not None and hasattr(self, 'proc_pause_btn') and self.proc_pause_btn:
                self.proc_pause_btn.setEnabled(pause_enabled)
            if stop_enabled is not None and hasattr(self, 'proc_stop_btn') and self.proc_stop_btn:
                self.proc_stop_btn.setEnabled(stop_enabled)
            if retry_enabled is not None and hasattr(self, 'proc_retry_btn') and self.proc_retry_btn:
                self.proc_retry_btn.setEnabled(retry_enabled)
    
    def _create_watch_tab(self) -> QWidget:
        """Create Watch tab for folder management."""
        tab = QWidget()
        tab.setObjectName("watchTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Watched Folders")
        header_label.setObjectName("watchHeader")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Folder list
        self.folder_list = QListWidget()
        self.folder_list.setAlternatingRowColors(True)
        self._style_list_widget(self.folder_list)
        layout.addWidget(self.folder_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self._add_watch_folder)
        self._style_button(self.add_folder_btn, variant="primary")
        button_layout.addWidget(self.add_folder_btn)
        
        self.remove_folder_btn = QPushButton("Remove Folder")
        self.remove_folder_btn.clicked.connect(self._remove_watch_folder)
        self.remove_folder_btn.setEnabled(False)
        self._style_button(self.remove_folder_btn, variant="secondary")
        button_layout.addWidget(self.remove_folder_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setShortcut("F5")
        self.refresh_btn.clicked.connect(self._refresh_inventory)
        self._style_button(self.refresh_btn, variant="secondary")
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Inventory stats
        stats_group = QGroupBox("Inventory Statistics")
        self._style_group_box(stats_group)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(6)
        
        self.total_files_label = QLabel("Total Files: 0")
        stats_layout.addWidget(self.total_files_label)
        
        self.by_type_label = QLabel("By Type: -")
        stats_layout.addWidget(self.by_type_label)
        
        self.unanalyzed_label = QLabel("Unanalyzed: 0")
        self.unanalyzed_label.setProperty("variant", "warning")
        stats_layout.addWidget(self.unanalyzed_label)
        
        layout.addWidget(stats_group)
        
        # Load watched folders
        self._load_watched_folders()

        self._apply_watch_theme(tab)
        
        return tab
    
    def _create_queue_tab(self) -> QWidget:
        """Create Queue tab for processing queue management."""
        tab = QWidget()
        tab.setObjectName("queueTab")

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        header_layout = QHBoxLayout()
        header_label = QLabel("Processing Queue")
        header_label.setObjectName("queueHeader")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        self.queue_table = QTableWidget()
        self.queue_table.setObjectName("queueTable")
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(["File", "Type", "Status", "Progress", "Priority"])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.queue_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.setColumnWidth(3, 160)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.queue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setFocusPolicy(Qt.StrongFocus)
        self.queue_table.setShowGrid(True)
        layout.addWidget(self.queue_table)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.enqueue_btn = QPushButton("Enqueue Selected Files")
        self.enqueue_btn.clicked.connect(self._enqueue_files)
        button_layout.addWidget(self.enqueue_btn)
        
        self.dequeue_btn = QPushButton("Remove Selected")
        self.dequeue_btn.clicked.connect(self._dequeue_files)
        self.dequeue_btn.setEnabled(False)
        button_layout.addWidget(self.dequeue_btn)
        
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.clicked.connect(self._move_queue_up)
        self.move_up_btn.setEnabled(False)
        self.move_up_btn.setFixedWidth(42)
        button_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.clicked.connect(self._move_queue_down)
        self.move_down_btn.setEnabled(False)
        self.move_down_btn.setFixedWidth(42)
        button_layout.addWidget(self.move_down_btn)
        
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        button_layout.addWidget(self.clear_queue_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

        priority_layout = QHBoxLayout()
        priority_layout.setSpacing(12)
        priority_label = QLabel("Set Priority:")
        priority_layout.addWidget(priority_label)

        self.priority_combo = QComboBox()
        for option in self.QUEUE_PRIORITY_LEVELS:
            display_text = f"{option['icon']} {option['label']}"
            self.priority_combo.addItem(display_text, option['value'])
        self.priority_combo.setCurrentIndex(self._priority_index_for_value(DEFAULT_QUEUE_PRIORITY))
        self.priority_combo.setToolTip("Choose the priority applied to selected queue items.")
        priority_layout.addWidget(self.priority_combo)

        self.priority_apply_btn = QPushButton("Apply Priority")
        self.priority_apply_btn.clicked.connect(self._set_selected_priority)
        self.priority_apply_btn.setEnabled(False)
        priority_layout.addWidget(self.priority_apply_btn)
        priority_layout.addStretch()
        layout.addLayout(priority_layout)
        
        self.queue_progress = QProgressBar()
        self.queue_progress.setMinimum(1)
        self.queue_progress.setValue(1)
        self.queue_progress.setFormat("%v / %m items")
        layout.addWidget(self.queue_progress)

        self._apply_queue_theme(tab)
        
        return tab
    
    def _apply_queue_theme(self, tab: QWidget) -> None:
        """Apply shared queue styling to the tab and its widgets."""
        colors = self.APP_PALETTE

        tab.setStyleSheet(
            f"""
            QWidget#queueTab {{
                background-color: {colors['canvas']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
            }}
            QLabel#queueHeader {{
                color: {colors['text_primary']};
                font-size: 18px;
                font-weight: 600;
            }}
            """
        )

        self._style_table(self.queue_table, "queueTable")

        for button in (self.enqueue_btn, self.dequeue_btn, self.move_up_btn,
                        self.move_down_btn, self.clear_queue_btn, self.priority_apply_btn):
            variant = "primary" if button in (self.enqueue_btn, self.priority_apply_btn) else "secondary"
            if button is self.clear_queue_btn:
                variant = "danger"
            self._style_button(button, variant=variant)

        self._style_combo(self.priority_combo)
        self._set_progress_bar_style(self.queue_progress)

    def _style_table(self, table: QTableWidget, object_name: str) -> None:
        colors = self.APP_PALETTE
        selector = f"QTableWidget#{object_name}"
        table.setStyleSheet(
            f"""
            {selector} {{
                background-color: {colors['surface']};
                alternate-background-color: {colors['surface_alt']};
                color: {colors['text_primary']};
                gridline-color: {colors['dividers']};
                selection-background-color: {colors['selected']};
                selection-color: {colors['text_primary']};
                border: 1px solid {colors['dividers']};
                border-radius: 8px;
            }}
            {selector}::item:hover:!selected {{
                background-color: {colors['hover']};
            }}
            {selector}::item:selected:hover {{
                background-color: {colors['selected_hover']};
            }}
            {selector}::item:focus {{
                outline: 2px solid {colors['focus']};
                outline-offset: 1px;
            }}
            QHeaderView::section {{
                background-color: {colors['surface_alt']};
                color: {colors['text_primary']};
                border: none;
                border-bottom: 1px solid {colors['dividers']};
                padding: 8px 10px;
            }}
            QTableCornerButton::section {{
                background-color: {colors['surface_alt']};
                border: none;
            }}
            """
        )
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.setAlternatingRowColors(True)

    def _style_button(self, button: QPushButton, *, variant: str = "secondary") -> None:
        colors = self.APP_PALETTE
        variants = {
            "primary": {
                "bg": colors['accent'],
                "hover": colors['selected_hover'],
                "pressed": colors['selected'],
                "border": colors['accent'],
                "text": colors['text_primary'],
            },
            "secondary": {
                "bg": colors['surface_alt'],
                "hover": colors['hover'],
                "pressed": colors['pressed'],
                "border": colors['dividers'],
                "text": colors['text_primary'],
            },
            "ghost": {
                "bg": "transparent",
                "hover": colors['hover'],
                "pressed": colors['pressed'],
                "border": "transparent",
                "text": colors['text_secondary'],
            },
            "danger": {
                "bg": colors['alert_error'],
                "hover": "#f05454",
                "pressed": "#d83b3b",
                "border": colors['alert_error'],
                "text": colors['text_primary'],
            },
            "warning": {
                "bg": colors['alert_warning'],
                "hover": "#fb8f1a",
                "pressed": "#d06d0e",
                "border": colors['alert_warning'],
                "text": colors['text_primary'],
            },
            "success": {
                "bg": colors['alert_success'],
                "hover": "#1ea558",
                "pressed": "#1b8c4b",
                "border": colors['alert_success'],
                "text": colors['text_primary'],
            },
        }

        style = variants.get(variant, variants['secondary'])
        disabled_bg = colors['surface']
        disabled_color = colors['text_disabled']

        if variant != "ghost" and button.minimumHeight() <= 0:
            button.setMinimumHeight(32)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {style['bg']};
                color: {style['text']};
                border: 1px solid {style['border']};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {style['hover']};
            }}
            QPushButton:pressed {{
                background-color: {style['pressed']};
            }}
            QPushButton:focus-visible {{
                outline: 2px solid {colors['focus']};
                outline-offset: 2px;
            }}
            QPushButton:disabled {{
                background-color: {disabled_bg};
                color: {disabled_color};
                border-color: {colors['dividers']};
            }}
            """
        )

    def _style_combo(self, combo: QComboBox) -> None:
        colors = self.APP_PALETTE
        combo.setMinimumWidth(220)
        combo.setMinimumHeight(32)
        combo.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['dividers']};
                border-radius: 6px;
                padding: 6px 10px;
            }}
            QComboBox:hover {{
                background-color: {colors['hover']};
            }}
            QComboBox:focus {{
                border: 1px solid {colors['accent']};
                outline: 2px solid {colors['focus']};
                outline-offset: 2px;
            }}
            QComboBox::drop-down {{
                background-color: {colors['surface_alt']};
                border-left: 1px solid {colors['dividers']};
                width: 26px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['surface']};
                border: 1px solid {colors['dividers']};
                selection-background-color: {colors['selected']};
                selection-color: {colors['text_primary']};
            }}
            """
        )

    def _style_line_edit(self, line_edit: QLineEdit) -> None:
        colors = self.APP_PALETTE
        line_edit.setMinimumHeight(32)
        line_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['dividers']};
                border-radius: 6px;
                padding: 6px 10px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
                outline: 2px solid {colors['focus']};
                outline-offset: 1px;
            }}
            QLineEdit:disabled {{
                background-color: {colors['surface_alt']};
                color: {colors['text_disabled']};
            }}
            """
        )

    def _style_list_widget(self, list_widget: QListWidget) -> None:
        colors = self.APP_PALETTE
        list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['dividers']};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {colors['selected']};
            }}
            QListWidget::item:hover {{
                background-color: {colors['hover']};
            }}
            """
        )

    def _style_group_box(self, group_box: QGroupBox) -> None:
        colors = self.APP_PALETTE
        group_box.setStyleSheet(
            f"""
            QGroupBox {{
                background-color: {colors['surface_alt']};
                border: 1px solid {colors['dividers']};
                border-radius: 10px;
                margin-top: 12px;
                padding: 12px;
            }}
            QGroupBox::title {{
                color: {colors['text_secondary']};
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px;
                background-color: {colors['surface_alt']};
            }}
            """
        )

    def _set_progress_bar_style(
        self,
        progress_bar: QProgressBar,
        *,
        chunk_color: Optional[str] = None,
        border_color: Optional[str] = None,
        text_color: Optional[str] = None,
    ) -> None:
        colors = self.APP_PALETTE
        progress_bar.setMinimumHeight(26)
        chunk = chunk_color or colors['accent']
        border = border_color or colors['dividers']
        text = text_color or colors['text_secondary']
        progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {colors['surface_alt']};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                text-align: center;
                font-weight: 500;
            }}
            QProgressBar::chunk {{
                background-color: {chunk};
                border-radius: 6px;
                margin: 1px;
            }}
            """
        )

    def _priority_index_for_value(self, value: int) -> int:
        for index, option in enumerate(self.QUEUE_PRIORITY_LEVELS):
            if option['value'] == value:
                return index
        return 0

    def _format_priority_text(self, priority: int) -> str:
        label, _ = self.PRIORITY_LABELS.get(priority, (f"Priority {priority}", ""))
        return f"{label} ({priority})"

    def _priority_detail_text(self, priority: int) -> str:
        detail = self.PRIORITY_LABELS.get(priority, ("", ""))[1]
        return detail or "Custom priority"

    def _row_color_for_priority(self, priority: int) -> str:
        colors = self.QUEUE_PALETTE
        if priority >= 10:
            return colors['pressed']
        if priority <= 0:
            return colors['surface_alt']
        return colors['surface']

    def _create_queue_table_item(self, text: str, *, secondary: bool = False) -> QTableWidgetItem:
        colors = self.QUEUE_PALETTE
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setForeground(QColor(colors['text_secondary' if secondary else 'text_primary']))
        return item

    def _create_queue_progress_widget(self, item) -> QProgressBar:
        progress_bar = QProgressBar()
        status = item.status
        
        # Special handling: if we're in PAUSED state, force any PROCESSING items to display as PENDING
        if status == QueueItemStatus.PROCESSING and hasattr(self, 'orchestrator') and self.orchestrator and \
           (self.orchestrator.state == ProcessingState.PAUSED or self.orchestrator.state == ProcessingState.PAUSING):
            # When paused, show any "processing" items as "pending" in the UI
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setFormat("Pending")
            self._set_progress_bar_style(progress_bar)
        elif status == QueueItemStatus.PROCESSING:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(5)
            progress_bar.setFormat("Processing...")
            self._set_progress_bar_style(progress_bar)
        elif status == QueueItemStatus.COMPLETED:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(100)
            progress_bar.setFormat("✓ Completed")
            self._set_progress_bar_style(progress_bar, text_color=self.APP_PALETTE['text_primary'])
        elif status == QueueItemStatus.FAILED:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(100)
            progress_bar.setFormat("✗ Failed")
            error_color = self.APP_PALETTE['alert_error']
            self._set_progress_bar_style(
                progress_bar,
                chunk_color=error_color,
                border_color=error_color,
                text_color=self.APP_PALETTE['text_primary'],
            )
        elif status == QueueItemStatus.SKIPPED:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setFormat("Skipped")
            self._set_progress_bar_style(progress_bar, chunk_color=self.APP_PALETTE['hover'])
        else:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setFormat("Pending")
            self._set_progress_bar_style(progress_bar)

        return progress_bar

    def _create_processing_tab(self) -> QWidget:
        """Create Processing tab for monitoring processing status."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Processing Status")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Status indicator
        self.processing_status_label = QLabel("Status: IDLE")
        self.processing_status_label.setStyleSheet("font-size: 12pt; padding: 8px;")
        layout.addWidget(self.processing_status_label)
        
        # Current file
        self.current_file_label = QLabel("Current File: -")
        layout.addWidget(self.current_file_label)
        
        # Progress bar
        self.processing_progress = QProgressBar()
        self.processing_progress.setMinimum(1)  # Start from 1 instead of 0
        self.processing_progress.setValue(1)    # Initial value of 1
        self.processing_progress.setFormat("%v / %m files processed")
        layout.addWidget(self.processing_progress)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.processed_label = QLabel("Processed: 0")
        stats_layout.addWidget(self.processed_label)
        
        self.failed_label = QLabel("Failed: 0")
        stats_layout.addWidget(self.failed_label)
        
        self.skipped_label = QLabel("Skipped: 0")
        stats_layout.addWidget(self.skipped_label)
        
        layout.addWidget(stats_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Start Processing")
        self.start_btn.clicked.connect(self._start_processing)
        self.start_btn.setMinimumHeight(40)
        control_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._pause_processing)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(40)
        control_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._stop_processing)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        control_layout.addWidget(self.stop_btn)
        
        self.retry_btn = QPushButton("🔄 Retry Failed")
        self.retry_btn.clicked.connect(self._retry_failed)
        self.retry_btn.setMinimumHeight(40)
        control_layout.addWidget(self.retry_btn)
        
        layout.addLayout(control_layout)
        
        layout.addStretch()
        
        return tab
    
    def _create_results_tab(self) -> QWidget:
        """Create Results tab for browsing analyzed files."""
        tab = QWidget()
        tab.setObjectName("resultsTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with actions
        header_layout = QHBoxLayout()
        header_label = QLabel("Analyzed Files")
        header_label.setObjectName("resultsHeader")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        self.results_refresh_button = QPushButton("🔄 Refresh")
        self.results_refresh_button.setObjectName("refreshButton")
        self.results_refresh_button.clicked.connect(self._refresh_results)
        self._style_button(self.results_refresh_button, variant="secondary")
        header_layout.addWidget(self.results_refresh_button)

        self.results_clear_button = QPushButton("🗑️ Clear All Results")
        self.results_clear_button.setObjectName("clearButton")
        self.results_clear_button.clicked.connect(self._clear_all_results)
        self._style_button(self.results_clear_button, variant="danger")
        header_layout.addWidget(self.results_clear_button)

        layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        search_label = QLabel("Search:")
        search_label.setObjectName("searchLabel")
        search_layout.addWidget(search_label)

        self.results_search_input = QLineEdit()
        self.results_search_input.setObjectName("resultsSearchInput")
        self.results_search_input.setPlaceholderText("Search descriptions and tags...")
        self.results_search_input.returnPressed.connect(self._search_results)
        self._style_line_edit(self.results_search_input)
        search_layout.addWidget(self.results_search_input)

        self.search_results_btn = QPushButton("🔍 Search")
        self.search_results_btn.setObjectName("searchButton")
        self.search_results_btn.clicked.connect(self._search_results)
        self._style_button(self.search_results_btn, variant="primary")
        search_layout.addWidget(self.search_results_btn)

        self.clear_search_btn = QPushButton("✕ Clear")
        self.clear_search_btn.setObjectName("clearSearchButton")
        self.clear_search_btn.clicked.connect(self._clear_search)
        self._style_button(self.clear_search_btn, variant="secondary")
        search_layout.addWidget(self.clear_search_btn)

        layout.addLayout(search_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setObjectName("resultsTable")
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "File Name", "Type", "Tags", "Description", "Confidence", "Analyzed"
        ])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.verticalHeader().setVisible(False)

        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.results_table.setColumnWidth(1, 80)
        self.results_table.setColumnWidth(2, 200)
        self.results_table.setColumnWidth(4, 90)
        self.results_table.setColumnWidth(5, 150)

        self.results_table.doubleClicked.connect(self._view_result_details)

        self._style_table(self.results_table, "resultsTable")
        layout.addWidget(self.results_table)
        
        # Statistics footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        footer_layout.setContentsMargins(4, 0, 4, 0)

        footer_label = QLabel("Results Count:")
        footer_label.setObjectName("countLabel")
        footer_layout.addWidget(footer_label)

        self.results_count_label = QLabel("0")
        self.results_count_label.setObjectName("countValue")
        count_font = QFont(self.font())
        count_font.setPointSize(12)
        count_font.setWeight(QFont.Weight.DemiBold)
        self.results_count_label.setFont(count_font)
        footer_layout.addWidget(self.results_count_label)

        footer_layout.addStretch()

        self.results_view_button = QPushButton("View Details")
        self.results_view_button.setObjectName("viewButton")
        self.results_view_button.clicked.connect(self._view_selected_result)
        self.results_view_button.setMinimumHeight(32)
        self._style_button(self.results_view_button, variant="secondary")
        footer_layout.addWidget(self.results_view_button)

        self.results_open_button = QPushButton("Open File")
        self.results_open_button.setObjectName("openButton")
        self.results_open_button.clicked.connect(self._open_result_file)
        self.results_open_button.setMinimumHeight(32)
        self._style_button(self.results_open_button, variant="secondary")
        footer_layout.addWidget(self.results_open_button)

        self.results_export_button = QPushButton("Export Selected")
        self.results_export_button.setObjectName("exportButton")
        self.results_export_button.clicked.connect(self._export_selected_results)
        self.results_export_button.setMinimumHeight(32)
        self._style_button(self.results_export_button, variant="primary")
        footer_layout.addWidget(self.results_export_button)

        self.results_delete_button = QPushButton("Delete Result")
        self.results_delete_button.setObjectName("deleteButton")
        self.results_delete_button.clicked.connect(self._delete_selected_result)
        self.results_delete_button.setMinimumHeight(32)
        self._style_button(self.results_delete_button, variant="danger")
        footer_layout.addWidget(self.results_delete_button)

        layout.addLayout(footer_layout)

        QTimer.singleShot(500, self._refresh_results)

        self._apply_results_theme(tab)

        return tab
    
    def _create_menu_bar(self) -> None:
        """Create application menu bar with standard layout and shortcuts."""
        menubar = self.menuBar()
        
        # ===========================
        # File menu - Core file operations
        # ===========================
        file_menu = menubar.addMenu("&File")
        
        # Watch folders section
        add_folder_action = QAction("Add Watched Folder...", self)
        add_folder_action.setShortcut("Ctrl+N")
        add_folder_action.setStatusTip("Add a new folder to monitor for documents")
        add_folder_action.triggered.connect(self._add_watch_folder)
        file_menu.addAction(add_folder_action)
        
        manage_folders_action = QAction("Manage Watch Folders...", self)
        manage_folders_action.setStatusTip("View and manage monitored folders")
        manage_folders_action.triggered.connect(self._manage_watch_folders)
        file_menu.addAction(manage_folders_action)
        
        file_menu.addSeparator()
        
        # Export/Import section
        export_submenu = file_menu.addMenu("Export")
        export_submenu.setStatusTip("Export analysis results in different formats")
        
        export_csv_action = QAction("Export to CSV...", self)
        export_csv_action.setStatusTip("Export analysis results to CSV format")
        export_csv_action.triggered.connect(lambda: self._export_results(format="csv"))
        export_submenu.addAction(export_csv_action)
        
        export_json_action = QAction("Export to JSON...", self)
        export_json_action.setStatusTip("Export analysis results to JSON format")
        export_json_action.triggered.connect(lambda: self._export_results(format="json"))
        export_submenu.addAction(export_json_action)
        
        file_menu.addSeparator()
        
        # Application control
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ===========================
        # Edit menu - Data operations
        # ===========================
        edit_menu = menubar.addMenu("&Edit")
        
        # Tag operations
        tag_submenu = edit_menu.addMenu("Tags")
        tag_submenu.setStatusTip("Manage document tags")
        
        manage_tags_action = QAction("Manage Tags...", self)
        manage_tags_action.setStatusTip("View and edit document tags")
        manage_tags_action.triggered.connect(self._manage_tags)
        tag_submenu.addAction(manage_tags_action)
        
        edit_menu.addSeparator()
        
        # Results operations
        clear_results_action = QAction("Clear All Results", self)
        clear_results_action.setStatusTip("Delete all analysis results")
        clear_results_action.triggered.connect(self._clear_all_results)
        edit_menu.addAction(clear_results_action)
        
        # ===========================
        # View menu - Display operations
        # ===========================
        view_menu = menubar.addMenu("&View")
        
        # Processed Files
        view_processed_action = QAction("📁 Processed Files...", self)
        view_processed_action.setStatusTip("View all processed files from database")
        view_processed_action.triggered.connect(self._view_processed_files)
        view_menu.addAction(view_processed_action)
        
        view_menu.addSeparator()
        
        # Refresh operations
        refresh_all_action = QAction("Refresh All Views", self)
        refresh_all_action.setShortcut("F5")
        refresh_all_action.setStatusTip("Refresh all data views")
        refresh_all_action.triggered.connect(self._refresh_all_views)
        view_menu.addAction(refresh_all_action)
        
        view_menu.addSeparator()
        
        # Tab-specific refresh
        refresh_watch_action = QAction("Refresh Watch Folders", self)
        refresh_watch_action.setStatusTip("Refresh the watch folders view")
        refresh_watch_action.triggered.connect(self._refresh_inventory)
        view_menu.addAction(refresh_watch_action)
        
        refresh_queue_action = QAction("Refresh Queue", self)
        refresh_queue_action.setStatusTip("Refresh the processing queue")
        refresh_queue_action.triggered.connect(self._refresh_queue_table)
        view_menu.addAction(refresh_queue_action)
        
        refresh_results_action = QAction("Refresh Results", self)
        refresh_results_action.setStatusTip("Refresh the analysis results")
        refresh_results_action.triggered.connect(self._refresh_results)
        view_menu.addAction(refresh_results_action)
        
        view_menu.addSeparator()
        
        # View preferences
        always_on_top_action = QAction("Always on Top", self)
        always_on_top_action.setCheckable(True)
        always_on_top_action.setStatusTip("Keep application window always on top")
        always_on_top_action.triggered.connect(self._toggle_always_on_top)
        view_menu.addAction(always_on_top_action)
        
        # ===========================
        # Processing menu - Queue processing operations
        # ===========================
        processing_menu = menubar.addMenu("&Processing")
        
        # Queue operations (moved from Edit menu)
        queue_submenu = processing_menu.addMenu("Queue Management")
        queue_submenu.setStatusTip("Manage processing queue")
        
        add_to_queue_action = QAction("Add Files to Queue...", self)
        add_to_queue_action.setShortcut("Ctrl+O")
        add_to_queue_action.setStatusTip("Add files directly to processing queue")
        add_to_queue_action.triggered.connect(self._add_files_to_queue)
        queue_submenu.addAction(add_to_queue_action)
        
        clear_queue_action = QAction("Clear Processing Queue", self)
        clear_queue_action.setStatusTip("Remove all items from the processing queue")
        clear_queue_action.triggered.connect(self._clear_queue)
        queue_submenu.addAction(clear_queue_action)
        
        processing_menu.addSeparator()
        
        # Main controls with icons
        start_processing_action = QAction("▶ Start Processing", self)
        start_processing_action.setShortcut("F9")
        start_processing_action.setStatusTip("Start processing the queue")
        start_processing_action.triggered.connect(self._start_processing)
        processing_menu.addAction(start_processing_action)
        
        pause_processing_action = QAction("⏸ Pause Processing", self)
        pause_processing_action.setShortcut("F10")
        pause_processing_action.setStatusTip("Pause the current processing")
        pause_processing_action.triggered.connect(self._pause_processing)
        processing_menu.addAction(pause_processing_action)
        
        stop_processing_action = QAction("⏹ Stop Processing", self)
        stop_processing_action.setShortcut("F11")
        stop_processing_action.setStatusTip("Stop all processing")
        stop_processing_action.triggered.connect(self._stop_processing)
        processing_menu.addAction(stop_processing_action)
        
        processing_menu.addSeparator()
        
        # Additional processing options
        retry_failed_action = QAction("Retry Failed Items", self)
        retry_failed_action.setStatusTip("Retry processing of failed items")
        retry_failed_action.triggered.connect(self.retry_failed_signal.emit)
        processing_menu.addAction(retry_failed_action)
        
        processing_menu.addSeparator()
        
        # Advanced options
        processing_options_action = QAction("Processing Options...", self)
        processing_options_action.setStatusTip("Configure processing options")
        processing_options_action.triggered.connect(self._show_processing_options)
        processing_menu.addAction(processing_options_action)
        
        # ===========================
        # Tools menu - Utilities and settings
        # ===========================
        tools_menu = menubar.addMenu("&Tools")
        
        # AI Model management
        ai_models_action = QAction("AI Model Manager...", self)
        ai_models_action.setShortcut("Ctrl+M")
        ai_models_action.setStatusTip("View and manage AI models")
        ai_models_action.triggered.connect(self._show_ai_models)
        tools_menu.addAction(ai_models_action)
        
        tools_menu.addSeparator()
        
        # Database utilities
        database_submenu = tools_menu.addMenu("Database")
        database_submenu.setStatusTip("Database management tools")
        
        db_maintenance_action = QAction("Database Maintenance...", self)
        db_maintenance_action.setStatusTip("Perform database maintenance tasks")
        db_maintenance_action.triggered.connect(self._show_db_maintenance)
        database_submenu.addAction(db_maintenance_action)
        
        tools_menu.addSeparator()
        
        # System utilities
        diagnostics_action = QAction("System Diagnostics...", self)
        diagnostics_action.setShortcut("Ctrl+D")
        diagnostics_action.setStatusTip("Run system diagnostics")
        diagnostics_action.triggered.connect(self._show_diagnostics)
        tools_menu.addAction(diagnostics_action)
        
        tools_menu.addSeparator()
        
        # Configuration
        settings_action = QAction("Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)
        
        # ===========================
        # Help menu - Documentation and support
        # ===========================
        help_menu = menubar.addMenu("&Help")
        
        # Documentation
        help_center_action = QAction("Help Center", self)
        help_center_action.setShortcut("F1")
        help_center_action.setStatusTip("Access the comprehensive help center")
        help_center_action.triggered.connect(self._show_help_center)
        help_menu.addAction(help_center_action)
        
        quickstart_action = QAction("Quick Start Guide", self)
        quickstart_action.setStatusTip("View getting started tutorial")
        quickstart_action.triggered.connect(self._show_quickstart)
        help_menu.addAction(quickstart_action)
        
        help_menu.addSeparator()
        
        # Support & Updates
        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.setStatusTip("Check for software updates")
        check_updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(check_updates_action)
        
        help_menu.addSeparator()
        
        # About
        about_action = QAction("About Previewless Insight Viewer", self)
        about_action.setStatusTip("Show application information")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self) -> None:
        """Create application status bar."""
        status_bar = QStatusBar()
        colors = self.APP_PALETTE
        status_bar.setStyleSheet(
            f"""
            QStatusBar {{
                background-color: {colors['surface']};
                color: {colors['text_secondary']};
                border-top: 1px solid {colors['dividers']};
            }}
            QLabel#statusSeparator {{
                color: {colors['dividers']};
                padding: 0 6px;
            }}
            QLabel#statusPrimary {{
                color: {colors['text_primary']};
            }}
            """
        )
        self.setStatusBar(status_bar)
        
        # Add notification area (left-most, stretches to fill available space)
        self.notification_area = QWidget()
        self.notification_area.setObjectName("statusNotification")
        notification_layout = QHBoxLayout(self.notification_area)
        notification_layout.setContentsMargins(2, 0, 2, 0)
        notification_layout.setSpacing(4)
        
        self.status_notification_icon = QLabel("")
        self.status_notification_icon.setFixedWidth(16)
        notification_layout.addWidget(self.status_notification_icon)
        
        self.status_notification_message = QLabel("")
        self.status_notification_message.setStyleSheet("padding: 0 4px;")
        notification_layout.addWidget(self.status_notification_message)
        notification_layout.addStretch()
        
        # Add close button for notifications
        self.status_notification_close = QPushButton("✕")
        self.status_notification_close.setFixedSize(16, 16)
        self.status_notification_close.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 10px;
                padding: 0px;
                color: {colors['text_secondary']};
            }}
            QPushButton:hover {{
                background-color: {colors['hover']};
                border-radius: 8px;
                color: {colors['text_primary']};
            }}
            """
        )
        self.status_notification_close.clicked.connect(self._hide_notification)
        self.status_notification_close.setVisible(False)  # Hide until needed
        notification_layout.addWidget(self.status_notification_close)
        
        status_bar.addWidget(self.notification_area, 1)  # Stretch to fill available space
        
        # Add permanent widgets (right side)
        separator_one = QLabel("●")
        separator_one.setObjectName("statusSeparator")
        status_bar.addPermanentWidget(separator_one)
        
        # AI Model status button
        self.ai_status_btn = QPushButton("● AI Models")
        self.ai_status_btn.setFlat(True)
        self._style_button(self.ai_status_btn, variant="ghost")
        self.ai_status_btn.clicked.connect(self._show_ai_model_dialog)
        status_bar.addPermanentWidget(self.ai_status_btn)
        
        self.inventory_status_label = QLabel("Files: 0")
        self.inventory_status_label.setObjectName("statusPrimary")
        self.inventory_status_label.setStyleSheet("padding: 0 8px;")
        status_bar.addPermanentWidget(self.inventory_status_label)
        
        separator_two = QLabel("●")
        separator_two.setObjectName("statusSeparator")
        status_bar.addPermanentWidget(separator_two)
        
        self.processing_status_bar_label = QLabel("Idle")
        self.processing_status_bar_label.setObjectName("statusPrimary")
        self.processing_status_bar_label.setStyleSheet("padding: 0 8px;")
        status_bar.addPermanentWidget(self.processing_status_bar_label)
    
    def _connect_signals(self):
        """Connect service signals to UI handlers."""
        # File watcher signals
        self.file_watcher.inventory_updated.connect(self._on_inventory_updated)
        self.file_watcher.error_occurred.connect(self._on_watcher_error)
        
        # AI status signal (thread-safe)
        self.ai_status_changed.connect(self._update_ai_status)
        
        # Queue manager signals
        self.queue_manager.item_added.connect(self._on_queue_item_added)
        self.queue_manager.item_removed.connect(self._on_queue_item_removed)
        self.queue_manager.item_updated.connect(self._on_queue_item_updated)
        self.queue_manager.queue_cleared.connect(self._refresh_queue_table)
        self.queue_manager.progress_changed.connect(self._on_queue_progress)
        
        # Orchestrator signals (if available)
        if self.orchestrator:
            # Connect control signals TO orchestrator methods
            self.start_processing_signal.connect(self.orchestrator.start_processing)
            self.pause_processing_signal.connect(self.orchestrator.pause_processing)
            self.resume_processing_signal.connect(self.orchestrator.resume_processing)
            self.stop_processing_signal.connect(self.orchestrator.stop_processing)
            self.retry_failed_signal.connect(self.orchestrator.retry_failed_items)
            
            # Connect orchestrator signals FROM orchestrator to UI
            self.orchestrator.processing_started.connect(self._on_processing_started)
            self.orchestrator.processing_paused.connect(self._on_processing_paused)
            self.orchestrator.processing_stopped.connect(self._on_processing_stopped)
            self.orchestrator.processing_completed.connect(self._on_processing_completed)
            self.orchestrator.item_processing_started.connect(self._on_item_processing_started)
            self.orchestrator.item_processing_completed.connect(self._on_item_processing_completed)
            self.orchestrator.item_processing_failed.connect(self._on_item_processing_failed)
            self.orchestrator.item_progress_updated.connect(self._on_item_progress_updated)
            self.orchestrator.review_required.connect(self._on_review_required)
            self.orchestrator.progress_updated.connect(self._on_processing_progress)
            self.orchestrator.state_changed.connect(self._on_processing_state_changed)
            
            # Connect new processing controls to orchestrator state changes
            if self.processing_controls_integration:
                self.orchestrator.state_changed.connect(
                    self.processing_controls_integration.handle_state_change,
                    Qt.QueuedConnection  # Ensure thread-safe execution
                )
                # Sync initial state
                self.processing_controls_integration.sync_state_with_orchestrator()
        
        # UI signals
        self.folder_list.itemSelectionChanged.connect(self._on_folder_selection_changed)
        self.queue_table.itemSelectionChanged.connect(self._on_queue_selection_changed)
        
        logger.info("Signals connected")
    
    def _show_settings(self):
        """Show settings dialog."""
        from src.ui.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()
    
    def _show_diagnostics(self):
        """Show diagnostics dialog."""
        from src.services.diagnostics import run_diagnostics
        
        # Run diagnostics
        logger.info("Running system diagnostics...")
        diag_service = run_diagnostics(self.config)
        
        # Get results
        summary = diag_service.get_status_summary()
        status = diag_service.results.get('overall_status', 'unknown')
        
        # Log detailed results
        logger.info(f"Diagnostics completed: {status}")
        logger.debug(f"Diagnostics details:\n{summary}")
        
        # Show inline notification with status
        if status == 'healthy':
            self._show_notification("✓ All systems operational", "success", auto_hide=4000)
        elif status == 'degraded':
            self._show_notification("⚠ Some systems need attention - check logs for details", "warning", auto_hide=6000)
    
    def _show_ai_model_dialog(self):
        """Show AI Model Manager dialog."""
        if not self.llm_adapter:
            self._show_notification("LLM adapter not available", "error")
            return
        
        dialog = AIModelDialog(self.llm_adapter, self)
        dialog.status_changed.connect(self._update_ai_status)
        dialog.exec()
    
    def _animate_processing_activity(self):
        """Animate activity indicator during processing to show it's working."""
        # Check if the orchestrator exists and if we're not in RUNNING state
        if not self.orchestrator:
            return
            
        # Handle different states
        if self.orchestrator.state == ProcessingState.PAUSED:
            # If paused, show "PAUSED" (without animation spinner)
            self._set_processing_status("⚙️ PAUSED", "warning")
            self.processing_status_bar_label.setText("Paused")
            
            # Stop the animation timer to prevent further updates
            if hasattr(self, '_activity_timer') and self._activity_timer.isActive():
                self._activity_timer.stop()
            return
        elif self.orchestrator.state == ProcessingState.STOPPED:
            # If stopped, show "STOPPED" (without animation spinner)
            self._set_processing_status("⚙️ STOPPED", "error")
            self.processing_status_bar_label.setText("Stopped")
            
            # Stop the animation timer to prevent further updates
            if hasattr(self, '_activity_timer') and self._activity_timer.isActive():
                self._activity_timer.stop()
            return
        elif self.orchestrator.state == ProcessingState.IDLE:
            # If idle, show "IDLE" (without animation spinner)
            self._set_processing_status("⚙️ IDLE")
            self.processing_status_bar_label.setText("Idle")
            
            # Stop the animation timer to prevent further updates
            if hasattr(self, '_activity_timer') and self._activity_timer.isActive():
                self._activity_timer.stop()
            return
            
        # Only proceed with animation for RUNNING, PAUSING, or STOPPING states
        # Cycle through animation frames (Braille spinner)
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._activity_frame = (self._activity_frame + 1) % len(frames)
        spinner = frames[self._activity_frame]
        
        # Update status with spinner based on current state
        current_state = self.orchestrator.state
        if current_state == ProcessingState.PAUSING:
            self._set_processing_status(f"{spinner} PAUSING...", "warning")
        elif current_state == ProcessingState.STOPPING:
            self._set_processing_status(f"{spinner} STOPPING...", "error")
        else:  # RUNNING state
            self._set_processing_status(f"{spinner} RUNNING", "info")
    
    def _check_ai_status(self):
        """Check AI model status in background thread to avoid blocking UI."""
        if not self.llm_adapter:
            self._update_ai_status(False)
            return
        
        # Run AI status check in background thread to avoid blocking UI
        def check_ai():
            try:
                is_ok = self.llm_adapter.verify_connection()
                # Emit signal to update UI on main thread (thread-safe)
                self.ai_status_changed.emit(is_ok)
            except Exception as e:
                logger.error(f"Error checking AI status: {e}")
                self.ai_status_changed.emit(False)
        
        # Start check in background thread
        import threading
        thread = threading.Thread(target=check_ai, daemon=True)
        thread.start()
    
    def _update_ai_status(self, status_ok: bool):
        """
        Update AI status indicator.
        
        Args:
            status_ok: True if AI models are working correctly
        """
        self._ai_status_ok = status_ok
        
        colors = self.APP_PALETTE
        if status_ok:
            self.ai_status_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    padding: 4px 12px;
                    color: {colors['alert_success']};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {colors['hover']};
                    border-radius: 6px;
                }}
                """
            )
            self.ai_status_btn.setToolTip("AI Models: Connected ✓\nClick to manage models")
        else:
            self.ai_status_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    padding: 4px 12px;
                    color: {colors['alert_error']};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {colors['hover']};
                    border-radius: 6px;
                }}
                """
            )
            self.ai_status_btn.setToolTip("AI Models: Not Connected ✕\nClick to troubleshoot")
    
    def _on_settings_changed(self):
        """Handle settings changes."""
        logger.info("Settings changed, applying updates...")
        
        # Reload theme if changed
        theme_name = self.config.get("ui.theme", "dark")
        theme_path = self.portable_root / "config" / "themes" / f"{theme_name}.qss"
        
        if theme_path.exists():
            with open(theme_path, "r", encoding="utf-8") as f:
                self.styleSheet = f.read()
                from PySide6.QtWidgets import QApplication
                QApplication.instance().setStyleSheet(self.styleSheet)
            logger.info(f"Reloaded theme: {theme_name}")
    
    # Watch tab handlers
    def _load_watched_folders(self):
        """Load watched folders into list."""
        self.folder_list.clear()
        watched = self.config.get('watched_folders', [])
        for folder in watched:
            self.folder_list.addItem(folder)
    
    def _add_watch_folder(self):
        """Add a new watched folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Watch",
            str(Path.home())
        )
        
        if folder:
            # Add the watch folder
            self.file_watcher.add_watch_path(folder)
            self._load_watched_folders()
            logger.info(f"Added watch folder: {folder}")
            
            # Show information message about supported file types
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Folder Added")
            msg_box.setText(f"The folder '{Path(folder).name}' has been added to the watch list.")
            msg_box.setInformativeText("Only supported file types will be processed. Would you like to see the list of supported file types?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            
            if msg_box.exec() == QMessageBox.Yes:
                self._show_supported_file_types_info()
    
    def _remove_watch_folder(self):
        """Remove selected watched folder."""
        selected = self.folder_list.currentItem()
        if selected:
            folder = selected.text()
            self.file_watcher.remove_watch_path(folder)
            self._load_watched_folders()
            logger.info(f"Removed watch folder: {folder}")
    
    def _refresh_inventory(self):
        """Refresh file inventory."""
        self.file_watcher.stop_watching()
        self.file_watcher.start_watching()
        logger.info("Inventory refreshed")
    
    def _on_folder_selection_changed(self):
        """Handle folder selection change."""
        has_selection = bool(self.folder_list.currentItem())
        self.remove_folder_btn.setEnabled(has_selection)
    
    def _on_inventory_updated(self, inventory):
        """Handle inventory update signal."""
        self.total_files_label.setText(f"Total Files: {inventory.total_files}")
        
        # Format by-type breakdown
        type_str = ", ".join(f"{k}: {v}" for k, v in inventory.by_type.items())
        self.by_type_label.setText(f"By Type: {type_str or '-'}")
        
        self.unanalyzed_label.setText(f"Unanalyzed: {inventory.unanalyzed_count}")
        
        # Update status bar
        self.inventory_status_label.setText(f"Files: {inventory.total_files}")
        
        # Auto-enqueue unanalyzed files
        self._auto_enqueue_unanalyzed()
        
        logger.debug(f"Inventory updated: {inventory.total_files} files")
    
    def _auto_enqueue_unanalyzed(self):
        """Automatically enqueue unanalyzed files from watched folders."""
        try:
            # Get all files from watched folders
            unanalyzed_files = []
            
            for file_path in self.file_watcher.known_files:
                path = Path(file_path)
                if not path.exists():
                    continue
                
                # Check if file is already in queue
                queue_items = self.queue_manager.get_queue_items()
                if any(item.file_path == str(path) for item in queue_items):
                    continue
                
                # Check if file is already analyzed
                file_hash = self.queue_manager._calculate_file_hash(path)
                with self.db.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT 1 FROM files f
                        WHERE f.file_hash = ?
                        AND (
                            EXISTS (SELECT 1 FROM descriptions d WHERE d.file_id = f.file_id)
                            OR EXISTS (SELECT 1 FROM classifications c WHERE c.file_id = f.file_id)
                        )
                        LIMIT 1
                    """, (file_hash,))
                    
                    if cursor.fetchone():
                        continue  # Already analyzed
                
                unanalyzed_files.append(str(path))
            
            # Add unanalyzed files to queue
            for file_path in unanalyzed_files:
                self.queue_manager.add_item(file_path)
                logger.debug(f"Auto-enqueued: {Path(file_path).name}")
            
            if unanalyzed_files:
                logger.info(f"Auto-enqueued {len(unanalyzed_files)} unanalyzed files")
                self._refresh_queue_table()
                self._update_queue_badge()
        
        except Exception as e:
            logger.error(f"Error auto-enqueueing files: {e}")
    
    def _update_queue_badge(self):
        """Update queue tab with glowing green dot indicator when files are ready."""
        queue_count = len(self.queue_manager.get_queue_items())
        
        if queue_count > 0:
            # Show glowing green dot when files are ready
            self.tabs.setTabText(1, "📋 Queue 🟢")
            # Start glow animation if not already running
            if not self._glow_timer.isActive():
                self._glow_timer.start(50)  # Update every 50ms for smooth animation
        else:
            # No indicator if empty
            self.tabs.setTabText(1, "📋 Queue")
            # Stop glow animation
            if self._glow_timer.isActive():
                self._glow_timer.stop()
            # Reset stylesheet
            if self._base_tab_bar_style:
                self.tabs.tabBar().setStyleSheet(self._base_tab_bar_style)
    
    def _animate_queue_glow(self):
        """Animate the glowing effect on the queue tab."""
        # Update intensity (0-100)
        self._glow_intensity += self._glow_direction * 5
        
        if self._glow_intensity >= 100:
            self._glow_intensity = 100
            self._glow_direction = -1
        elif self._glow_intensity <= 30:  # Don't go too dim
            self._glow_intensity = 30
            self._glow_direction = 1
        
        accent_hex = self.APP_PALETTE['focus'].lstrip('#')
        accent_r = int(accent_hex[0:2], 16)
        accent_g = int(accent_hex[2:4], 16)
        accent_b = int(accent_hex[4:6], 16)
        alpha = 0.35 + (0.45 * self._glow_intensity / 100)
        glow_color = f"rgba({accent_r}, {accent_g}, {accent_b}, {alpha:.2f})"

        glow_style = (
            f"""
            QTabBar::tab:nth-child(2) {{
                color: {glow_color};
                font-weight: 600;
            }}
            """
        )

        self.tabs.tabBar().setStyleSheet(self._base_tab_bar_style + glow_style)

    
    def _on_watcher_error(self, error_code, message):
        """Handle file watcher error."""
        logger.error(f"File watcher error: {error_code} - {message}")
        self.status_label.setText(f"Error: {message}")
    
    # Queue tab handlers
    def _refresh_queue_table(self):
        """Refresh queue table display."""
        items = self.queue_manager.get_queue_items()

        previously_selected = set()
        selection_model = self.queue_table.selectionModel()
        if selection_model:
            for index in selection_model.selectedRows():
                if 0 <= index.row() < len(items):
                    previously_selected.add(items[index.row()].file_path)

        self.queue_table.setRowCount(0)
        self._file_progress_bars.clear()

        for item in items:
            row = self.queue_table.rowCount()
            self.queue_table.insertRow(row)

            file_item = self._create_queue_table_item(Path(item.file_path).name)
            file_item.setToolTip(item.file_path)
            file_item.setData(Qt.UserRole, item.file_path)
            self.queue_table.setItem(row, 0, file_item)

            type_item = self._create_queue_table_item(item.file_type or "-", secondary=True)
            self.queue_table.setItem(row, 1, type_item)

            # Special handling for status column - show PROCESSING as PENDING when paused
            if item.status == QueueItemStatus.PROCESSING and hasattr(self, 'orchestrator') and self.orchestrator and \
               (self.orchestrator.state == ProcessingState.PAUSED or self.orchestrator.state == ProcessingState.PAUSING):
                status_label = QueueItemStatus.PENDING.value.replace("_", " ").title()
                status_secondary = True
            else:
                status_label = item.status.value.replace("_", " ").title()
                status_secondary = item.status in (QueueItemStatus.PENDING, QueueItemStatus.SKIPPED)
            
            status_item = self._create_queue_table_item(status_label, secondary=status_secondary)
            self.queue_table.setItem(row, 2, status_item)

            progress_bar = self._create_queue_progress_widget(item)
            self.queue_table.setCellWidget(row, 3, progress_bar)
            self._file_progress_bars[item.file_path] = progress_bar

            priority_item = self._create_queue_table_item(self._format_priority_text(item.priority))
            priority_item.setToolTip(self._priority_detail_text(item.priority))
            self.queue_table.setItem(row, 4, priority_item)

            row_brush = QBrush(QColor(self._row_color_for_priority(item.priority)))
            for col_index in (0, 1, 2, 4):
                cell = self.queue_table.item(row, col_index)
                if cell:
                    cell.setBackground(row_brush)

            if item.file_path in previously_selected:
                self.queue_table.selectRow(row)

        self.queue_table.resizeRowsToContents()
        self._on_queue_selection_changed()
        logger.debug(f"Queue table refreshed: {len(items)} items")
    
    def _show_supported_file_types_info(self):
        """Show a dialog with information about supported file types."""
        file_types = self.queue_manager.get_supported_file_types()
        
        # Create message with supported extensions by category
        message = "The following file types are supported for analysis:\n\n"
        
        for category, extensions in file_types.items():
            # Convert extensions to friendly format (without leading dot)
            friendly_exts = [ext[1:].upper() for ext in extensions]
            
            # Format by category
            if category == 'pdf':
                message += f"📄 <b>PDF Documents:</b> {', '.join(friendly_exts)}\n\n"
            elif category == 'image':
                message += f"🖼️ <b>Images:</b> {', '.join(friendly_exts)}\n\n"
            elif category == 'text':
                message += f"📝 <b>Text Files:</b> {', '.join(friendly_exts)}\n\n"
            elif category == 'office':
                message += f"📊 <b>Office Documents:</b> {', '.join(friendly_exts)}\n\n"
            else:
                message += f"<b>{category.title()}:</b> {', '.join(friendly_exts)}\n\n"
        
        # Create message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Supported File Types")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.addButton(QMessageBox.Ok)
        msg_box.addButton("Help", QMessageBox.HelpRole)
        
        # Add help button with more detailed info
        if msg_box.exec() == QMessageBox.HelpRole:
            self._show_help("file_types")
    
    def _enqueue_files(self):
        """Enqueue files for processing."""
        # Get supported file extensions from QueueManager
        file_types = self.queue_manager.get_supported_file_types()
        
        # Build the filter string for QFileDialog
        filter_parts = []
        
        # Add "All Supported Files" filter with all extensions
        all_extensions = []
        for extensions in file_types.values():
            all_extensions.extend([ext[1:] for ext in extensions])  # Remove the leading dot
        
        all_filter = f"All Supported Files (*.{' *.'.join(all_extensions)})"
        filter_parts.append(all_filter)
        
        # Add specific type filters
        filter_parts.append(f"PDF Files (*.pdf)")
        filter_parts.append(f"Image Files (*.{' *.'.join([ext[1:] for ext in file_types['image']])})")
        filter_parts.append(f"Text Files (*.{' *.'.join([ext[1:] for ext in file_types['text']])})")
        filter_parts.append(f"Office Documents (*.{' *.'.join([ext[1:] for ext in file_types['office']])})")
        filter_parts.append("All Files (*.*)")
        
        # Join filters with double semicolons
        filter_string = ";;".join(filter_parts)
        
        # Show file dialog with filters
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Process",
            str(Path.home()),
            filter_string
        )
        
        if files:
            priority_value = self._prompt_priority_for_new_items(len(files))
            if priority_value is None:
                self.show_status_message("Enqueue cancelled", "warning")
                return

            count = self.queue_manager.add_batch(files, priority_value)
            if count < len(files):
                skipped = len(files) - count
                self.show_status_message(f"Enqueued {count} files, skipped {skipped} unsupported files")

                if skipped > 0:
                    QTimer.singleShot(500, self._show_supported_file_types_info)
            else:
                self.show_status_message(
                    f"Enqueued {count} files at {self._format_priority_text(priority_value)}"
                )

            logger.info(f"Enqueued {count}/{len(files)} files with priority {priority_value}")
            self.priority_combo.setCurrentIndex(self._priority_index_for_value(priority_value))
            self._refresh_queue_table()
            self._update_queue_badge()
    
    def _dequeue_files(self):
        """Remove selected files from queue."""
        selection_model = self.queue_table.selectionModel()
        if not selection_model:
            return

        selected_rows = sorted((index.row() for index in selection_model.selectedRows()), reverse=True)
        if not selected_rows:
            return

        items = self.queue_manager.get_queue_items()
        removed = 0
        for row in selected_rows:
            if 0 <= row < len(items):
                if self.queue_manager.remove_item(items[row].file_path):
                    removed += 1

        if removed:
            self.show_status_message(f"Removed {removed} item(s) from the queue")
        
        self._refresh_queue_table()
        self._update_queue_badge()
    
    def _move_queue_up(self):
        """Move selected queue item up."""
        selection_model = self.queue_table.selectionModel()
        if not selection_model:
            return

        selected_rows = sorted(index.row() for index in selection_model.selectedRows())
        if not selected_rows:
            return

        current_row = selected_rows[0]
        if current_row <= 0:
            return

        items = self.queue_manager.get_queue_items()
        if current_row < len(items) and self.queue_manager.move_up(items[current_row].file_path):
            self._refresh_queue_table()
            self.queue_table.selectRow(current_row - 1)
            self._on_queue_selection_changed()
    
    def _move_queue_down(self):
        """Move selected queue item down."""
        selection_model = self.queue_table.selectionModel()
        if not selection_model:
            return

        selected_rows = sorted(index.row() for index in selection_model.selectedRows())
        if not selected_rows:
            return

        current_row = selected_rows[-1]
        items = self.queue_manager.get_queue_items()
        if current_row < 0 or current_row >= len(items) - 1:
            return

        if self.queue_manager.move_down(items[current_row].file_path):
            self._refresh_queue_table()
            self.queue_table.selectRow(current_row + 1)
            self._on_queue_selection_changed()

    def _set_selected_priority(self):
        """Apply the chosen priority to all selected queue items."""
        if not self.priority_combo:
            return

        selection_model = self.queue_table.selectionModel()
        if not selection_model or not selection_model.hasSelection():
            return

        selected_rows = sorted(index.row() for index in selection_model.selectedRows())
        items = self.queue_manager.get_queue_items()
        selected_paths = [items[row].file_path for row in selected_rows if 0 <= row < len(items)]

        if not selected_paths:
            return

        priority_value = self.priority_combo.currentData()
        if priority_value is None:
            return

        updated = self.queue_manager.set_batch_priority(selected_paths, priority_value)
        if updated:
            display_text = self._format_priority_text(priority_value)
            self.show_status_message(f"Updated {updated} item(s) to {display_text}")
            self.priority_combo.setCurrentIndex(self._priority_index_for_value(priority_value))
            self._refresh_queue_table()
            self._update_queue_badge()

    def _prompt_priority_for_new_items(self, count: int) -> Optional[int]:
        """Prompt the user for a priority selection before enqueueing."""
        dialog = PrioritySelectionDialog(
            self.QUEUE_PALETTE,
            self.QUEUE_PRIORITY_LEVELS,
            DEFAULT_QUEUE_PRIORITY,
            self
        )
        plural = "s" if count != 1 else ""
        dialog.set_message(f"Assign a priority for the {count} file{plural} you are adding.")
        if dialog.exec() == QDialog.Accepted:
            return dialog.selected_priority()
        return None
    
    def _clear_queue(self):
        """Clear the processing queue."""
        # Clear queue directly without confirmation dialog
        self.queue_manager.clear_queue()
        self._refresh_queue_table()
        self._update_queue_badge()
        logger.info("Queue cleared")
        
        # Show inline notification
        self._show_notification("Queue cleared successfully", "info", auto_hide=3000)
    
    def _on_queue_selection_changed(self):
        """Handle queue selection change."""
        selection_model = self.queue_table.selectionModel()
        has_selection = bool(selection_model and selection_model.hasSelection())
        current_row = self.queue_table.currentRow()
        row_count = self.queue_table.rowCount()

        self.dequeue_btn.setEnabled(has_selection)
        if self.priority_apply_btn:
            self.priority_apply_btn.setEnabled(has_selection)

        can_move_up = has_selection and current_row > 0
        can_move_down = has_selection and 0 <= current_row < row_count - 1
        self.move_up_btn.setEnabled(can_move_up)
        self.move_down_btn.setEnabled(can_move_down)
    
    def _on_queue_item_added(self, item):
        """Handle queue item added signal."""
        self._refresh_queue_table()
        self._update_queue_badge()
    
    def _on_queue_item_removed(self, file_path):
        """Handle queue item removed signal."""
        self._refresh_queue_table()
        self._update_queue_badge()
    
    def _on_queue_item_updated(self, item):
        """Handle queue item updated signal."""
        self._refresh_queue_table()
        self._update_queue_badge()
    
    def _on_queue_progress(self, completed, total):
        """Handle queue progress signal."""
        self.queue_progress.setMaximum(total)
        # Ensure completed is at least 1
        adjusted_completed = max(1, completed)
        self.queue_progress.setValue(adjusted_completed)
    
    # Processing tab handlers
    def _start_processing(self):
        """Start processing the queue."""
        if not self.orchestrator:
            self._show_notification(
                "Processing not available. Please check OCR and LLM configuration in Settings.",
                "warning",
                auto_hide=6000
            )
            return
        
        # Check if we're resuming from paused state
        # For new controls, check orchestrator state; for old controls, check button text
        should_resume = False
        if self._using_new_controls:
            # With new controls, check the orchestrator state
            should_resume = (hasattr(self.orchestrator, 'state') and 
                           self.orchestrator.state == ProcessingState.PAUSED)
        elif hasattr(self, 'proc_start_btn') and self.proc_start_btn:
            # With old controls, check button text
            should_resume = self.proc_start_btn.text() == "▶ Resume"
        
        if should_resume:
            self._resume_processing()
        else:
            # Emit signal to trigger start_processing on worker thread
            logger.info("Emitting start_processing_signal...")
            self.start_processing_signal.emit()
    
    def _resume_processing(self):
        """Resume processing from paused state."""
        if not self.orchestrator:
            logger.warning("Cannot resume: orchestrator not available")
            return
            
        if not self._validate_state_transition(self.orchestrator.state, ProcessingState.RUNNING, "resume"):
            return
        
        # Emit signal to trigger resume_processing on worker thread
        logger.info("Emitting resume_processing_signal...")
        self.resume_processing_signal.emit()
    
    def _validate_state_transition(self, current_state, target_state, action):
        """Validate if a state transition is allowed."""
        logger.info(f"Validating state transition: {current_state} -> {target_state} for action '{action}'")
        
        valid_transitions = {
            ProcessingState.IDLE: [ProcessingState.RUNNING],
            ProcessingState.RUNNING: [ProcessingState.PAUSING, ProcessingState.STOPPING],
            ProcessingState.PAUSING: [ProcessingState.PAUSED],
            ProcessingState.PAUSED: [ProcessingState.RUNNING, ProcessingState.STOPPING],
            ProcessingState.STOPPING: [ProcessingState.STOPPED],
            ProcessingState.STOPPED: [ProcessingState.IDLE, ProcessingState.RUNNING],
        }
        
        allowed_targets = valid_transitions.get(current_state, [])
        logger.info(f"Allowed transitions from {current_state}: {allowed_targets}")
        
        if target_state not in allowed_targets:
            logger.error(f"Invalid state transition for {action}: {current_state} -> {target_state}")
            self._show_notification(
                f"Cannot {action}: invalid state transition from {current_state.value}",
                "error",
                auto_hide=3000
            )
            return False
        
        logger.info(f"State transition validation passed for {action}")
        return True
    
    def _pause_processing(self):
        """Toggle between pause and resume processing."""
        try:
            logger.info(f"_pause_processing called")
            # Only log button state if using old controls
            if not self._using_new_controls and hasattr(self, 'proc_pause_btn') and self.proc_pause_btn:
                logger.info(f"Pause button enabled: {self.proc_pause_btn.isEnabled()}")
            
            if not hasattr(self, 'orchestrator') or self.orchestrator is None:
                logger.error("Orchestrator not available")
                self._show_notification("Processing orchestrator not available", "error", auto_hide=3000)
                return
            
            logger.info(f"Current orchestrator state: {self.orchestrator.state}")
            
            # Check current state to determine if we need to pause or resume
            if self.orchestrator.state == ProcessingState.RUNNING:
                logger.info("State is RUNNING, attempting to pause...")
                # Validate pause transition
                if not self._validate_state_transition(self.orchestrator.state, ProcessingState.PAUSING, "pause"):
                    logger.warning("State transition validation failed for pause")
                    return
                # Pause processing - let state machine handle UI updates
                logger.info("Processing pause requested - emitting pause_processing_signal")
                try:
                    self.pause_processing_signal.emit()
                    logger.info("pause_processing_signal emitted successfully")
                except Exception as e:
                    logger.error(f"Failed to emit pause_processing_signal: {e}")
                    
            elif self.orchestrator.state == ProcessingState.PAUSED:
                # Resume processing using the dedicated method
                logger.info("Processing resume requested via pause button")
                self._resume_processing()
            else:
                logger.warning(f"Cannot pause/resume from state: {self.orchestrator.state}")
                self._show_notification(f"Cannot pause from state: {self.orchestrator.state.value}", "warning", auto_hide=3000)
                
        except Exception as e:
            logger.error(f"Error in _pause_processing: {e}")
            self._show_notification(f"Error in pause processing: {str(e)}", "error", auto_hide=5000)
    
    def _stop_processing(self):
        """Stop processing."""
        if not self.orchestrator:
            logger.warning("Cannot stop: orchestrator not available")
            return
            
        # Validate stop transition
        if not self._validate_state_transition(self.orchestrator.state, ProcessingState.STOPPING, "stop"):
            return
            
        # Update UI immediately to show stop is pending with spinner
        self._set_processing_status("⠋ STOPPING...", "error")
        self.processing_status_bar_label.setText("Stopping...")
        
        # Update buttons safely
        self._update_control_buttons_safe(
            start_enabled=False,
            pause_enabled=False,
            stop_enabled=False,
            retry_enabled=False  # Disable retry during stopping
        )
        
        # Emit signal to trigger stop_processing on worker thread
        self.stop_processing_signal.emit()
        logger.info("Processing stop requested")
    
    def _retry_failed(self):
        """Retry failed items."""
        if self.orchestrator:
            # Emit signal to trigger retry_failed_items on worker thread
            self.retry_failed_signal.emit()
            logger.info("Retrying failed items")
    
    def _on_processing_started(self):
        """Handle processing started signal."""
        from datetime import datetime
        
        # Record start time for speed calculations
        self._processing_start_time = datetime.now()
        
        # Reset pause tracking variables
        self._pause_time = None
        self._paused_elapsed_seconds = 0
        
        # This is now just a backup handler - state change should handle it
        logger.debug("_on_processing_started called - delegating to state handler")
        if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'state'):
            # Import the correct ProcessingState from orchestrator
            try:
                from src.services.processing_orchestrator import ProcessingState as OrchestratorState
                expected_state = OrchestratorState.RUNNING
            except ImportError:
                # Fallback - try to compare by string representation
                expected_state = "RUNNING"
                
            # Just double-check that we're actually in RUNNING state
            if self.orchestrator.state != expected_state:
                # Check by string representation as fallback
                state_str = str(self.orchestrator.state).split('.')[-1]  # Get enum name
                if state_str != "RUNNING":
                    logger.warning(f"Expected RUNNING state but got {self.orchestrator.state}, fixing...")
                    # Force state to RUNNING
                    self.orchestrator.state = expected_state
                
            self._on_processing_state_changed(ProcessingState.RUNNING)
        else:
            logger.warning("Orchestrator not available for state check")
        
        # Reset performance tracking
        self._processing_start_time = datetime.now()
        self._last_progress_time = datetime.now()
        self._files_processed_in_batch = 0
        self._processing_speed = 0.0
        self.proc_speed_label.setText("⚡ Speed: initializing...")
        self.proc_eta_label.setText("⏱️ ETA: calculating...")
        
        # Start activity animation
        self._activity_frame = 0
        self._activity_timer.start(500)  # Update every 500ms
        
        logger.info("UI updated: processing started")
    
    def _on_processing_paused(self):
        """Handle processing paused signal - backup handler only."""
        logger.debug("_on_processing_paused called - verifying state consistency")
        if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'state'):
            # Just verify state consistency - all UI updates handled by state change handler
            if self.orchestrator.state != ProcessingState.PAUSED:
                logger.warning(f"Expected PAUSED state but got {self.orchestrator.state}, triggering state handler")
                self._on_processing_state_changed(ProcessingState.PAUSED)
        else:
            logger.warning("Orchestrator not available for state check")
    
    def _on_processing_stopped(self):
        """Handle processing stopped signal - backup handler only."""
        logger.debug("_on_processing_stopped called - verifying state consistency")
        if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'state'):
            # Just verify state consistency - all UI updates handled by state change handler
            if self.orchestrator.state != ProcessingState.STOPPED:
                logger.warning(f"Expected STOPPED state but got {self.orchestrator.state}, triggering state handler")
                self._on_processing_state_changed(ProcessingState.STOPPED)
        else:
            logger.warning("Orchestrator not available for state check")
    
    def _on_processing_completed(self):
        """Handle processing completed signal."""
        # Stop activity animation
        self._activity_timer.stop()
        
        self._set_processing_status("⚙️ COMPLETED", "success")
        self.processing_status_bar_label.setText("Complete")
        
        # Show final speed statistics
        if self._processing_speed > 0:
            if self._processing_speed >= 1.0:
                final_speed = f"⚡ Avg Speed: {self._processing_speed:.2f} files/sec"
            else:
                seconds_per_file = 1.0 / self._processing_speed
                final_speed = f"⚡ Avg Speed: {seconds_per_file:.1f} sec/file"
            self.proc_speed_label.setText(final_speed)
        self.proc_eta_label.setText("⏱️ ETA: Done!")
        
        self._reset_processing_ui()
        
        # Show compact inline notification (single line for status bar style)
        message = (
            f"Processing completed - "
            f"Processed: {self.orchestrator.processed_count} | "
            f"Failed: {self.orchestrator.failed_count} | "
            f"Skipped: {self.orchestrator.skipped_count}"
        )
        self._show_notification(message, "success", auto_hide=8000)
        
        logger.info("UI updated: processing completed")
    
    def _on_item_processing_started(self, file_path):
        """Handle item processing started signal."""
        self._current_processing_file = file_path
        
        file_name = Path(file_path).name
        # Truncate long filenames
        if len(file_name) > 50:
            file_name = file_name[:47] + "..."
        self.proc_current_file_label.setText(file_name)
        
        # Update progress bar for this file
        if file_path in self._file_progress_bars:
            progress_bar = self._file_progress_bars[file_path]
            progress_bar.setRange(0, 100)
            progress_bar.setValue(10)
            progress_bar.setFormat("Starting...")
            self._set_progress_bar_style(progress_bar)
        
        # Get the current orchestrator state - don't update status if we're pausing/stopping
        if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'state'):
            state = self.orchestrator.state
            if state == ProcessingState.PAUSING:
                logger.debug("In PAUSING state, not updating bottom status bar")
                return
            elif state == ProcessingState.STOPPING:
                logger.debug("In STOPPING state, not updating bottom status bar")
                return
        
        # Update status to show activity
        if not self._processing_start_time:
            # First file
            self.processing_status_bar_label.setText("Analyzing first image (vision model loading)...")
        else:
            # Subsequent files - show we're actively processing
            elapsed = (datetime.now() - self._processing_start_time).total_seconds()
            if self._processing_speed > 0:
                avg_time = 1.0 / self._processing_speed
                self.processing_status_bar_label.setText(f"Analyzing image (avg {avg_time:.0f}s per file)...")
            else:
                self.processing_status_bar_label.setText("Analyzing image with vision model...")
        
        logger.debug(f"Processing: {file_name}")
    
    def _on_item_processing_completed(self, result):
        """Handle item processing completed signal."""
        # Update progress bar to completed
        if result.file_path in self._file_progress_bars:
            progress_bar = self._file_progress_bars[result.file_path]
            progress_bar.setValue(100)
            progress_bar.setFormat("✓ Completed")
            self._set_progress_bar_style(progress_bar, text_color=self.QUEUE_PALETTE['text_primary'])
        
        # Clear current file if this was it
        if self._current_processing_file == result.file_path:
            self._current_processing_file = None
            
        # Auto-update the results tab with the newly processed file
        try:
            # Since ProcessingResult doesn't have file_id, we can't use _add_file_to_results directly
            # Instead, we'll perform a targeted refresh to show the latest results
            self._refresh_results()
            
            # Highlight the newly processed file in the results table if possible
            file_name = Path(result.file_path).name
            rows = self.results_table.rowCount()
            for row in range(rows):
                item = self.results_table.item(row, 0)  # First column has filename
                if item and item.text() == file_name:
                    # Highlight the newly added row for better visibility
                    for col in range(self.results_table.columnCount()):
                        cell_item = self.results_table.item(row, col)
                        if cell_item:
                            from PySide6.QtGui import QColor
                            # Set a light green background for the new item
                            cell_item.setBackground(QColor(self.APP_PALETTE['selected_hover']))
                    break
        except Exception as e:
            logger.error(f"Failed to auto-update results: {e}")
            # Fallback to standard refresh in case of error
            self._refresh_results()
        
        if self.orchestrator:
            self.proc_processed_label.setText(f"✓ Processed: {self.orchestrator.processed_count}")
            
            # Get the current orchestrator state - don't update status if we're pausing/stopping
            state = self.orchestrator.state
            if state == ProcessingState.PAUSING:
                logger.debug("In PAUSING state, not updating bottom status bar on completion")
                return
            elif state == ProcessingState.STOPPING:
                logger.debug("In STOPPING state, not updating bottom status bar on completion")
                return
            elif state == ProcessingState.PAUSED:
                logger.debug("In PAUSED state, not updating bottom status bar on completion")
                return
            elif state == ProcessingState.STOPPED:
                logger.debug("In STOPPED state, not updating bottom status bar on completion")
                return
            
            # Update status to show progress
            self.processing_status_bar_label.setText(f"Completed {self.orchestrator.processed_count} files...")
    
    def _on_item_processing_failed(self, file_path, error_code, message):
        """Handle item processing failed signal."""
        # Update progress bar to failed
        if file_path in self._file_progress_bars:
            progress_bar = self._file_progress_bars[file_path]
            progress_bar.setValue(100)
            progress_bar.setFormat("✗ Failed")
            self._set_progress_bar_style(
                progress_bar,
                chunk_color=self.APP_PALETTE['alert_error'],
                border_color=self.APP_PALETTE['alert_error'],
                text_color=self.APP_PALETTE['text_primary']
            )
        
        # Clear current file if this was it
        if self._current_processing_file == file_path:
            self._current_processing_file = None
        
        if self.orchestrator:
            self.proc_failed_label.setText(f"✗ Failed: {self.orchestrator.failed_count}")
        logger.warning(f"Processing failed: {Path(file_path).name} - {error_code}")
    
    def _on_item_progress_updated(self, file_path, percentage, stage_description):
        """Handle item progress update signal."""
        if file_path in self._file_progress_bars:
            progress_bar = self._file_progress_bars[file_path]
            # Ensure percentage is at least 1%
            adjusted_percentage = max(1, percentage)
            progress_bar.setValue(adjusted_percentage)
            progress_bar.setFormat(f"{stage_description} ({adjusted_percentage}%)")
            
            # Update the current stage label with the processing stage
            self.proc_stage_label.setText(f"🔍 Stage: {stage_description}")
    
    def _on_review_required(self, result):
        """Handle review required signal."""
        dialog = ReviewDialog(self)
        dialog.load_result(result)
        dialog.approved.connect(self._on_review_approved)
        dialog.rejected.connect(self._on_review_rejected)
        dialog.exec()
    
    def _on_review_approved(self, approved_data):
        """Handle review approved."""
        logger.info(f"Review approved: {Path(approved_data['file_path']).name}")
        # TODO: Save to database
        self.status_label.setText("Results approved and saved")
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
    
    def _on_review_rejected(self, file_path):
        """Handle review rejected."""
        logger.info(f"Review rejected: {Path(file_path).name}")
        self.status_label.setText("Results rejected")
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
    
    def _on_processing_progress(self, current, total, current_file):
        """Handle processing progress signal with speed and ETA calculation."""
        from datetime import datetime, timedelta
        
        logger.debug(f"Progress update: {current}/{total} - {Path(current_file).name if current_file else 'N/A'}")
        
        self.proc_progress.setMaximum(total)
        # Ensure current is at least 1
        adjusted_current = max(1, current)
        self.proc_progress.setValue(adjusted_current)
        
        # Calculate processing speed and ETA
        now = datetime.now()
        
        # Initialize tracking on first progress update
        if self._processing_start_time is None and current >= 0:
            self._processing_start_time = now
            self._last_progress_time = now
            self._files_processed_in_batch = 0
            logger.debug(f"Initialized speed tracking at progress {current}/{total}")
            
            # Start an elapsed time update timer
            self._elapsed_timer = QTimer()
            self._elapsed_timer.setInterval(1000)  # Update every second
            self._elapsed_timer.timeout.connect(self._update_elapsed_time)
            self._elapsed_timer.start()
        
        # Calculate speed and ETA for any progress > 0
        if current > 0 and self._processing_start_time:
            elapsed = (now - self._processing_start_time).total_seconds()
            logger.debug(f"Speed calculation: current={current}, elapsed={elapsed:.2f}s")
            
            if elapsed > 0.5:  # Only calculate after at least 0.5 seconds elapsed
                self._processing_speed = current / elapsed
                
                # Format speed display
                if self._processing_speed >= 1.0:
                    speed_text = f"⚡ Speed: {self._processing_speed:.1f} files/sec"
                else:
                    seconds_per_file = 1.0 / self._processing_speed if self._processing_speed > 0 else 0
                    speed_text = f"⚡ Speed: {seconds_per_file:.1f} sec/file"
                
                logger.debug(f"Speed: {self._processing_speed:.3f} files/sec, Display: {speed_text}")
                self.proc_speed_label.setText(speed_text)
                
                # Calculate ETA
                remaining_files = total - current
                if remaining_files > 0 and self._processing_speed > 0:
                    eta_seconds = remaining_files / self._processing_speed
                    
                    # Format ETA display
                    if eta_seconds < 60:
                        eta_text = f"⏱️ ETA: {int(eta_seconds)}s"
                    elif eta_seconds < 3600:
                        minutes = int(eta_seconds / 60)
                        seconds = int(eta_seconds % 60)
                        eta_text = f"⏱️ ETA: {minutes}m {seconds}s"
                    else:
                        hours = int(eta_seconds / 3600)
                        minutes = int((eta_seconds % 3600) / 60)
                        eta_text = f"⏱️ ETA: {hours}h {minutes}m"
                    
                    logger.debug(f"ETA: {eta_text} ({eta_seconds:.1f}s remaining for {remaining_files} files)")
                    self.proc_eta_label.setText(eta_text)
                elif remaining_files == 0:
                    self.proc_eta_label.setText("⏱️ ETA: Done!")
                else:
                    self.proc_eta_label.setText("⏱️ ETA: --")
            else:
                # Too early to calculate meaningful speed
                self.proc_speed_label.setText("⚡ Speed: calculating...")
                self.proc_eta_label.setText("⏱️ ETA: calculating...")
        elif current == 0:
            # Just started, show placeholder
            self.proc_speed_label.setText("⚡ Speed: --")
            self.proc_eta_label.setText("⏱️ ETA: --")
        
        # Update skipped count
        if self.orchestrator:
            self.proc_skipped_label.setText(f"⊘ Skipped: {self.orchestrator.skipped_count}")
        
        # Update progress bar format to show more detail including current file
        if current == total:
            self.proc_progress.setFormat(f"%v / %m files (100%) • Complete!")
        else:
            percentage = int((current / total) * 100) if total > 0 else 0
            current_file_name = Path(current_file).name if current_file else "..."
            
            # Show more detailed progress info with current file
            if current > 0 and current_file:
                self.proc_progress.setFormat(f"%v / %m files ({percentage}%) • Processing: {current_file_name}")
            else:
                self.proc_progress.setFormat(f"%v / %m files ({percentage}%) • Processing...")
    
    def _on_processing_state_changed(self, state):
        """Handle processing state changed signal."""
        logger.info(f"Processing state changed to {state}")
        
        # Sync new controls state first
        self._sync_new_controls_state()
        
        if state == ProcessingState.IDLE:
            self._set_processing_status("⚙️ IDLE")
            self.processing_status_bar_label.setText("Idle")
            self._reset_processing_ui()
            
            # Enable retry button if there are failed items
            if self.orchestrator and self.orchestrator.failed_count > 0:
                self.proc_retry_btn.setEnabled(True)
            else:
                self.proc_retry_btn.setEnabled(False)
        elif state == ProcessingState.PAUSING:
            # Start spinner animation for PAUSING state
            if not self._activity_timer.isActive():
                self._activity_timer.start(80)
            
            self._set_processing_status("⠋ PAUSING...", "warning")
            self.processing_status_bar_label.setText("Pausing...")
        elif state == ProcessingState.PAUSED:
            # Stop activity animation
            if hasattr(self, '_activity_timer') and self._activity_timer.isActive():
                self._activity_timer.stop()
            
            # Stop progress bar pulse animation
            if hasattr(self, '_progress_pulse_timer') and self._progress_pulse_timer.isActive():
                self._progress_pulse_timer.stop()
            
            # Set status text directly (don't rely on spinner animation)
            self._set_processing_status("⚙️ PAUSED", "warning")
            self.processing_status_bar_label.setText("Paused")
            
            # Update the progress bar format to show paused
            completed = self.proc_progress.value()
            maximum = self.proc_progress.maximum()
            percentage = int(completed / max(1, maximum) * 100)
            self.proc_progress.setFormat(f"%v / %m files ({percentage}%) • Paused")
            
            # Refresh the queue table to show current status of all items
            self._refresh_queue_table()
            
            # Reset the stage info to show paused
            self.proc_stage_label.setText("🔍 Stage: Paused")
            
            # Save the time when processing was paused and record elapsed time
            from datetime import datetime
            self._pause_time = datetime.now()
            if self._processing_start_time:
                self._paused_elapsed_seconds = (self._pause_time - self._processing_start_time).total_seconds()
            
            # Update buttons safely
            self._update_control_buttons_safe(start_enabled=True, pause_enabled=True)
            # Update button text for old controls only
            if not self._using_new_controls:
                if hasattr(self, 'proc_start_btn') and self.proc_start_btn:
                    self.proc_start_btn.setText("▶ Resume")
                if hasattr(self, 'proc_pause_btn') and self.proc_pause_btn:
                    self.proc_pause_btn.setText("▶ Resume")
            self._style_button(self.proc_pause_btn, variant="success")
            # Also update the other pause button if it exists
            if hasattr(self, 'pause_btn'):
                self.pause_btn.setEnabled(True)
                self.pause_btn.setText("▶ Resume")
                self._style_button(self.pause_btn, variant="success")
            self._update_control_buttons_safe(stop_enabled=True, retry_enabled=False)  # Disable retry during paused state
        elif state == ProcessingState.STOPPING:
            # Start spinner animation for STOPPING state
            if not self._activity_timer.isActive():
                self._activity_timer.start(80)
            
            self._set_processing_status("⠋ STOPPING...", "error")
            self.processing_status_bar_label.setText("Stopping...")
            
            # Update buttons safely
            self._update_control_buttons_safe(
                start_enabled=False,
                pause_enabled=False,
                stop_enabled=False,
                retry_enabled=False  # Disable retry during stopping
            )
        elif state == ProcessingState.STOPPED:
            # Stop activity animation
            self._activity_timer.stop()
            
            # Set status text directly (don't rely on spinner animation)
            self._set_processing_status("⚙️ STOPPED", "error")
            self.processing_status_bar_label.setText("Stopped")
            
            # Update buttons safely
            retry_enabled = (self.orchestrator and self.orchestrator.failed_count > 0)
            self._update_control_buttons_safe(
                start_enabled=True,
                pause_enabled=False,
                stop_enabled=False,
                retry_enabled=retry_enabled
            )
            # Update button text for old controls only
            if not self._using_new_controls and hasattr(self, 'proc_start_btn') and self.proc_start_btn:
                self.proc_start_btn.setText("▶ Start")
            else:
                self.proc_retry_btn.setEnabled(False)
        elif state == ProcessingState.RUNNING:
            # Start spinner animation for RUNNING state if not already active
            if not self._activity_timer.isActive():
                self._activity_timer.start(80)
            
            # Start progress bar pulse animation
            if not self._progress_pulse_timer.isActive():
                self._progress_pulse_timer.start()

            self._set_processing_status("⚙️ RUNNING", "info")
                
            # Make sure elapsed timer is started and handle resuming
            from datetime import datetime, timedelta
            now = datetime.now()
            
            # Handle initial start vs. resume from pause
            if self._processing_start_time is None:
                # Initial start
                self._processing_start_time = now
                self._paused_elapsed_seconds = 0
            elif self._pause_time is not None:
                # Calculate pause duration and adjust start time accordingly
                pause_duration = (now - self._pause_time).total_seconds()
                # Adjust start time to account for the pause duration
                self._processing_start_time = now - timedelta(seconds=self._paused_elapsed_seconds)
                # Reset pause tracking
                self._pause_time = None
                
            # Create and start elapsed timer if not already active
            if not hasattr(self, '_elapsed_timer') or not self._elapsed_timer.isActive():
                self._elapsed_timer = QTimer()
                self._elapsed_timer.setInterval(1000)  # Update every second
                self._elapsed_timer.timeout.connect(self._update_elapsed_time)
                self._elapsed_timer.start()
                logger.debug("Started elapsed time timer")
            self.processing_status_bar_label.setText("Processing...")
            
            # Update buttons safely - enable pause during processing
            self._update_control_buttons_safe(start_enabled=False, pause_enabled=True)
            # Update button text and style for old controls only
            if not self._using_new_controls:
                if hasattr(self, 'proc_pause_btn') and self.proc_pause_btn:
                    self.proc_pause_btn.setText("⏸ Pause")
                    self._style_button(self.proc_pause_btn, variant="warning")
            # Also update the other pause button if it exists
            if hasattr(self, 'pause_btn'):
                self.pause_btn.setEnabled(True)
                self.pause_btn.setText("⏸ Pause")
                self._style_button(self.pause_btn, variant="warning")
            self._update_control_buttons_safe(stop_enabled=True, retry_enabled=False)  # Disable retry during processing
            
            # Refresh the queue table to show updated status (especially when resuming)
            self._refresh_queue_table()
    
    def _sync_new_controls_state(self):
        """Sync the new processing controls with current application state."""
        if not self.processing_controls_integration:
            return
            
        try:
            # Throttle updates to avoid excessive calls
            import time
            current_time = time.time()
            if current_time - self._last_progress_update < 0.1:  # 100ms throttle
                return
            self._last_progress_update = current_time
            
            # Update retry button visibility based on failed items
            failed_count = 0
            if self.orchestrator and hasattr(self.orchestrator, 'failed_count'):
                failed_count = self.orchestrator.failed_count
            elif hasattr(self, 'queue_manager') and self.queue_manager:
                # Fallback to checking queue manager for failed items
                stats = self.queue_manager.get_statistics()
                failed_count = stats.get('failed', 0)
                
            self.processing_controls_integration.show_retry_button(failed_count > 0)
            
            # Update progress information
            if self.orchestrator:
                current = getattr(self.orchestrator, 'processed_count', 0)
                total_pending = 0
                if hasattr(self, 'queue_manager') and self.queue_manager:
                    stats = self.queue_manager.get_statistics()
                    total_pending = stats.get('pending', 0) + stats.get('processing', 0)
                
                total = current + total_pending + failed_count
                if total > 0:  # Only update if we have meaningful data
                    self.processing_controls_integration.update_progress(current, total, failed_count)
            
            # Enable confirmation dialogs (can be made configurable later)
            self.processing_controls_integration.enable_confirmation_dialogs(True)
            
        except Exception as e:
            logger.warning(f"Failed to sync new controls state: {e}")
    
    def _reset_processing_ui(self):
        """Reset processing UI to initial state."""
        self._update_control_buttons_safe(start_enabled=True)
        # Update button text for old controls only
        if not self._using_new_controls and hasattr(self, 'proc_start_btn') and self.proc_start_btn:
            self.proc_start_btn.setText("▶ Start")
        
        # Reset pause tracking
        self._pause_time = None
        self._paused_elapsed_seconds = 0
        
        # Stop progress pulse animation
        if hasattr(self, '_progress_pulse_timer') and self._progress_pulse_timer.isActive():
            self._progress_pulse_timer.stop()
        
        # Stop elapsed time timer
        if hasattr(self, '_elapsed_timer') and self._elapsed_timer.isActive():
            self._elapsed_timer.stop()
            
        # Reset stage label and elapsed time
        self.proc_stage_label.setText("🔍 Stage: --")
        self.proc_elapsed_label.setText("⏳ Elapsed: --")
        self.proc_pause_btn.setEnabled(False)
        self.proc_stop_btn.setEnabled(False)
        self.proc_current_file_label.setText("No file processing")
        
        # Reset speed/ETA if processing stopped before completion
        if not self._processing_speed:
            self.proc_speed_label.setText("⚡ Speed: --")
            self.proc_eta_label.setText("⏱️ ETA: --")
    
    def _update_elapsed_time(self):
        """Update the elapsed time label based on processing start time."""
        # Display frozen elapsed time during PAUSED state
        if self.orchestrator and self.orchestrator.state == ProcessingState.PAUSED and self._paused_elapsed_seconds > 0:
            # Use the saved elapsed seconds from when we paused
            elapsed_seconds = self._paused_elapsed_seconds
        elif not self._processing_start_time or not self.orchestrator or self.orchestrator.state not in [ProcessingState.RUNNING]:
            if hasattr(self, '_elapsed_timer') and self._elapsed_timer.isActive():
                self._elapsed_timer.stop()
            return
        else:
            # Normal running state - calculate from start time
            elapsed_seconds = (datetime.now() - self._processing_start_time).total_seconds()
        
        # Format elapsed time display
        if elapsed_seconds < 60:
            elapsed_text = f"⏳ Elapsed: {int(elapsed_seconds)}s"
        elif elapsed_seconds < 3600:
            minutes = int(elapsed_seconds / 60)
            seconds = int(elapsed_seconds % 60)
            elapsed_text = f"⏳ Elapsed: {minutes}m {seconds}s"
        else:
            hours = int(elapsed_seconds / 3600)
            minutes = int((elapsed_seconds % 3600) / 60)
            elapsed_text = f"⏳ Elapsed: {hours}h {minutes}m"
        
        self.proc_elapsed_label.setText(elapsed_text)
    
    def _pulse_progress_bar(self):
        """Create a subtle animation effect on the progress bar during processing."""
        if not self.orchestrator or self.orchestrator.state not in [ProcessingState.RUNNING]:
            self._progress_pulse_timer.stop()
            
    def _export_results(self, format=None):
        """Export analysis results to CSV or JSON file."""
        from PySide6.QtWidgets import QFileDialog
        
        # Determine file filters based on format parameter
        if format == "csv":
            file_filter = "CSV Files (*.csv)"
            default_extension = ".csv"
        elif format == "json":
            file_filter = "JSON Files (*.json)"
            default_extension = ".json"
        else:
            file_filter = "CSV Files (*.csv);;JSON Files (*.json)"
            default_extension = None
            
        # Get export path from user
        export_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "",
            file_filter
        )
        
        if not export_path:
            return  # User cancelled
        
        try:
            if export_path.lower().endswith('.csv'):
                self._export_to_csv(export_path)
            elif export_path.lower().endswith('.json'):
                self._export_to_json(export_path)
            else:
                # Add default extension based on format or filter
                if default_extension:
                    export_path += default_extension
                    if export_path.lower().endswith('.csv'):
                        self._export_to_csv(export_path)
                    elif export_path.lower().endswith('.json'):
                        self._export_to_json(export_path)
                elif "CSV" in selected_filter:
                    export_path += ".csv"
                    self._export_to_csv(export_path)
                else:
                    export_path += ".json"
                    self._export_to_json(export_path)
            
            self._show_notification(f"Results exported to {export_path}", "info")
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            self._show_notification(f"Export failed: {str(e)}", "error")
            
    def _export_to_csv(self, filepath, file_ids=None):
        """Export results to CSV format.
        
        Args:
            filepath: Path to save the CSV file
            file_ids: Optional list of file IDs to export. If None, exports all files.
        """
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['File', 'Path', 'Tags', 'Description', 'Processed Date'])
            
            # Write data from database
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Base SQL query
                sql_query = """
                    SELECT 
                        f.file_id,
                        f.file_path,
                        GROUP_CONCAT(c.tag_text, '; ') as tags,
                        d.description_text,
                        f.processed_date
                    FROM files f
                    LEFT JOIN classifications c ON f.file_id = c.file_id
                    LEFT JOIN descriptions d ON f.file_id = d.file_id
                    WHERE f.processed_date IS NOT NULL
                """
                
                # Add file_id filter if specific IDs are provided
                params = ()
                if file_ids:
                    # Use parameter placeholders based on number of IDs
                    placeholders = ','.join('?' * len(file_ids))
                    sql_query += f" AND f.file_id IN ({placeholders})"
                    params = tuple(file_ids)
                
                # Complete the query
                sql_query += """
                    GROUP BY f.file_id
                    ORDER BY f.processed_date DESC
                """
                
                # Execute the query with or without file_id parameters
                cursor.execute(sql_query, params)
                
                rows = cursor.fetchall()
                for row in rows:
                    file_path = row['file_path']
                    filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                    
                    writer.writerow([
                        filename,
                        file_path,
                        row['tags'] or '',
                        row['description_text'] or '',
                        row['processed_date'] or ''
                    ])
        
        logger.info(f"Exported {len(rows)} records to CSV: {filepath}")
            
    def _export_to_json(self, filepath, file_ids=None):
        """Export results to JSON format.
        
        Args:
            filepath: Path to save the JSON file
            file_ids: Optional list of file IDs to export. If None, exports all files.
        """
        import json
        
        results = []
        
        # Get data from database
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Base SQL query
            sql_query = """
                SELECT file_id, file_path, file_hash, processed_date
                FROM files
                WHERE processed_date IS NOT NULL
            """
            
            # Add file_id filter if specific IDs are provided
            params = ()
            if file_ids:
                # Use parameter placeholders based on number of IDs
                placeholders = ','.join('?' * len(file_ids))
                sql_query += f" AND file_id IN ({placeholders})"
                params = tuple(file_ids)
            
            # Complete the query
            sql_query += " ORDER BY processed_date DESC"
            
            # Execute the query with or without file_id parameters
            cursor.execute(sql_query, params)
            
            files = cursor.fetchall()
            
            for file in files:
                file_id = file['file_id']
                file_record = {
                    'file_id': file_id,
                    'file_path': file['file_path'],
                    'file_hash': file['file_hash'],
                    'processed_date': file['processed_date'],
                    'tags': [],
                    'description': None
                }
                
                # Get tags for this file
                cursor.execute("""
                    SELECT tag_text, confidence, model_used 
                    FROM classifications 
                    WHERE file_id = ?
                """, (file_id,))
                
                tags = cursor.fetchall()
                file_record['tags'] = [
                    {
                        'text': tag['tag_text'],
                        'confidence': tag['confidence'],
                        'model': tag['model_used']
                    }
                    for tag in tags
                ]
                
                # Get description for this file
                cursor.execute("""
                    SELECT description_text, model_used 
                    FROM descriptions 
                    WHERE file_id = ?
                """, (file_id,))
                
                description = cursor.fetchone()
                if description:
                    file_record['description'] = {
                        'text': description['description_text'],
                        'model': description['model_used']
                    }
                
                results.append(file_record)
        
        # Write to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported {len(results)} records to JSON: {filepath}")
    
    def _delete_selected_result(self):
        """Delete the currently selected result from the database."""
        from PySide6.QtWidgets import QMessageBox
        
        # Get the current selection
        current_row = self.results_table.currentRow()
        
        if current_row < 0:
            self._show_notification("Please select a result to delete", "warning", 3000)
            return
        
        # Get file_id and filename from the selected row
        file_id = self.results_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        filename = self.results_table.item(current_row, 2).text()
        
        if not file_id:
            logger.error("No file_id found in selected row")
            return
        
        # Confirm deletion with the user
        confirm = QMessageBox.question(
            self,
            "Delete Result",
            f"Are you sure you want to delete the result for '{filename}'?\n\n"
            "This will remove all analysis data for this file from the database. "
            "The original file will not be affected.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Delete the record from database
            success = self.db.delete_file_record(file_id)
            
            if success:
                # Remove from the table
                self.results_table.removeRow(current_row)
                self._update_results_count_label()
                self._show_notification("Result deleted successfully", "success")
                logger.info(f"Deleted result for file: {filename} (ID: {file_id})")
            else:
                self._show_notification("Failed to delete result", "error", 3000)
                
        except Exception as e:
            logger.error(f"Error deleting result: {e}")
            self._show_notification(f"Error: {e}", "error", 5000)
            
    def _show_ai_models(self):
        """Show AI model management dialog."""
        from src.ui.ai_model_dialog import AIModelDialog
        
        if not self.llm_adapter:
            self._show_notification("LLM adapter not available", "error")
            return
            
        # Pass the LLM adapter and self as parent
        dialog = AIModelDialog(self.llm_adapter, self)
        dialog.exec()
        
        # Create a subtle ripple effect in the progress bar
        self._progress_pulse_effect = (self._progress_pulse_effect + 1) % 4
        
        colors = self.APP_PALETTE
        accent = colors['accent']
        focus = colors['focus']
        selected = colors['selected']
        selected_hover = colors['selected_hover']

        if self._progress_pulse_effect == 0:
            chunk_style = f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:0.5 {focus}, stop:1 {selected});
            """
        elif self._progress_pulse_effect == 1:
            chunk_style = f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {focus}, stop:0.5 {selected}, stop:1 {selected_hover});
            """
        elif self._progress_pulse_effect == 2:
            chunk_style = f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {selected}, stop:0.5 {selected_hover}, stop:1 {accent});
            """
        else:
            chunk_style = f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:0.3 {selected_hover}, stop:0.7 {focus}, stop:1 {accent});
            """
        
        # Update progress bar style with the new gradient
        current_style = self.proc_progress.styleSheet()
        style_parts = current_style.split("QProgressBar::chunk {")
        if len(style_parts) == 2:
            style_prefix = style_parts[0] + "QProgressBar::chunk {"
            style_suffix = style_parts[1].split("}", 1)[1]
            new_style = style_prefix + chunk_style + "border-radius: 6px;\nmargin: 1px;\n}" + style_suffix
            self.proc_progress.setStyleSheet(new_style)
    
    # Results tab handlers
    def _refresh_results(self):
        """Refresh the results table with analyzed files."""
        try:
            # Get analyzed files from database
            files = self.db.get_analyzed_files(limit=1000)
            
            # Update table
            self.results_table.setRowCount(0)
            
            for file_data in files:
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                
                # File name (just the name, not full path)
                file_path = Path(file_data['file_path'])
                self.results_table.setItem(row, 0, QTableWidgetItem(file_path.name))
                
                # File type
                file_type = file_data.get('file_type', '').upper() or 'UNKNOWN'
                self.results_table.setItem(row, 1, QTableWidgetItem(file_type))
                
                # Tags (truncated if too long)
                tags = file_data.get('tags', '') or '-'
                if len(tags) > 50:
                    tags = tags[:47] + '...'
                self.results_table.setItem(row, 2, QTableWidgetItem(tags))
                
                # Description (truncated)
                description = file_data.get('description_text', '') or '-'
                if len(description) > 100:
                    description = description[:97] + '...'
                self.results_table.setItem(row, 3, QTableWidgetItem(description))
                
                # Confidence (average of tag and description confidence)
                tag_conf = file_data.get('avg_tag_confidence', 0) or 0
                desc_conf = file_data.get('description_confidence', 0) or 0
                avg_conf = (tag_conf + desc_conf) / 2 if (tag_conf or desc_conf) else 0
                
                conf_text = f"{avg_conf:.1%}" if avg_conf > 0 else "-"
                conf_item = QTableWidgetItem(conf_text)
                
                # Color code confidence
                if avg_conf >= 0.8:
                    conf_item.setForeground(Qt.GlobalColor.green)
                elif avg_conf >= 0.5:
                    conf_item.setForeground(Qt.GlobalColor.yellow)
                else:
                    conf_item.setForeground(Qt.GlobalColor.red)
                
                self.results_table.setItem(row, 4, conf_item)
                
                # Analyzed date
                analyzed_at = file_data.get('analyzed_at', '')
                if analyzed_at:
                    try:
                        dt = datetime.fromisoformat(analyzed_at)
                        date_str = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        date_str = analyzed_at
                else:
                    date_str = '-'
                
                self.results_table.setItem(row, 5, QTableWidgetItem(date_str))
                
                # Store file_id in row data for later retrieval
                self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, file_data['file_id'])
            
            # Update count
            self.results_count_label.setText(str(len(files)))
            
            logger.info(f"Results table refreshed: {len(files)} files")
            
        except Exception as e:
            logger.error(f"Error refreshing results: {e}")
            self._show_notification(f"Error loading results: {e}", "error", 5000)
    



    def _search_results(self):
        """Search results using FTS5."""
        query = self.results_search_input.text().strip()
        
        if not query:
            self._refresh_results()
            return
        
        try:
            # Search using FTS5
            results = self.db.search_full_text(query, search_type='both', limit=100)
            
            if not results:
                self._show_notification("No results found", "info", 3000)
                return
            
            # Group results by file_id
            file_results = {}
            for result in results:
                file_id = result['file_id']
                if file_id not in file_results:
                    file_results[file_id] = result
            
            # Update table with search results
            self.results_table.setRowCount(0)
            
            for file_id, result in file_results.items():
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                
                # File name
                file_path = Path(result['file_path'])
                self.results_table.setItem(row, 0, QTableWidgetItem(file_path.name))
                
                # File type
                file_type = result.get('file_type', '').upper() or 'UNKNOWN'
                self.results_table.setItem(row, 1, QTableWidgetItem(file_type))
                
                # Show what matched
                if result.get('result_type') == 'ocr':
                    match_text = f"OCR: {result.get('ocr_text', '')[:50]}..."
                else:
                    match_text = f"Tag: {result.get('tag_text', '')}"
                
                self.results_table.setItem(row, 2, QTableWidgetItem(match_text))
                self.results_table.setItem(row, 3, QTableWidgetItem("[Search result - view details]"))
                
                # Confidence
                conf = result.get('confidence', result.get('ocr_confidence', 0))
                conf_text = f"{conf:.1%}" if conf > 0 else "-"
                self.results_table.setItem(row, 4, QTableWidgetItem(conf_text))
                
                self.results_table.setItem(row, 5, QTableWidgetItem("-"))
                
                # Store file_id
                self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, file_id)
            
            # Update count
            self.results_count_label.setText(str(len(file_results)))
            
            self._show_notification(f"Found {len(file_results)} matching files", "success", 3000)
            
        except Exception as e:
            logger.error(f"Error searching results: {e}")
            self._show_notification(f"Search error: {e}", "error", 5000)
    
    def _clear_search(self):
        """Clear search and show all results."""
        self.results_search_input.clear()
        self._refresh_results()
    
    def _clear_all_results(self):
        """Clear all results from the database with custom styled dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Clear All Results")
        dialog.setModal(True)
        dialog.setMinimumWidth(450)

        colors = self.APP_PALETTE
        dialog.setStyleSheet(
            f"""
            QDialog {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['dividers']};
                border-radius: 10px;
            }}
            QLabel {{
                color: {colors['text_secondary']};
            }}
            """
        )
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Icon and title row
        title_row = QHBoxLayout()
        
        # Warning icon
        icon_label = QLabel("⚠️")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row.addWidget(icon_label)
        
        # Title
        title_label = QLabel("Delete All Results?")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(
            f"color: {colors['text_primary']}; background: transparent; padding-left: 10px;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(title_label, 1)
        
        layout.addLayout(title_row)
        
        # Message
        message = QLabel(
            "This will permanently delete all analyzed files from the database.\n\n"
            "• All tags and descriptions will be removed\n"
            "• OCR text data will be deleted\n"
            "• This action cannot be undone"
        )
        message.setWordWrap(True)
        message.setStyleSheet(
            f"""
            QLabel {{
                color: {colors['text_secondary']};
                font-size: 11pt;
                background: transparent;
                padding: 10px;
                line-height: 1.5;
            }}
            """
        )
        layout.addWidget(message)
        
        # Get count for display
        count = 0
        if hasattr(self, 'db') and self.db:
            try:
                stats = self.db.get_statistics()

                count = stats.get('files_count', 0)
            except:
                pass
        
        if count > 0:
            count_label = QLabel(f"📊 {count} file{'s' if count != 1 else ''} will be deleted")
            count_color = colors['alert_error']
            count_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {count_color};
                    font-size: 12pt;
                    font-weight: 600;
                    background-color: {colors['surface_alt']};
                    padding: 12px;
                    border-radius: 8px;
                    border: 1px solid {count_color};
                }}
                """
            )
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(count_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(120)
        self._style_button(cancel_btn, variant="secondary")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete All")
        delete_btn.setMinimumHeight(40)
        delete_btn.setMinimumWidth(140)
        self._style_button(delete_btn, variant="danger")
        delete_btn.clicked.connect(dialog.accept)
        delete_btn.setDefault(False)  # Don't make it default (safer)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        # Show dialog and handle result
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            try:
                # Clear all results from database using the Database method
                if hasattr(self, 'db') and self.db:
                    count = self.db.clear_all_results()
                    
                    # Refresh the table
                    self._refresh_results()
                    
                    # Show success notification
                    self._show_notification(f"Cleared {count} analyzed files", "success", 3000)
                    logger.info(f"Cleared {count} results from database")
                else:
                    self._show_notification("Database not available", "error", 3000)
            except Exception as e:
                logger.error(f"Failed to clear results: {e}")
                self._show_notification(f"Failed to clear results: {str(e)}", "error", 5000)
    
    def _view_result_details(self):
        """View detailed information for selected result."""
        self._view_selected_result()
    
    def _view_selected_result(self):
        """View detailed information for the currently selected result."""
        current_row = self.results_table.currentRow()
        
        if current_row < 0:
            self._show_notification("Please select a file to view", "warning", 3000)
            return
        
        # Get file_id from row data
        file_id = self.results_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not file_id:
            logger.error("No file_id found in selected row")
            return
        
        try:
            # Get detailed file information
            file_details = self.db.get_file_details(file_id)
            
            if not file_details:
                self._show_notification("File details not found", "error", 3000)
                return
            
            # Create details dialog
            self._show_file_details_dialog(file_details)
            
        except Exception as e:
            logger.error(f"Error viewing result details: {e}")
            self._show_notification(f"Error loading details: {e}", "error", 5000)

    def _open_result_file(self) -> None:
        """Open the currently selected result file with the default application."""
        current_row = self.results_table.currentRow()

        if current_row < 0:
            self._show_notification("Please select a file to open", "warning", 3000)
            return

        file_item = self.results_table.item(current_row, 0)
        if file_item is None:
            self._show_notification("Unable to determine selected file", "error", 3000)
            return

        file_id = file_item.data(Qt.ItemDataRole.UserRole)
        if not file_id:
            logger.error("Selected row is missing file_id metadata")
            self._show_notification("Unable to locate file in database", "error", 3000)
            return

        try:
            file_details = self.db.get_file_details(file_id)
            if not file_details:
                self._show_notification("File details not found", "error", 3000)
                return

            file_path = Path(file_details.get("file_path", ""))
            if not file_path:
                self._show_notification("File path unavailable", "error", 3000)
                return

            if not file_path.exists():
                self._show_notification("File not found on disk", "warning", 4000)
                logger.warning(f"Result file missing on disk: {file_path}")
                return

            opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
            if not opened:
                self._show_notification("Unable to open file", "error", 4000)
                logger.error(f"QDesktopServices failed to open file: {file_path}")
            else:
                logger.info(f"Opened result file: {file_path}")

        except Exception as e:
            logger.error(f"Error opening result file: {e}")
            self._show_notification(f"Error opening file: {e}", "error", 5000)
    
    def _export_selected_results(self):
        """Export currently selected results to CSV or JSON file."""
        # Check if any rows are selected
        selected_rows = set()
        for index in self.results_table.selectedIndexes():
            selected_rows.add(index.row())
            
        if not selected_rows:
            self._show_notification("No results selected. Please select at least one result to export.", "warning", 3000)
            return
        
        # Get the file IDs from selected rows
        selected_file_ids = []
        for row in selected_rows:
            file_id_item = self.results_table.item(row, 0)
            if file_id_item:
                file_id = file_id_item.data(Qt.ItemDataRole.UserRole)
                if file_id:
                    selected_file_ids.append(file_id)
        
        if not selected_file_ids:
            self._show_notification("Could not retrieve selected file IDs", "error", 3000)
            return
            
        from PySide6.QtWidgets import QFileDialog
        
        # Let user choose file format and location
        file_filter = "CSV Files (*.csv);;JSON Files (*.json)"
        export_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Selected Results",
            "",
            file_filter
        )
        
        if not export_path:
            return  # User cancelled
        
        try:
            # Determine export format from file extension or filter
            if export_path.lower().endswith('.csv'):
                self._export_to_csv(export_path, selected_file_ids)
            elif export_path.lower().endswith('.json'):
                self._export_to_json(export_path, selected_file_ids)
            else:
                # Add default extension based on filter
                if "CSV" in selected_filter:
                    export_path += ".csv"
                    self._export_to_csv(export_path, selected_file_ids)
                else:
                    export_path += ".json"
                    self._export_to_json(export_path, selected_file_ids)
            
            self._show_notification(f"Selected results exported to {export_path}", "info")
            
        except Exception as e:
            logger.error(f"Failed to export selected results: {e}")
            self._show_notification(f"Export failed: {e}", "error", 5000)
    
    def _show_file_details_dialog(self, file_details: dict):
        """
        Show a dialog with complete file analysis details.
        
        Args:
            file_details: Complete file information from database
        """
        from PySide6.QtWidgets import QDialog, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Details: {Path(file_details['file_path']).name}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create text display
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        
        # Format details as readable text
        text_lines = [
            "═" * 80,
            f"FILE: {file_details['file_path']}",
            "═" * 80,
            f"Type: {file_details.get('file_type', 'Unknown')}",
            f"Pages: {file_details.get('page_count', 0)}",
            f"Size: {file_details.get('file_size', 0):,} bytes",
            f"Analyzed: {file_details.get('analyzed_at', 'Unknown')}",
            "",
            "─" * 80,
            "DESCRIPTION",
            "─" * 80,
        ]
        
        if file_details.get('description'):
            desc = file_details['description']
            text_lines.append(f"{desc.get('description_text', 'No description')}")
            text_lines.append(f"Confidence: {desc.get('confidence', 0):.1%}")
            text_lines.append(f"Model: {desc.get('model_used', 'Unknown')}")
        else:
            text_lines.append("No description available")
        
        text_lines.extend([
            "",
            "─" * 80,
            "TAGS / CLASSIFICATIONS",
            "─" * 80,
        ])
        
        if file_details.get('classifications'):
            for i, classification in enumerate(file_details['classifications'], 1):
                text_lines.append(f"{i}. {classification['tag_text']} (confidence: {classification['confidence']:.1%})")
        else:
            text_lines.append("No classifications available")
        
        text_lines.extend([
            "",
            "─" * 80,
            "OCR TEXT (by page)",
            "─" * 80,
        ])
        
        if file_details.get('pages'):
            for page in file_details['pages']:
                text_lines.append(f"\n--- Page {page['page_number']} (OCR Mode: {page.get('ocr_mode', 'Unknown')}, Confidence: {page.get('ocr_confidence', 0):.1%}) ---")
                text_lines.append(page.get('ocr_text', 'No OCR text'))
        else:
            text_lines.append("No OCR pages available")
        
        text_lines.append("\n" + "═" * 80)
        
        details_text.setPlainText("\n".join(text_lines))
        
        layout.addWidget(details_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def showEvent(self, event):
        """Called when window is about to be shown - defer heavy operations here."""
        super().showEvent(event)
        
        # Only do this once (on first show)
        if not hasattr(self, '_ai_status_check_scheduled'):
            self._ai_status_check_scheduled = True
            
            # Schedule AI status check AFTER window is shown
            # This ensures window appears even if AI check is slow
            QTimer.singleShot(500, self._check_ai_status)
            logger.info("Scheduled AI status check after window show")
    
    def closeEvent(self, event):
        """Handle window close event - cleanup worker thread."""
        logger.info("Application closing, cleaning up worker thread...")
        
        # Stop processing if running
        if self.orchestrator:
            self.orchestrator.stop_processing()
        
        # Stop and wait for worker thread
        if self._processing_thread and self._processing_thread.isRunning():
            self._processing_thread.quit()
            self._processing_thread.wait(5000)  # Wait up to 5 seconds
            
            if self._processing_thread.isRunning():
                logger.warning("Worker thread did not stop gracefully, terminating...")
                self._processing_thread.terminate()
                self._processing_thread.wait()
        
        logger.info("Worker thread cleanup complete")
        event.accept()
    
    # Removed resizeEvent and _position_notification_banner methods
    # since we're now using the status bar for notifications