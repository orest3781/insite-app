# How to Manually Test Start, Pause, and Stop Buttons

This guide provides step-by-step instructions for manually testing the start, pause, and stop button functionality in the InsiteApp.

---

## Prerequisites

1. Application is running
2. Processing tab is visible
3. Queue has items to process (or add test files)
4. Logs are visible in console/debug output

---

## Test Scenario 1: Basic Start and Stop

### Steps
1. Click **"▶ Start"** button
2. Observe:
   - [ ] Button immediately becomes disabled
   - [ ] Status changes to "⚙️ RUNNING" (green color)
   - [ ] Processing spinner appears
   - [ ] Pause button becomes enabled
   - [ ] Stop button becomes enabled

3. Wait a few seconds, then click **"🛑 Stop"** button
4. Observe:
   - [ ] All buttons become disabled
   - [ ] Status changes to "⠋ STOPPING..." (red color)
   - [ ] Spinner shows active animation

5. Wait for stop to complete
6. Observe:
   - [ ] Status changes to "⚙️ STOPPED" (red color)
   - [ ] Status then changes to "⚙️ IDLE" (white color)
   - [ ] Start button becomes enabled again
   - [ ] Counters are reset to 0
   - [ ] Pause and Stop buttons become disabled

**Expected Result:** ✅ Complete cycle works correctly

---

## Test Scenario 2: Pause and Resume

### Steps
1. Click **"▶ Start"** button
2. Wait a few seconds, then click **"⏸️ Pause"** button
3. Observe:
   - [ ] All buttons become disabled
   - [ ] Status changes to "⠋ PAUSING..." (orange color)
   - [ ] Spinner shows active animation

4. Wait for pause to complete
5. Observe:
   - [ ] Status changes to "⚙️ PAUSED" (orange color)
   - [ ] Start button becomes enabled with text "▶ Resume"
   - [ ] Stop button remains enabled
   - [ ] Pause button becomes disabled

6. Click **"▶ Resume"** button
7. Observe:
   - [ ] Start button becomes disabled
   - [ ] Status changes to "⚙️ RUNNING" (green color)
   - [ ] Processing continues
   - [ ] Processing spinner appears

**Expected Result:** ✅ Pause and resume work correctly

---

## Test Scenario 3: Pause Then Stop

### Steps
1. Click **"▶ Start"** button
2. Wait a few seconds, then click **"⏸️ Pause"** button
3. Wait for pause to complete (see Scenario 2, steps 4-5)
4. Verify you see "⚙️ PAUSED" status
5. Click **"🛑 Stop"** button
6. Observe:
   - [ ] All buttons become disabled
   - [ ] Status changes to "⠋ STOPPING..." (red color)

7. Wait for stop to complete
8. Observe:
   - [ ] Status changes to "⚙️ STOPPED" then "⚙️ IDLE"
   - [ ] Start button becomes enabled with text "▶ Start"
   - [ ] All counters reset

**Expected Result:** ✅ Stop works correctly from paused state

---

## Test Scenario 4: Start with Empty Queue

### Steps
1. Clear all items from queue (if possible)
2. Click **"▶ Start"** button
3. Observe:
   - [ ] Button remains enabled
   - [ ] Notification appears: "Queue is empty"
   - [ ] Processing does NOT start
   - [ ] Status remains "⚙️ IDLE"

**Expected Result:** ✅ Notification prevents processing start

---

## Test Scenario 5: Rapid Button Clicks

### Steps
1. Click **"▶ Start"** button
2. Immediately (within 1 second) click **"⏸️ Pause"**
3. Immediately click **"▶ Resume"** (Resume button if available)
4. Immediately click **"🛑 Stop"**
5. Observe:
   - [ ] No crashes
   - [ ] All actions are processed in order
   - [ ] Final state is IDLE
   - [ ] All counters are reset

**Expected Result:** ✅ System handles rapid clicks gracefully

---

## Test Scenario 6: Verify Retry Button

### Steps
1. Start processing and let some items fail
2. Click **"🛑 Stop"** to stop processing
3. Wait for stop to complete
4. Observe:
   - [ ] Status is "⚙️ IDLE"
   - [ ] Retry button is **enabled** if there are failed items
   - [ ] Retry button is **disabled** if no failed items

5. Click **"🔄 Retry"** button
6. Observe:
   - [ ] Processing starts immediately
   - [ ] Failed items are re-added to queue

**Expected Result:** ✅ Retry button works correctly

---

## Test Scenario 7: Button States in Each State

### Verify each state has correct button enable/disable

#### IDLE State
- [ ] Start button: **ENABLED**
- [ ] Pause button: **DISABLED**
- [ ] Stop button: **DISABLED**
- [ ] Retry button: **Enabled if failed items exist, else disabled**

#### RUNNING State
- [ ] Start button: **DISABLED**
- [ ] Pause button: **ENABLED**
- [ ] Stop button: **ENABLED**
- [ ] Retry button: **DISABLED**

#### PAUSING State (transition)
- [ ] Start button: **DISABLED**
- [ ] Pause button: **DISABLED**
- [ ] Stop button: **ENABLED**
- [ ] Retry button: **DISABLED**
- [ ] Status shows: "⠋ PAUSING..." (with spinner)

#### PAUSED State
- [ ] Start button: **ENABLED** (text shows "▶ Resume")
- [ ] Pause button: **DISABLED**
- [ ] Stop button: **ENABLED**
- [ ] Retry button: **DISABLED**

