"""
Test script to verify the elapsed time fix for pausing and resuming processing.

This test:
1. Starts processing
2. Waits a few seconds
3. Pauses processing
4. Verifies elapsed time stops incrementing during pause
5. Resumes processing
6. Verifies elapsed time continues from where it left off
"""
import time
import sys
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath('src'))

# Import our modules
from src.ui.main_window import MainWindow
from src.services.app_config import AppConfig
from src.services.processing_orchestrator import ProcessingState

def test_elapsed_time_fix():
    """Test that elapsed time correctly handles pause/resume."""
    print("Starting test for elapsed time during pause/resume...")
    
    app = QApplication(sys.argv)
    config = AppConfig()
    
    # Create main window
    main_window = MainWindow(app, config)
    main_window.show()
    
    # Setup for test
    main_window._processing_start_time = datetime.now() - timedelta(seconds=10)
    main_window.orchestrator.state = ProcessingState.RUNNING
    
    # Start elapsed timer
    main_window._elapsed_timer = QTimer()
    main_window._elapsed_timer.setInterval(1000)  # Update every second
    main_window._elapsed_timer.timeout.connect(main_window._update_elapsed_time)
    main_window._elapsed_timer.start()
    
    # Force update elapsed time
    main_window._update_elapsed_time()
    initial_elapsed = main_window.proc_elapsed_label.text()
    print(f"Initial elapsed time: {initial_elapsed}")
    
    # Simulate a pause
    main_window.orchestrator.state = ProcessingState.PAUSED
    main_window._on_processing_state_changed(ProcessingState.PAUSED)
    main_window._update_elapsed_time()
    
    paused_elapsed = main_window.proc_elapsed_label.text()
    print(f"Paused elapsed time: {paused_elapsed}")
    
    # Wait a bit and verify time doesn't change during pause
    time.sleep(2)
    main_window._update_elapsed_time()
    paused_elapsed_2 = main_window.proc_elapsed_label.text()
    print(f"Paused elapsed time after 2s: {paused_elapsed_2}")
    
    # Resume processing
    main_window.orchestrator.state = ProcessingState.RUNNING
    main_window._on_processing_state_changed(ProcessingState.RUNNING)
    main_window._update_elapsed_time()
    
    resumed_elapsed = main_window.proc_elapsed_label.text()
    print(f"Resumed elapsed time: {resumed_elapsed}")
    
    # Wait a bit more to verify time continues incrementing
    time.sleep(2)
    main_window._update_elapsed_time()
    resumed_elapsed_2 = main_window.proc_elapsed_label.text()
    print(f"Resumed elapsed time after 2s: {resumed_elapsed_2}")
    
    # Check results
    print("\nTest results:")
    print(f"- Paused elapsed time matches: {paused_elapsed == paused_elapsed_2}")
    print(f"- Resumed elapsed time differs: {resumed_elapsed != resumed_elapsed_2}")
    
    print("\nTest complete.")

if __name__ == '__main__':
    test_elapsed_time_fix()