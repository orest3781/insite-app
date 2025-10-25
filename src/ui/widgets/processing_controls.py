"""
Enhanced Processing Controls Widget
Modern redesign of start, pause, and stop buttons following UI best practices.
"""
from enum import Enum
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, 
    QFrame, QMessageBox, QProgressBar, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QPalette, QIcon, QKeySequence, QShortcut


class ProcessingState(Enum):
    """Enhanced processing state enum with better state management."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class AnimatedButton(QPushButton):
    """Enhanced button with smooth animations and better visual feedback."""
    
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._setup_animations()
        
    def _setup_animations(self):
        """Setup button animations."""
        self._opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self._opacity_effect)
        
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(200)
        self._fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        
    def fade_in(self):
        """Fade in animation."""
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.start()
        
    def fade_out(self):
        """Fade out animation."""
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.3)
        self._fade_animation.start()


class ProcessingControlsWidget(QWidget):
    """
    Modern processing controls widget with enhanced UX.
    
    Features:
    - State-aware button visibility
    - Smooth transitions and animations
    - Better visual hierarchy
    - Accessibility improvements
    - Confirmation dialogs for destructive actions
    """
    
    # Signals
    start_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    retry_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_state = ProcessingState.IDLE
        self._confirmation_enabled = True
        self._progress_info = {'current': 0, 'total': 0, 'failed': 0}
        self._sound_enabled = False  # Disabled by default
        
        # Animation timers
        self._state_transition_timer = QTimer()
        self._state_transition_timer.setSingleShot(True)
        self._state_transition_timer.timeout.connect(self._complete_state_transition)
        
        self._setup_ui()
        self._setup_styles()
        self._setup_keyboard_shortcuts()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the enhanced UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create control group container
        self._control_group = QFrame()
        self._control_group.setObjectName("processing_control_group")
        control_layout = QHBoxLayout(self._control_group)
        control_layout.setContentsMargins(8, 8, 8, 8)
        control_layout.setSpacing(12)
        
        # Primary action button (Start/Resume)
        self._primary_btn = AnimatedButton()
        self._primary_btn.setObjectName("primary_action_btn")
        self._primary_btn.setMinimumSize(120, 48)
        self._primary_btn.clicked.connect(self._handle_primary_action)
        control_layout.addWidget(self._primary_btn)
        
        # Secondary controls container
        self._secondary_container = QWidget()
        secondary_layout = QHBoxLayout(self._secondary_container)
        secondary_layout.setContentsMargins(0, 0, 0, 0)
        secondary_layout.setSpacing(8)
        
        # Pause button
        self._pause_btn = AnimatedButton()
        self._pause_btn.setObjectName("pause_action_btn")
        self._pause_btn.setMinimumSize(100, 48)
        self._pause_btn.clicked.connect(self._handle_pause_action)
        secondary_layout.addWidget(self._pause_btn)
        
        # Stop button
        self._stop_btn = AnimatedButton()
        self._stop_btn.setObjectName("stop_action_btn")
        self._stop_btn.setMinimumSize(100, 48)
        self._stop_btn.clicked.connect(self._handle_stop_action)
        secondary_layout.addWidget(self._stop_btn)
        
        control_layout.addWidget(self._secondary_container)
        
        # Retry button (separate from main controls)
        self._retry_btn = AnimatedButton()
        self._retry_btn.setObjectName("retry_action_btn")
        self._retry_btn.setMinimumSize(100, 48)
        self._retry_btn.clicked.connect(self._handle_retry_action)
        self._retry_btn.setVisible(False)
        control_layout.addWidget(self._retry_btn)
        
        control_layout.addStretch()
        layout.addWidget(self._control_group)
        
        # State indicator (subtle, modern)
        self._state_indicator = QLabel()
        self._state_indicator.setObjectName("state_indicator")
        self._state_indicator.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._state_indicator)
        
        # Initialize button states
        self._update_ui_for_state(ProcessingState.IDLE)
        
    def _setup_styles(self):
        """Setup modern button styles."""
        # Get app palette (assuming it's available from parent)
        colors = self._get_app_colors()
        
        self.setStyleSheet(f"""
            QFrame#processing_control_group {{
                background-color: {colors.get('surface', '#2b2b2b')};
                border: 1px solid {colors.get('dividers', '#404040')};
                border-radius: 12px;
                padding: 4px;
            }}
            
            QPushButton#primary_action_btn {{
                background-color: {colors.get('accent', '#4CAF50')};
                color: {colors.get('text_primary', '#ffffff')};
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                padding: 12px 24px;
            }}
            
            QPushButton#primary_action_btn:hover {{
                background-color: {colors.get('selected_hover', '#45a049')};
            }}
            
            QPushButton#primary_action_btn:pressed {{
                background-color: {colors.get('selected', '#3d8b40')};
            }}
            
            QPushButton#primary_action_btn:disabled {{
                background-color: {colors.get('surface', '#404040')};
                color: {colors.get('text_disabled', '#888888')};
            }}
            
            QPushButton#pause_action_btn {{
                background-color: {colors.get('alert_warning', '#FF9800')};
                color: {colors.get('text_primary', '#ffffff')};
                border: none;
                border-radius: 8px;
                font-weight: 500;
                font-size: 13px;
                padding: 12px 20px;
            }}
            
            QPushButton#pause_action_btn:hover {{
                background-color: #fb8f1a;
            }}
            
            QPushButton#pause_action_btn:pressed {{
                background-color: #d06d0e;
            }}
            
            QPushButton#stop_action_btn {{
                background-color: {colors.get('alert_error', '#F44336')};
                color: {colors.get('text_primary', '#ffffff')};
                border: none;
                border-radius: 8px;
                font-weight: 500;
                font-size: 13px;
                padding: 12px 20px;
            }}
            
            QPushButton#stop_action_btn:hover {{
                background-color: #f05454;
            }}
            
            QPushButton#stop_action_btn:pressed {{
                background-color: #d83b3b;
            }}
            
            QPushButton#retry_action_btn {{
                background-color: {colors.get('surface_alt', '#353535')};
                color: {colors.get('text_primary', '#ffffff')};
                border: 1px solid {colors.get('dividers', '#555555')};
                border-radius: 8px;
                font-weight: 500;
                font-size: 13px;
                padding: 12px 20px;
            }}
            
            QPushButton#retry_action_btn:hover {{
                background-color: {colors.get('hover', '#404040')};
                border-color: {colors.get('accent', '#4CAF50')};
            }}
            
            QLabel#state_indicator {{
                color: {colors.get('text_secondary', '#aaaaaa')};
                font-size: 11px;
                font-weight: 500;
                padding: 4px 0px;
            }}
        """)
        
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for processing controls."""
        # Space or F5 for Start/Resume
        self._start_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self._start_shortcut.activated.connect(self._handle_primary_action)
        
        self._f5_shortcut = QShortcut(QKeySequence(Qt.Key_F5), self)
        self._f5_shortcut.activated.connect(self._handle_primary_action)
        
        # Escape for Pause/Stop
        self._escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._escape_shortcut.activated.connect(self._handle_escape_key)
        
        # Ctrl+Shift+S for Stop with confirmation
        self._stop_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self._stop_shortcut.activated.connect(self._handle_stop_action)
        
        # F6 for Retry
        self._retry_shortcut = QShortcut(QKeySequence(Qt.Key_F6), self)
        self._retry_shortcut.activated.connect(self._handle_retry_action)
        
    def _handle_escape_key(self):
        """Handle escape key press - pause if running, stop if paused."""
        if self._current_state == ProcessingState.RUNNING:
            self._handle_pause_action()
        elif self._current_state == ProcessingState.PAUSED:
            self._handle_stop_action()
        
    def _get_app_colors(self) -> Dict[str, str]:
        """Get application color palette."""
        # Try to get colors from parent main window
        parent = self.parent()
        while parent:
            if hasattr(parent, 'APP_PALETTE'):
                return parent.APP_PALETTE
            parent = parent.parent()
            
        # Fallback dark theme colors
        return {
            'surface': '#2b2b2b',
            'surface_alt': '#353535',
            'accent': '#4CAF50',
            'alert_warning': '#FF9800',
            'alert_error': '#F44336',
            'alert_success': '#4CAF50',
            'text_primary': '#ffffff',
            'text_secondary': '#aaaaaa',
            'text_disabled': '#888888',
            'dividers': '#404040',
            'hover': '#404040',
            'selected': '#3d8b40',
            'selected_hover': '#45a049',
        }
        
    def _connect_signals(self):
        """Connect internal signals."""
        pass
        
    def _handle_primary_action(self):
        """Handle primary action (Start/Resume)."""
        if self._current_state in [ProcessingState.IDLE, ProcessingState.STOPPED]:
            self._play_sound('start')
            self.start_requested.emit()
        elif self._current_state == ProcessingState.PAUSED:
            self._play_sound('start')
            self.start_requested.emit()  # Resume
            
    def _play_sound(self, sound_type: str):
        """Play sound feedback if enabled."""
        if not self._sound_enabled:
            return
            
        try:
            if sound_type == 'start' and hasattr(self, '_sound_start'):
                # Use system beep or similar
                pass  # QSoundEffect requires sound files
        except:
            pass  # Ignore sound errors
            
    def _handle_pause_action(self):
        """Handle pause action."""
        if self._current_state == ProcessingState.RUNNING:
            self.pause_requested.emit()
            
    def _handle_stop_action(self):
        """Handle stop action with context-aware confirmation."""
        if self._current_state in [ProcessingState.RUNNING, ProcessingState.PAUSED]:
            if self._confirmation_enabled:
                # Create context-aware dialog
                dialog = QMessageBox(self)
                dialog.setWindowTitle("Confirm Stop Processing")
                dialog.setIcon(QMessageBox.Question)
                
                # Context-aware message
                if self._current_state == ProcessingState.RUNNING:
                    message = ("Are you sure you want to stop processing?\n\n"
                             "• Current progress will be lost\n"
                             "• Files being processed will be reset to pending\n"
                             "• You can resume processing later from the beginning")
                else:  # PAUSED
                    message = ("Are you sure you want to stop processing?\n\n"
                             "• Processing is currently paused\n"
                             "• All progress will be lost\n"
                             "• Files will return to pending status")
                
                dialog.setText(message)
                dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                dialog.setDefaultButton(QMessageBox.No)
                
                # Add custom button text
                dialog.button(QMessageBox.Yes).setText("Stop Processing")
                dialog.button(QMessageBox.No).setText("Continue")
                
                if dialog.exec() != QMessageBox.Yes:
                    return
                    
            self.stop_requested.emit()
            
    def _handle_retry_action(self):
        """Handle retry action."""
        self.retry_requested.emit()
        
    def set_state(self, state: ProcessingState, animated: bool = True):
        """
        Set the current processing state with optional animation.
        
        Args:
            state: New processing state
            animated: Whether to animate the transition
        """
        if state == self._current_state:
            return
            
        old_state = self._current_state
        self._current_state = state
        
        if animated:
            # Start transition animation
            self._start_state_transition(old_state, state)
        else:
            self._update_ui_for_state(state)
            
    def _start_state_transition(self, from_state: ProcessingState, to_state: ProcessingState):
        """Start animated state transition."""
        # Fade out current buttons
        for btn in [self._primary_btn, self._pause_btn, self._stop_btn, self._retry_btn]:
            if btn.isVisible():
                btn.fade_out()
                
        # Start timer to complete transition
        self._state_transition_timer.start(250)
        
    def _complete_state_transition(self):
        """Complete the state transition."""
        self._update_ui_for_state(self._current_state)
        
        # Fade in new buttons
        for btn in [self._primary_btn, self._pause_btn, self._stop_btn, self._retry_btn]:
            if btn.isVisible():
                btn.fade_in()
                
    def _update_ui_for_state(self, state: ProcessingState):
        """Update UI elements for the given state."""
        # Button configurations for each state
        configs = {
            ProcessingState.IDLE: {
                'primary': {'text': '▶️ Start Processing', 'visible': True, 'enabled': True},
                'pause': {'visible': False},
                'stop': {'visible': False},
                'retry': {'visible': False},
                'indicator': 'Ready to start processing'
            },
            ProcessingState.STARTING: {
                'primary': {'text': '⚙️ Starting...', 'visible': True, 'enabled': False},
                'pause': {'visible': False},
                'stop': {'visible': False},
                'retry': {'visible': False},
                'indicator': 'Initializing processing engine...'
            },
            ProcessingState.RUNNING: {
                'primary': {'visible': False},
                'pause': {'text': '⏸️ Pause', 'visible': True, 'enabled': True},
                'stop': {'text': '⏹️ Stop', 'visible': True, 'enabled': True},
                'retry': {'visible': False},
                'indicator': 'Processing files... Press ESC to pause'
            },
            ProcessingState.PAUSING: {
                'primary': {'visible': False},
                'pause': {'text': '⚙️ Pausing...', 'visible': True, 'enabled': False},
                'stop': {'text': '⏹️ Stop', 'visible': True, 'enabled': True},
                'retry': {'visible': False},
                'indicator': 'Pausing processing... Please wait'
            },
            ProcessingState.PAUSED: {
                'primary': {'text': '▶️ Resume Processing', 'visible': True, 'enabled': True},
                'pause': {'visible': False},
                'stop': {'text': '⏹️ Stop', 'visible': True, 'enabled': True},
                'retry': {'visible': False},
                'indicator': 'Processing paused • Press Space to resume'
            },
            ProcessingState.STOPPING: {
                'primary': {'visible': False},
                'pause': {'visible': False},
                'stop': {'text': '⚙️ Stopping...', 'visible': True, 'enabled': False},
                'retry': {'visible': False},
                'indicator': 'Stopping processing... Cleaning up resources'
            },
            ProcessingState.STOPPED: {
                'primary': {'text': '▶️ Start Processing', 'visible': True, 'enabled': True},
                'pause': {'visible': False},
                'stop': {'visible': False},
                'retry': {'visible': False},
                'indicator': 'Processing stopped • Ready to start new session'
            },
            ProcessingState.ERROR: {
                'primary': {'text': '🔄 Try Again', 'visible': True, 'enabled': True},
                'pause': {'visible': False},
                'stop': {'visible': False},
                'retry': {'text': '� Retry Failed Items', 'visible': True, 'enabled': True},
                'indicator': 'Error occurred • Check logs and retry'
            },
        }
        
        config = configs.get(state, configs[ProcessingState.IDLE])
        
        # Update buttons
        self._update_button(self._primary_btn, config.get('primary', {}))
        self._update_button(self._pause_btn, config.get('pause', {}))
        self._update_button(self._stop_btn, config.get('stop', {}))
        self._update_button(self._retry_btn, config.get('retry', {}))
        
        # Update tooltips based on state
        self._update_tooltips(state)
        
        # Update state indicator
        self._state_indicator.setText(config.get('indicator', ''))
        
    def _update_tooltips(self, state: ProcessingState):
        """Update button tooltips based on current state."""
        tooltips = {
            ProcessingState.IDLE: {
                'primary': 'Start processing files (Space, F5)',
                'retry': 'Retry failed items (F6)',
            },
            ProcessingState.RUNNING: {
                'pause': 'Pause processing (Esc)',
                'stop': 'Stop processing and reset (Ctrl+Shift+S)',
            },
            ProcessingState.PAUSED: {
                'primary': 'Resume processing from where it was paused (Space, F5)',
                'stop': 'Stop processing and reset all progress (Ctrl+Shift+S)',
            },
            ProcessingState.STOPPED: {
                'primary': 'Start a new processing session (Space, F5)',
            },
            ProcessingState.ERROR: {
                'primary': 'Try processing again (Space, F5)',
                'retry': 'Retry only the failed items (F6)',
            },
        }
        
        state_tooltips = tooltips.get(state, {})
        
        # Apply tooltips
        self._primary_btn.setToolTip(state_tooltips.get('primary', ''))
        self._pause_btn.setToolTip(state_tooltips.get('pause', ''))
        self._stop_btn.setToolTip(state_tooltips.get('stop', ''))
        self._retry_btn.setToolTip(state_tooltips.get('retry', ''))
        
    def _update_button(self, button: QPushButton, config: Dict[str, Any]):
        """Update a button based on configuration."""
        button.setVisible(config.get('visible', False))
        button.setEnabled(config.get('enabled', True))
        if 'text' in config:
            button.setText(config['text'])
            
    def set_confirmation_enabled(self, enabled: bool):
        """Enable/disable confirmation dialogs for destructive actions."""
        self._confirmation_enabled = enabled
        
    def get_current_state(self) -> ProcessingState:
        """Get the current processing state."""
        return self._current_state
        
    def show_retry_button(self, show: bool = True):
        """Show or hide the retry button."""
        self._retry_btn.setVisible(show)
        
    def update_progress_info(self, current: int, total: int, failed: int = 0):
        """Update progress information for enhanced state messages."""
        self._progress_info = {'current': current, 'total': total, 'failed': failed}
        self._update_state_indicator()
        
    def _update_state_indicator(self):
        """Update state indicator with progress information."""
        base_message = self._get_base_indicator_message()
        
        if self._current_state in [ProcessingState.RUNNING, ProcessingState.PAUSED]:
            current = self._progress_info['current']
            total = self._progress_info['total']
            failed = self._progress_info['failed']
            
            if total > 0:
                percentage = int((current / total) * 100)
                progress_text = f" • {current}/{total} files ({percentage}%)"
                if failed > 0:
                    progress_text += f" • {failed} failed"
                base_message += progress_text
                
        self._state_indicator.setText(base_message)
        
    def _get_base_indicator_message(self) -> str:
        """Get the base indicator message for current state."""
        messages = {
            ProcessingState.IDLE: 'Ready to start processing',
            ProcessingState.STARTING: 'Initializing processing engine...',
            ProcessingState.RUNNING: 'Processing files... Press ESC to pause',
            ProcessingState.PAUSING: 'Pausing processing... Please wait',
            ProcessingState.PAUSED: 'Processing paused • Press Space to resume',
            ProcessingState.STOPPING: 'Stopping processing... Cleaning up resources',
            ProcessingState.STOPPED: 'Processing stopped • Ready to start new session',
            ProcessingState.ERROR: 'Error occurred • Check logs and retry',
        }
        return messages.get(self._current_state, '')