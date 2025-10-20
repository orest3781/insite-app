# Elapsed Time Fix - Manual Test Guide

This document provides steps to manually verify that the elapsed time calculation correctly handles pausing and resuming processing.

## Test Procedure

1. Run the application: `python main.py`
2. Go to the Processing tab
3. Start processing by clicking the Start button
4. Wait approximately 10 seconds and observe the elapsed time counter incrementing
   - Note the current elapsed time value (e.g., "⏳ Elapsed: 10s")
5. Click the Pause button
6. Verify that:
   - The status changes to "PAUSED"
   - The elapsed time counter stops incrementing and remains frozen at its current value
7. Wait at least 5 seconds (with processing paused)
8. Verify that the elapsed time display has not changed from step 5
9. Click the Resume button
10. Verify that:
    - The status changes to "RUNNING" 
    - The elapsed time counter resumes incrementing from where it left off
    - The elapsed time does NOT reset to zero
    - The elapsed time does NOT include the paused duration
11. Let processing continue for at least 5 more seconds
12. Verify elapsed time continues incrementing normally

## Expected Results

- When processing is running, the elapsed time increments normally
- When processing is paused, the elapsed time display freezes but preserves its value
- When processing is resumed, the elapsed time continues from the preserved value
- The elapsed time calculation correctly accounts for the time spent processing, excluding any paused periods

## Bug Fixed

The implementation now correctly:
1. Tracks the pause time
2. Records the elapsed seconds at the time of pausing
3. Displays the frozen elapsed time while paused
4. Adjusts the start time when resuming to account for the paused duration

This ensures accurate elapsed time tracking across pause/resume cycles, which also improves the accuracy of processing speed and ETA calculations.