"""
Main application window for Previewless Insight Viewer.
"""
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QStatusBar, QMenuBar, QMenu, QPushButton,
    QListWidget, QTableWidget, QTableWidgetItem, QProgressBar,
    QFileDialog, QGroupBox, QHeaderView, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QTimer, QThread, QMetaObject, Q_ARG, Signal
from PySide6.QtGui import QAction, QColor

from src.core.config import ConfigManager
from src.models.database import Database
from src.services.file_watcher import FileWatcherService
from src.services.queue_manager import QueueManager, QueueItemStatus
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


logger = get_logger("ui.main_window")


class MainWindow(QMainWindow):
    """Main application window."""
    
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
        main_layout.addWidget(self.tabs)
        
        # Add tabs (removed Processing tab - now in top bar)
        self.tabs.addTab(self._create_watch_tab(), "📁 Watch")
        self.tabs.addTab(self._create_queue_tab(), "📋 Queue")
        self.tabs.addTab(self._create_results_tab(), "📊 Results")
        
        # Notification system now uses status bar, no separate banner needed
        
        # Create status bar
        self._create_status_bar()
        
        # Auto-refresh timer to prevent UI lockups
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh_ui)
        self._refresh_timer.start(1000)  # Refresh every second
    
    def _create_processing_status_bar(self) -> None:
        """Create prominent processing status bar at top of window."""
        self.processing_status_bar = QWidget()
        self.processing_status_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 8px;
                border: 2px solid #2a5298;
                padding: 8px;
            }
        """)
        self.processing_status_bar.setMinimumHeight(120)
        
        bar_layout = QVBoxLayout(self.processing_status_bar)
        bar_layout.setSpacing(8)
        
        # Top row: Status and controls
        top_row = QHBoxLayout()
        
        # Status indicator (large and prominent)
        status_container = QVBoxLayout()
        self.proc_status_label = QLabel("⚙️ IDLE")
        self.proc_status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        status_container.addWidget(self.proc_status_label)
        
        self.proc_current_file_label = QLabel("No file processing")
        self.proc_current_file_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 10pt;
                background: transparent;
            }
        """)
        status_container.addWidget(self.proc_current_file_label)
        
        top_row.addLayout(status_container, 1)
        
        # Control buttons (compact)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)
        
        self.proc_start_btn = QPushButton("▶ Start")
        self.proc_start_btn.clicked.connect(self._start_processing)
        self.proc_start_btn.setMinimumHeight(35)
        self.proc_start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        controls_layout.addWidget(self.proc_start_btn)
        
        self.proc_pause_btn = QPushButton("⏸ Pause")
        self.proc_pause_btn.clicked.connect(self._pause_processing)
        self.proc_pause_btn.setEnabled(False)
        self.proc_pause_btn.setMinimumHeight(35)
        self.proc_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e68900; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        controls_layout.addWidget(self.proc_pause_btn)
        
        self.proc_stop_btn = QPushButton("⏹ Stop")
        self.proc_stop_btn.clicked.connect(self._stop_processing)
        self.proc_stop_btn.setEnabled(False)
        self.proc_stop_btn.setMinimumHeight(35)
        self.proc_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        controls_layout.addWidget(self.proc_stop_btn)
        
        self.proc_retry_btn = QPushButton("🔄 Retry")
        self.proc_retry_btn.clicked.connect(self._retry_failed)
        self.proc_retry_btn.setMinimumHeight(35)
        self.proc_retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        controls_layout.addWidget(self.proc_retry_btn)
        
        top_row.addLayout(controls_layout)
        bar_layout.addLayout(top_row)
        
        # Progress bar with detailed format (prominent)
        self.proc_progress = QProgressBar()
        self.proc_progress.setMinimum(1)  # Start from 1 instead of 0
        self.proc_progress.setFormat("%v / %m files (%p%) • Processing...")
        self.proc_progress.setMinimumHeight(36)  # Slightly taller
        self.proc_progress.setTextVisible(True)
        self.proc_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                background-color: rgba(0, 0, 0, 0.3);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #66BB6A, stop:1 #81C784);
                border-radius: 6px;
                margin: 1px;
            }
            QProgressBar::chunk:disabled {
                background: #666666;
            }
        """)
        
        # Progress animation timer for active processing
        self._progress_pulse_timer = QTimer()
        self._progress_pulse_timer.setInterval(800)
        self._progress_pulse_timer.timeout.connect(self._pulse_progress_bar)
        self._progress_pulse_effect = 0
        bar_layout.addWidget(self.proc_progress)
        
        # Processing speed and ETA row
        speed_row = QHBoxLayout()
        speed_row.setSpacing(16)
        
        # Current processing stage indicator
        self.proc_stage_label = QLabel("🔍 Stage: --")
        self.proc_stage_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 9pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        speed_row.addWidget(self.proc_stage_label)
        
        self.proc_elapsed_label = QLabel("⏳ Elapsed: --")
        self.proc_elapsed_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 9pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        speed_row.addWidget(self.proc_elapsed_label)
        
        self.proc_speed_label = QLabel("⚡ Speed: --")
        self.proc_speed_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 9pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        speed_row.addWidget(self.proc_speed_label)
        
        self.proc_eta_label = QLabel("⏱️ ETA: --")
        self.proc_eta_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 9pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        speed_row.addWidget(self.proc_eta_label)
        
        speed_row.addStretch()
        bar_layout.addLayout(speed_row)
        
        # Bottom row: Statistics
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        
        self.proc_processed_label = QLabel("✓ Processed: 0")
        self.proc_processed_label.setStyleSheet("""
            QLabel {
                color: #8BC34A;
                font-size: 10pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        stats_row.addWidget(self.proc_processed_label)
        
        self.proc_failed_label = QLabel("✗ Failed: 0")
        self.proc_failed_label.setStyleSheet("""
            QLabel {
                color: #f44336;
                font-size: 10pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        stats_row.addWidget(self.proc_failed_label)
        
        self.proc_skipped_label = QLabel("⊘ Skipped: 0")
        self.proc_skipped_label.setStyleSheet("""
            QLabel {
                color: #FF9800;
                font-size: 10pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        stats_row.addWidget(self.proc_skipped_label)
        
        stats_row.addStretch()
        bar_layout.addLayout(stats_row)
    
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
        # Set icon and styling based on type
        if notification_type == "success":
            icon = "✓"
            text_color = "#4CAF50"
        elif notification_type == "warning":
            icon = "⚠"
            text_color = "#FF9800"
        elif notification_type == "error":
            icon = "✕"
            text_color = "#F44336"
        else:  # info
            icon = "ℹ"
            text_color = "#2196F3"
        
        # Update status bar notification
        self.status_notification_icon.setText(icon)
        self.status_notification_message.setText(message)
        
        # Show close button if we're not auto-hiding
        self.status_notification_close.setVisible(auto_hide == 0)
        
        # Set colors for status bar notification
        self.notification_area.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-weight: bold;
            }}
        """)
        
        # Auto-hide if requested
        if auto_hide > 0:
            QTimer.singleShot(auto_hide, self._hide_notification)
    
    def _hide_notification(self):
        """Clear notification from status bar."""
        self.status_notification_icon.setText("")
        self.status_notification_message.setText("")
        self.notification_area.setStyleSheet("")
        self.status_notification_close.setVisible(False)  # Hide close button
    
    def _create_watch_tab(self) -> QWidget:
        """Create Watch tab for folder management."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Watched Folders")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Folder list
        self.folder_list = QListWidget()
        self.folder_list.setAlternatingRowColors(True)
        layout.addWidget(self.folder_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self._add_watch_folder)
        button_layout.addWidget(self.add_folder_btn)
        
        self.remove_folder_btn = QPushButton("Remove Folder")
        self.remove_folder_btn.clicked.connect(self._remove_watch_folder)
        self.remove_folder_btn.setEnabled(False)
        button_layout.addWidget(self.remove_folder_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setShortcut("F5")
        self.refresh_btn.clicked.connect(self._refresh_inventory)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Inventory stats
        stats_group = QGroupBox("Inventory Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_files_label = QLabel("Total Files: 0")
        stats_layout.addWidget(self.total_files_label)
        
        self.by_type_label = QLabel("By Type: -")
        stats_layout.addWidget(self.by_type_label)
        
        self.unanalyzed_label = QLabel("Unanalyzed: 0")
        self.unanalyzed_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        stats_layout.addWidget(self.unanalyzed_label)
        
        layout.addWidget(stats_group)
        
        # Load watched folders
        self._load_watched_folders()
        
        return tab
    
    def _create_queue_tab(self) -> QWidget:
        """Create Queue tab for processing queue management."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Processing Queue")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Queue table
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(["File", "Type", "Status", "Progress", "Priority"])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.queue_table.setColumnWidth(3, 120)  # Progress column fixed width
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.queue_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.enqueue_btn = QPushButton("Enqueue Selected Files")
        self.enqueue_btn.clicked.connect(self._enqueue_files)
        button_layout.addWidget(self.enqueue_btn)
        
        self.dequeue_btn = QPushButton("Remove Selected")
        self.dequeue_btn.clicked.connect(self._dequeue_files)
        self.dequeue_btn.setEnabled(False)
        button_layout.addWidget(self.dequeue_btn)
        
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.clicked.connect(self._move_queue_up)
        self.move_up_btn.setMaximumWidth(40)
        button_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.clicked.connect(self._move_queue_down)
        self.move_down_btn.setMaximumWidth(40)
        button_layout.addWidget(self.move_down_btn)
        
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        button_layout.addWidget(self.clear_queue_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Progress
        self.queue_progress = QProgressBar()
        self.queue_progress.setMinimum(1)  # Start from 1 instead of 0
        self.queue_progress.setValue(1)    # Initial value of 1
        self.queue_progress.setFormat("%v / %m items")
        layout.addWidget(self.queue_progress)
        
        return tab
    
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
        layout = QVBoxLayout(tab)
        
        # Header with search
        header_layout = QHBoxLayout()
        header_label = QLabel("Analyzed Files")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Clear all button
        clear_all_btn = QPushButton("🗑️ Clear All Results")
        clear_all_btn.clicked.connect(self._clear_all_results)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        header_layout.addWidget(clear_all_btn)
        
        # Refresh button
        refresh_results_btn = QPushButton("🔄 Refresh")
        refresh_results_btn.clicked.connect(self._refresh_results)
        header_layout.addWidget(refresh_results_btn)
        
        layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)
        
        self.results_search_input = QLineEdit()
        self.results_search_input.setPlaceholderText("Search descriptions and tags...")
        self.results_search_input.returnPressed.connect(self._search_results)
        search_layout.addWidget(self.results_search_input)
        
        self.search_results_btn = QPushButton("🔍 Search")
        self.search_results_btn.clicked.connect(self._search_results)
        search_layout.addWidget(self.search_results_btn)
        
        self.clear_search_btn = QPushButton("✕ Clear")
        self.clear_search_btn.clicked.connect(self._clear_search)
        search_layout.addWidget(self.clear_search_btn)
        
        layout.addLayout(search_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "File Name", "Type", "Tags", "Description", "Confidence", "Analyzed"
        ])
        
        # Configure table
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.verticalHeader().setVisible(False)
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # File Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)     # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Tags
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)   # Description
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)     # Confidence
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)     # Analyzed
        
        self.results_table.setColumnWidth(1, 80)   # Type
        self.results_table.setColumnWidth(2, 200)  # Tags
        self.results_table.setColumnWidth(4, 90)   # Confidence
        self.results_table.setColumnWidth(5, 150)  # Analyzed
        
        # Connect double-click to view details
        self.results_table.doubleClicked.connect(self._view_result_details)
        
        layout.addWidget(self.results_table)
        
        # Statistics footer
        footer_layout = QHBoxLayout()
        self.results_count_label = QLabel("Total files: 0")
        footer_layout.addWidget(self.results_count_label)
        footer_layout.addStretch()
        
        view_details_btn = QPushButton("View Details")
        view_details_btn.clicked.connect(self._view_selected_result)
        footer_layout.addWidget(view_details_btn)
        
        layout.addLayout(footer_layout)
        
        # Load initial results
        QTimer.singleShot(500, self._refresh_results)
        
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
        self.setStatusBar(status_bar)
        
        # Add notification area (left-most, stretches to fill available space)
        self.notification_area = QWidget()
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
        self.status_notification_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }
        """)
        self.status_notification_close.clicked.connect(self._hide_notification)
        self.status_notification_close.setVisible(False)  # Hide until needed
        notification_layout.addWidget(self.status_notification_close)
        
        status_bar.addWidget(self.notification_area, 1)  # Stretch to fill available space
        
        # Add permanent widgets (right side)
        status_bar.addPermanentWidget(QLabel("●"))
        
        # AI Model status button
        self.ai_status_btn = QPushButton("● AI Models")
        self.ai_status_btn.setFlat(True)
        self.ai_status_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 4px 12px;
                color: #888888;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(128, 128, 128, 0.2);
                border-radius: 3px;
            }
        """)
        self.ai_status_btn.clicked.connect(self._show_ai_model_dialog)
        status_bar.addPermanentWidget(self.ai_status_btn)
        
        self.inventory_status_label = QLabel("Files: 0")
        self.inventory_status_label.setStyleSheet("padding: 0 8px;")
        status_bar.addPermanentWidget(self.inventory_status_label)
        
        status_bar.addPermanentWidget(QLabel("●"))
        
        self.processing_status_bar_label = QLabel("Idle")
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
        # Cycle through animation frames (Braille spinner)
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._activity_frame = (self._activity_frame + 1) % len(frames)
        spinner = frames[self._activity_frame]
        
        # Update status with spinner based on current state
        current_text = self.proc_status_label.text()
        if "PAUSING" in current_text:
            self.proc_status_label.setText(f"{spinner} PAUSING...")
        elif "STOPPING" in current_text:
            self.proc_status_label.setText(f"{spinner} STOPPING...")
        else:
            # Normal RUNNING state
            self.proc_status_label.setText(f"{spinner} RUNNING")
    
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
        
        if status_ok:
            # Green dot
            self.ai_status_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 4px 12px;
                    color: #4CAF50;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(76, 175, 80, 0.2);
                    border-radius: 3px;
                }
            """)
            self.ai_status_btn.setToolTip("AI Models: Connected ✓\nClick to manage models")
        else:
            # Red dot
            self.ai_status_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 4px 12px;
                    color: #F44336;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(244, 67, 54, 0.2);
                    border-radius: 3px;
                }
            """)
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
            self.tabs.tabBar().setStyleSheet("")
    
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
        
        # Calculate color with intensity
        # From dim green (0, 80, 0) to bright green (0, 255, 0)
        green_value = int(80 + (175 * self._glow_intensity / 100))
        
        # Apply stylesheet with current intensity
        self.tabs.tabBar().setStyleSheet(f"""
            QTabBar::tab {{
                font-size: 11pt;
            }}
            QTabBar::tab:nth-child(2) {{
                color: rgb(0, {green_value}, 0);
                font-weight: bold;
            }}
        """)

    
    def _on_watcher_error(self, error_code, message):
        """Handle file watcher error."""
        logger.error(f"File watcher error: {error_code} - {message}")
        self.status_label.setText(f"Error: {message}")
    
    # Queue tab handlers
    def _refresh_queue_table(self):
        """Refresh queue table display."""
        self.queue_table.setRowCount(0)
        self._file_progress_bars.clear()  # Clear old progress bar references
        items = self.queue_manager.get_queue_items()
        
        for item in items:
            row = self.queue_table.rowCount()
            self.queue_table.insertRow(row)
            
            # File name
            file_name = Path(item.file_path).name
            self.queue_table.setItem(row, 0, QTableWidgetItem(file_name))
            
            # Type
            self.queue_table.setItem(row, 1, QTableWidgetItem(item.file_type or '-'))
            
            # Status
            self.queue_table.setItem(row, 2, QTableWidgetItem(item.status.value))
            
            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setMinimum(1)  # Start from 1 instead of 0
            progress_bar.setMaximum(100)
            progress_bar.setValue(1)    # Initial value of 1 instead of 0
            progress_bar.setTextVisible(True)
            progress_bar.setFormat("")  # Empty initially
            
            # Style based on status
            if item.status == QueueItemStatus.PROCESSING:
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #3498db;
                        border-radius: 3px;
                        text-align: center;
                        background-color: #ecf0f1;
                    }
                    QProgressBar::chunk {
                        background-color: #3498db;
                    }
                """)
                progress_bar.setFormat("Processing...")
            elif item.status == QueueItemStatus.COMPLETED:
                progress_bar.setValue(100)
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #27ae60;
                        border-radius: 3px;
                        text-align: center;
                        background-color: #ecf0f1;
                    }
                    QProgressBar::chunk {
                        background-color: #27ae60;
                    }
                """)
                progress_bar.setFormat("✓ Done")
            elif item.status == QueueItemStatus.FAILED:
                progress_bar.setValue(100)
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #e74c3c;
                        border-radius: 3px;
                        text-align: center;
                        background-color: #ecf0f1;
                    }
                    QProgressBar::chunk {
                        background-color: #e74c3c;
                    }
                """)
                progress_bar.setFormat("✗ Failed")
            else:
                # Pending/Skipped
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #95a5a6;
                        border-radius: 3px;
                        text-align: center;
                        background-color: #ecf0f1;
                    }
                    QProgressBar::chunk {
                        background-color: #95a5a6;
                    }
                """)
                progress_bar.setFormat("—")
            
            self.queue_table.setCellWidget(row, 3, progress_bar)
            self._file_progress_bars[item.file_path] = progress_bar
            
            # Priority
            self.queue_table.setItem(row, 4, QTableWidgetItem(str(item.priority)))
        
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
            count = self.queue_manager.add_batch(files)
            if count < len(files):
                skipped = len(files) - count
                self.show_status_message(f"Enqueued {count} files, skipped {skipped} unsupported files")
                
                # Show info about supported file types if files were skipped
                if skipped > 0:
                    QTimer.singleShot(500, self._show_supported_file_types_info)
            else:
                self.show_status_message(f"Enqueued {count} files")
            
            logger.info(f"Enqueued {count}/{len(files)} files")
            self._refresh_queue_table()
            self._update_queue_badge()
            self._refresh_queue_table()
            self._update_queue_badge()
    
    def _dequeue_files(self):
        """Remove selected files from queue."""
        selected_rows = set(item.row() for item in self.queue_table.selectedItems())
        
        for row in sorted(selected_rows, reverse=True):
            file_item = self.queue_table.item(row, 0)
            if file_item:
                # Find full path (simplified - would need proper mapping)
                items = self.queue_manager.get_queue_items()
                if row < len(items):
                    self.queue_manager.remove_item(items[row].file_path)
        
        self._refresh_queue_table()
        self._update_queue_badge()
    
    def _move_queue_up(self):
        """Move selected queue item up."""
        current_row = self.queue_table.currentRow()
        if current_row > 0:
            items = self.queue_manager.get_queue_items()
            if current_row < len(items):
                self.queue_manager.move_up(items[current_row].file_path)
                self._refresh_queue_table()
                self.queue_table.selectRow(current_row - 1)
    
    def _move_queue_down(self):
        """Move selected queue item down."""
        current_row = self.queue_table.currentRow()
        items = self.queue_manager.get_queue_items()
        if current_row >= 0 and current_row < len(items) - 1:
            self.queue_manager.move_down(items[current_row].file_path)
            self._refresh_queue_table()
            self.queue_table.selectRow(current_row + 1)
    
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
        has_selection = bool(self.queue_table.selectedItems())
        self.dequeue_btn.setEnabled(has_selection)
    
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
        """Start or resume processing the queue."""
        if not self.orchestrator:
            self._show_notification(
                "Processing not available. Please check OCR and LLM configuration in Settings.",
                "warning",
                auto_hide=6000
            )
            return
        
        # Check if we're resuming from paused state (Processing tab button)
        if self.proc_start_btn.text() == "▶ Resume":
            # Emit signal to trigger resume_processing on worker thread
            logger.info("Emitting resume_processing_signal...")
            self.resume_processing_signal.emit()
        else:
            # Emit signal to trigger start_processing on worker thread
            logger.info("Emitting start_processing_signal...")
            self.start_processing_signal.emit()
    
    def _pause_processing(self):
        """Pause processing."""
        if self.orchestrator:
            # Emit signal to trigger pause_processing on worker thread
            # The orchestrator will emit state_changed signal which updates UI
            self.pause_processing_signal.emit()
            logger.info("Processing pause requested")
    
    def _stop_processing(self):
        """Stop processing."""
        if self.orchestrator:
            # Update UI immediately to show stop is pending with spinner
            self.proc_status_label.setText("⠋ STOPPING...")
            self.proc_status_label.setStyleSheet("""
                QLabel {
                    color: #F44336;
                    font-size: 18pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            self.processing_status_bar_label.setText("Stopping...")
            
            # Update buttons
            self.proc_start_btn.setEnabled(False)
            self.proc_pause_btn.setEnabled(False)
            self.proc_stop_btn.setEnabled(False)
            self.proc_retry_btn.setEnabled(False)  # Disable retry during stopping
            
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
            # Just double-check that we're actually in RUNNING state
            if self.orchestrator.state != ProcessingState.RUNNING:
                logger.warning(f"Expected RUNNING state but got {self.orchestrator.state}, fixing...")
                # Force state to RUNNING
                self.orchestrator.state = ProcessingState.RUNNING
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
        """Handle processing paused signal."""
        # This is now just a backup handler - state change should handle it
        logger.debug("_on_processing_paused called - delegating to state handler")
        if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'state'):
            # Just double-check that we're actually in PAUSED state
            if self.orchestrator.state != ProcessingState.PAUSED:
                logger.warning(f"Expected PAUSED state but got {self.orchestrator.state}, fixing...")
                # Force state to PAUSED
                self.orchestrator.state = ProcessingState.PAUSED
                self._on_processing_state_changed(ProcessingState.PAUSED)
        else:
            logger.warning("Orchestrator not available for state check")
    
    def _on_processing_stopped(self):
        """Handle processing stopped signal."""
        # This is now just a backup handler - state change should handle it
        logger.debug("_on_processing_stopped called - delegating to state handler")
        if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'state'):
            # Just double-check that we're actually in STOPPED state
            if self.orchestrator.state != ProcessingState.STOPPED:
                logger.warning(f"Expected STOPPED state but got {self.orchestrator.state}, fixing...")
                # Force state to STOPPED
                self.orchestrator.state = ProcessingState.STOPPED
                self._on_processing_state_changed(ProcessingState.STOPPED)
        else:
            logger.warning("Orchestrator not available for state check")
        
        logger.info("UI updated: processing stopped")
    
    def _on_processing_completed(self):
        """Handle processing completed signal."""
        # Stop activity animation
        self._activity_timer.stop()
        
        self.proc_status_label.setText("⚙️ COMPLETED")
        self.proc_status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 18pt;
                font-weight: bold;
                background: transparent;
            }
        """)
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
            progress_bar.setValue(10)  # Show some initial progress
            progress_bar.setFormat("Starting...")
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #ecf0f1;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                }
            """)
        
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
            progress_bar.setFormat("✓ Done")
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #27ae60;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #ecf0f1;
                }
                QProgressBar::chunk {
                    background-color: #27ae60;
                }
            """)
        
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
                            cell_item.setBackground(QColor(240, 255, 240))
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
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #e74c3c;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #ecf0f1;
                }
                QProgressBar::chunk {
                    background-color: #e74c3c;
                }
            """)
        
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
        
        if state == ProcessingState.IDLE:
            self.proc_status_label.setText("⚙️ IDLE")
            self.proc_status_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 18pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)
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
            
            # Update status with yellow color
            self.proc_status_label.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    font-size: 18pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            self.processing_status_bar_label.setText("Pausing...")
        elif state == ProcessingState.PAUSED:
            # Stop activity animation
            self._activity_timer.stop()
            
            # Set status text directly (don't rely on spinner animation)
            self.proc_status_label.setText("⚙️ PAUSED")
            self.proc_status_label.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    font-size: 18pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            self.processing_status_bar_label.setText("Paused")
            
            # Save the time when processing was paused and record elapsed time
            from datetime import datetime
            self._pause_time = datetime.now()
            if self._processing_start_time:
                self._paused_elapsed_seconds = (self._pause_time - self._processing_start_time).total_seconds()
            
            # Update buttons
            self.proc_start_btn.setEnabled(True)
            self.proc_start_btn.setText("▶ Resume")
            self.proc_pause_btn.setEnabled(False)
            self.proc_stop_btn.setEnabled(True)
            self.proc_retry_btn.setEnabled(False)  # Disable retry during paused state
        elif state == ProcessingState.STOPPING:
            # Start spinner animation for STOPPING state
            if not self._activity_timer.isActive():
                self._activity_timer.start(80)
            
            # Update status with red color
            self.proc_status_label.setStyleSheet("""
                QLabel {
                    color: #F44336;
                    font-size: 18pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            self.processing_status_bar_label.setText("Stopping...")
            
            # Update buttons
            self.proc_start_btn.setEnabled(False)
            self.proc_pause_btn.setEnabled(False)
            self.proc_stop_btn.setEnabled(False)
            self.proc_retry_btn.setEnabled(False)  # Disable retry during stopping
        elif state == ProcessingState.STOPPED:
            # Stop activity animation
            self._activity_timer.stop()
            
            # Set status text directly (don't rely on spinner animation)
            self.proc_status_label.setText("⚙️ STOPPED")
            self.proc_status_label.setStyleSheet("""
                QLabel {
                    color: #F44336;
                    font-size: 18pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            self.processing_status_bar_label.setText("Stopped")
            
            # Update buttons
            self.proc_start_btn.setEnabled(True)
            self.proc_start_btn.setText("▶ Start")
            self.proc_pause_btn.setEnabled(False)
            self.proc_stop_btn.setEnabled(False)
            
            # Enable retry button if there are failed items
            if self.orchestrator and self.orchestrator.failed_count > 0:
                self.proc_retry_btn.setEnabled(True)
            else:
                self.proc_retry_btn.setEnabled(False)
        elif state == ProcessingState.RUNNING:
            # Start spinner animation for RUNNING state if not already active
            if not self._activity_timer.isActive():
                self._activity_timer.start(80)
            
            # Start progress bar pulse animation
            if not self._progress_pulse_timer.isActive():
                self._progress_pulse_timer.start()
                
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
            
            # Update status with green color
            self.proc_status_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-size: 18pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            self.processing_status_bar_label.setText("Processing...")
            
            # Update buttons - enable pause during processing
            self.proc_start_btn.setEnabled(False)
            self.proc_pause_btn.setEnabled(True)  # Enable pause button in RUNNING state
            self.proc_stop_btn.setEnabled(True)
            self.proc_retry_btn.setEnabled(False)  # Disable retry during processing
    
    def _reset_processing_ui(self):
        """Reset processing UI to initial state."""
        self.proc_start_btn.setEnabled(True)
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
            
    def _export_to_csv(self, filepath):
        """Export results to CSV format."""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['File', 'Path', 'Tags', 'Description', 'Processed Date'])
            
            # Write data from database
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Join tables to get complete data
                cursor.execute("""
                    SELECT 
                        f.file_path,
                        GROUP_CONCAT(c.tag_text, '; ') as tags,
                        d.description_text,
                        f.processed_date
                    FROM files f
                    LEFT JOIN classifications c ON f.file_id = c.file_id
                    LEFT JOIN descriptions d ON f.file_id = d.file_id
                    WHERE f.processed_date IS NOT NULL
                    GROUP BY f.file_id
                    ORDER BY f.processed_date DESC
                """)
                
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
            
    def _export_to_json(self, filepath):
        """Export results to JSON format."""
        import json
        
        results = []
        
        # Get data from database
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all processed files
            cursor.execute("""
                SELECT file_id, file_path, file_hash, processed_date
                FROM files
                WHERE processed_date IS NOT NULL
                ORDER BY processed_date DESC
            """)
            
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
        
        # Change the gradient colors slightly based on the pulse effect
        if self._progress_pulse_effect == 0:
            chunk_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #66BB6A, stop:1 #81C784);
            """
        elif self._progress_pulse_effect == 1:
            chunk_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #66BB6A, stop:0.5 #81C784, stop:1 #4CAF50);
            """
        elif self._progress_pulse_effect == 2:
            chunk_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #81C784, stop:0.5 #4CAF50, stop:1 #66BB6A);
            """
        else:
            chunk_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.3 #81C784, stop:0.7 #66BB6A, stop:1 #4CAF50);
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
            self.results_count_label.setText(f"Total files: {len(files)}")
            
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
            self.results_count_label.setText(f"Search results: {len(file_results)}")
            
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
        
        # Set dialog stylesheet
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-radius: 8px;
            }
        """)
        
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
        title_label.setStyleSheet("color: white; background: transparent; padding-left: 10px;")
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
        message.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 11pt;
                background: transparent;
                padding: 10px;
                line-height: 1.5;
            }
        """)
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
            count_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 12pt;
                    font-weight: bold;
                   
                    background: rgba(231, 76, 60, 0.1);
                    padding: 12px;
                    border-radius: 6px;
                    border: 2px solid #e74c3c;
                }
            """)
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(count_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:pressed {
                background-color: #6c7a7b;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete All")
        delete_btn.setMinimumHeight(40)
        delete_btn.setMinimumWidth(140)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
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