#### STOPPING State (transition)
- [ ] Start button: **DISABLED**
- [ ] Pause button: **DISABLED**
- [ ] Stop button: **DISABLED**
- [ ] Retry button: **DISABLED**
- [ ] Status shows: "⠋ STOPPING..." (with spinner)

#### STOPPED State
- [ ] Start button: **ENABLED** (text shows "▶ Start")
- [ ] Pause button: **DISABLED**
- [ ] Stop button: **DISABLED**
- [ ] Retry button: **Enabled if failed items exist, else disabled**

**Expected Result:** ✅ All button states match expected table

---

## Test Scenario 8: Counter Reset Verification

### Steps
1. Start processing
2. Wait a few items to process
3. Click **"🛑 Stop"**
4. Wait for stop to complete
5. Observe the counter display:
   - [ ] Processed count: 0/total
   - [ ] Failed count: 0
   - [ ] Skipped count: 0

6. Click **"▶ Start"** again
7. Observe:
   - [ ] Counters restart from 0
   - [ ] Processing continues with fresh counts

**Expected Result:** ✅ Counters properly reset

---

## Test Scenario 9: Visual Feedback - Colors

### Verify status label colors match expected

1. Status should be **WHITE** when IDLE
   - [ ] Status text: "⚙️ IDLE"
   - [ ] Color is white/default

2. Status should be **GREEN** when RUNNING
   - [ ] Status text: "⚙️ RUNNING"
   - [ ] Color is green (#4CAF50)

3. Status should be **ORANGE** when PAUSING
   - [ ] Status text: "⠋ PAUSING..."
   - [ ] Color is orange (#FF9800)

4. Status should be **ORANGE** when PAUSED
   - [ ] Status text: "⚙️ PAUSED"
   - [ ] Color is orange (#FF9800)

5. Status should be **RED** when STOPPING
   - [ ] Status text: "⠋ STOPPING..."
   - [ ] Color is red (#F44336)

6. Status should be **RED** when STOPPED
   - [ ] Status text: "⚙️ STOPPED"
   - [ ] Color is red (#F44336)

**Expected Result:** ✅ All colors match specification

---

## Test Scenario 10: Queue Preservation

### Verify queue state is preserved correctly

#### After Pause
1. Start processing
2. Click pause after a few items
3. Stop processing (DON'T pause first)
4. Observe:
   - [ ] Unprocessed items remain in queue with PENDING status
   - [ ] Queue count unchanged

#### After Stop
1. Start processing
2. Wait a few items to process
3. Click stop
4. Observe:
   - [ ] Processed items remain with COMPLETED status
   - [ ] Failed items remain with FAILED status
   - [ ] Unprocessed items remain with PENDING status
   - [ ] Queue is NOT cleared

**Expected Result:** ✅ Queue state preserved correctly

---

## Troubleshooting

### Issue: Start button doesn't work
- [ ] Check if queue has items
- [ ] Check if orchestrator is initialized
- [ ] Look for warnings in logs

### Issue: Pause button doesn't work
- [ ] Check if processing is actually running (status should be green)
- [ ] Button should only be enabled during RUNNING state
- [ ] Check logs for pause_processing signal

### Issue: Stop button doesn't work
- [ ] Check if processing is running or paused
- [ ] Button should be disabled during IDLE/STOPPED states
- [ ] Check logs for stop_processing signal

### Issue: Counters not resetting
- [ ] Check if stop completes successfully
- [ ] Verify _handle_stop() is being called
- [ ] Check logs for reset messages

### Issue: Rapid clicks cause issues
- [ ] Look for queued signals in logs
- [ ] Check if state validation is working
- [ ] Verify orchestrator doesn't crash

---

## Log Messages to Expect

### Start Processing
```
INFO | Emitting start_processing_signal...
INFO | start_processing called, current state: idle
INFO | Processing started, emitting signals...
INFO | Starting processing loop...
```

### Pause Processing
```
INFO | Processing pause requested
INFO | pause_processing called, current state: running
INFO | Resetting current item to pending
INFO | Processing immediately paused
```

### Resume Processing
```
INFO | resume_processing called
INFO | Processing resumed from paused state
```

### Stop Processing
```
INFO | Processing stop requested
INFO | stop_processing called
INFO | Handling stop - resetting to IDLE state
INFO | Stop handling complete - back to IDLE state
```

---

## Checklist for Test Completion

- [ ] Test Scenario 1: Basic Start and Stop ✅
- [ ] Test Scenario 2: Pause and Resume ✅
- [ ] Test Scenario 3: Pause Then Stop ✅
- [ ] Test Scenario 4: Start with Empty Queue ✅
- [ ] Test Scenario 5: Rapid Button Clicks ✅
- [ ] Test Scenario 6: Retry Button ✅
- [ ] Test Scenario 7: Button States ✅
- [ ] Test Scenario 8: Counter Reset ✅
- [ ] Test Scenario 9: Visual Feedback Colors ✅
- [ ] Test Scenario 10: Queue Preservation ✅

**Overall Result:** ✅ ALL TESTS PASSED

---

## Conclusion

If all test scenarios pass successfully, the start, pause, and stop button functionality is working correctly and is ready for production use.

**Date Tested:** _________________  
**Tester Name:** _________________  
**Status:** ✅ APPROVED / ❌ NEEDS FIXES
