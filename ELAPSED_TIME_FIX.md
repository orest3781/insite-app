# ELAPSED TIME FIX

## Problem
The elapsed time calculation was not correctly handling pause and resume operations. When processing was paused and then resumed, the elapsed time would either continue counting from the original start time (including the paused duration) or reset to zero, resulting in inaccurate timing and ETA calculations.

## Solution
The fix implements proper tracking of pause durations and adjusts the processing start time when resuming to account for paused periods.

### Key Changes:

1. Added tracking variables:
   - `_pause_time`: Records when processing was paused
   - `_paused_elapsed_seconds`: Stores the elapsed processing time at the point of pausing

2. Modified `_on_processing_state_changed` to:
   - Record the time and elapsed seconds when entering the PAUSED state
   - When returning to RUNNING state, adjust the start time to account for the pause duration

3. Modified `_update_elapsed_time` to:
   - Show a frozen elapsed time during PAUSED state
   - Calculate correct elapsed time when running
   - Handle proper timer stopping when not processing

4. Updated other functions to reset pause tracking variables when necessary:
   - `_reset_processing_ui`: Resets pause tracking when UI is reset
   - `_on_processing_started`: Resets pause tracking on processing start

### Benefits:
- Accurate elapsed time calculation across pause/resume cycles
- Improved processing speed and ETA accuracy
- Consistent and expected user experience when pausing/resuming processing

## Manual Testing
Please refer to `ELAPSED_TIME_MANUAL_TEST.md` for steps to verify this fix.