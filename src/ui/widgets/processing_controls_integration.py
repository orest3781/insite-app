"""
Processing Controls Integration
Helper module to integrate the new ProcessingControlsWidget with existing main window.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QMetaObject, Qt, Q_ARG
from .processing_controls import ProcessingControlsWidget, ProcessingState


class ProcessingControlsIntegration:
    """
    Integration helper for migrating from old button system to new ProcessingControlsWidget.
    
    This class helps maintain backward compatibility while introducing the new controls.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.controls_widget: Optional[ProcessingControlsWidget] = None
        self._old_buttons_hidden = False
        
    def install_new_controls(self, parent_widget: QWidget) -> ProcessingControlsWidget:
        """
        Install the new processing controls widget.
        
        Args:
            parent_widget: Widget to add the controls to
            
        Returns:
            The new ProcessingControlsWidget instance
        """
        # Create new controls widget
        self.controls_widget = ProcessingControlsWidget(parent_widget)
        
        # Connect signals to existing handlers
        self._connect_signals()
        
        return self.controls_widget
        
    def _connect_signals(self):
        """Connect new widget signals to existing main window handlers."""
        if not self.controls_widget:
            return
            
        # Connect to existing processing handlers
        self.controls_widget.start_requested.connect(self.main_window._start_processing)
        self.controls_widget.pause_requested.connect(self.main_window._pause_processing)
        self.controls_widget.stop_requested.connect(self.main_window._stop_processing)
        self.controls_widget.retry_requested.connect(self.main_window._retry_failed)
        
    def setup_connections(self):
        """Public method to setup signal connections - for backward compatibility."""
        self._connect_signals()
        
    def sync_state(self):
        """Public method to sync state - for backward compatibility."""
        self._sync_state()
        
    def hide_old_buttons(self):
        """Hide the old button implementation."""
        if hasattr(self.main_window, 'proc_start_btn'):
            self.main_window.proc_start_btn.setVisible(False)
        if hasattr(self.main_window, 'proc_pause_btn'):
            self.main_window.proc_pause_btn.setVisible(False)
        if hasattr(self.main_window, 'proc_stop_btn'):
            self.main_window.proc_stop_btn.setVisible(False)
        if hasattr(self.main_window, 'proc_retry_btn'):
            self.main_window.proc_retry_btn.setVisible(False)
            
        self._old_buttons_hidden = True
        
    def show_old_buttons(self):
        """Show the old button implementation (for rollback)."""
        if hasattr(self.main_window, 'proc_start_btn'):
            self.main_window.proc_start_btn.setVisible(True)
        if hasattr(self.main_window, 'proc_pause_btn'):
            self.main_window.proc_pause_btn.setVisible(True)
        if hasattr(self.main_window, 'proc_stop_btn'):
            self.main_window.proc_stop_btn.setVisible(True)
        if hasattr(self.main_window, 'proc_retry_btn'):
            self.main_window.proc_retry_btn.setVisible(True)
            
        self._old_buttons_hidden = False
        
    def sync_state_with_orchestrator(self):
        """Sync the new controls state with the existing orchestrator state."""
        if not self.controls_widget or not hasattr(self.main_window, 'orchestrator'):
            return
            
        # Map orchestrator states to new ProcessingState enum
        orchestrator = self.main_window.orchestrator
        if not orchestrator:
            return
            
        # Import the orchestrator's ProcessingState if available
        try:
            from src.services.processing_orchestrator import ProcessingState as OrchestratorState
            
            state_mapping = {
                OrchestratorState.IDLE: ProcessingState.IDLE,
                OrchestratorState.RUNNING: ProcessingState.RUNNING,
                OrchestratorState.PAUSING: ProcessingState.PAUSING,
                OrchestratorState.PAUSED: ProcessingState.PAUSED,
                OrchestratorState.STOPPING: ProcessingState.STOPPING,
                OrchestratorState.STOPPED: ProcessingState.STOPPED,
            }
            
            orchestrator_state = orchestrator.state
            new_state = state_mapping.get(orchestrator_state, ProcessingState.IDLE)
            self.controls_widget.set_state(new_state, animated=True)
            
        except ImportError:
            # Fallback to IDLE if orchestrator state can't be imported
            self.controls_widget.set_state(ProcessingState.IDLE)
            
    def handle_state_change(self, orchestrator_state):
        """
        Handle state change from orchestrator.
        
        Args:
            orchestrator_state: State from the processing orchestrator
        """
        if not self.controls_widget:
            return
            
        # Ensure this runs on the main thread to avoid timer issues
        QMetaObject.invokeMethod(
            self,
            "_handle_state_change_on_main_thread",
            Qt.QueuedConnection,
            Q_ARG("QVariant", orchestrator_state)
        )
    
    def _handle_state_change_on_main_thread(self, orchestrator_state):
        """Handle state change on main thread (private method)."""
        if not self.controls_widget:
            return
            
        # Map orchestrator states to new ProcessingState enum
        try:
            from src.services.processing_orchestrator import ProcessingState as OrchestratorState
            
            state_mapping = {
                OrchestratorState.IDLE: ProcessingState.IDLE,
                OrchestratorState.RUNNING: ProcessingState.RUNNING,
                OrchestratorState.PAUSING: ProcessingState.PAUSING,
                OrchestratorState.PAUSED: ProcessingState.PAUSED,
                OrchestratorState.STOPPING: ProcessingState.STOPPING,
                OrchestratorState.STOPPED: ProcessingState.STOPPED,
            }
            
            new_state = state_mapping.get(orchestrator_state, ProcessingState.IDLE)
            self.controls_widget.set_state(new_state, animated=True)
            
        except (ImportError, AttributeError):
            # Handle case where orchestrator states don't match
            # Convert string states to enum
            state_str = str(orchestrator_state).lower()
            if 'idle' in state_str:
                self.controls_widget.set_state(ProcessingState.IDLE)
            elif 'running' in state_str:
                self.controls_widget.set_state(ProcessingState.RUNNING)
            elif 'pausing' in state_str:
                self.controls_widget.set_state(ProcessingState.PAUSING)
            elif 'paused' in state_str:
                self.controls_widget.set_state(ProcessingState.PAUSED)
            elif 'stopping' in state_str:
                self.controls_widget.set_state(ProcessingState.STOPPING)
            elif 'stopped' in state_str:
                self.controls_widget.set_state(ProcessingState.STOPPED)
            else:
                self.controls_widget.set_state(ProcessingState.IDLE)
                
    def enable_confirmation_dialogs(self, enabled: bool = True):
        """Enable or disable confirmation dialogs for destructive actions."""
        if self.controls_widget:
            self.controls_widget.set_confirmation_enabled(enabled)
            
    def show_retry_button(self, show: bool = True):
        """Show or hide the retry button based on failed items."""
        if self.controls_widget:
            self.controls_widget.show_retry_button(show)
            
    def update_progress(self, current: int, total: int, failed: int = 0):
        """Update progress information in the controls."""
        if self.controls_widget:
            self.controls_widget.update_progress_info(current, total, failed)
            
    def is_using_new_controls(self) -> bool:
        """Check if new controls are currently active."""
        return self.controls_widget is not None and self._old_buttons_hidden