# Testing the AI Model Status Feature

**Quick Test Guide**

---

## ✅ Test 1: Basic Functionality (Everything Working)

### Prerequisites
- Ollama is installed
- Ollama is running (`ollama serve`)
- At least one model is installed (`ollama pull llama3.2`)

### Steps
1. Start the application: `python main.py`
2. Look at bottom-right corner of status bar
3. **Wait 1-2 seconds** for initial check

### Expected Results
- ✅ Button appears: `● AI Models`
- ✅ Dot is **GREEN** (#4CAF50)
- ✅ Hover shows: "AI Models: Connected ✓"
- ✅ Click button opens dialog
- ✅ Dialog shows: "● AI Models Ready"
- ✅ Dialog lists installed models
- ✅ Active model has green highlight

### Pass Criteria
All checkboxes above are ✅

---

## 🔴 Test 2: Ollama Not Running

### Prerequisites
- Stop Ollama service

### Steps
1. Stop Ollama (close `ollama serve` terminal)
2. **Wait 30 seconds** for background check OR click "Test Connection"
3. Observe button color change

### Expected Results
- ✅ Button turns **RED** (#F44336)
- ✅ Hover shows: "AI Models: Not Connected ✕"
- ✅ Click button opens dialog
- ✅ Dialog shows: "❌ AI Models Not Available"
- ✅ Diagnostics shows error message:
  ```
  ❌ Cannot connect to http://localhost:11434
  
  Troubleshooting steps:
  1. Check if Ollama is installed
  2. Start Ollama service:
     • Run: ollama serve
  ...
  ```

### Pass Criteria
All checkboxes above are ✅

---

## 🟢 Test 3: Recovery from Error State

### Prerequisites
- Button is currently RED (from Test 2)

### Steps
1. Open terminal
2. Start Ollama: `ollama serve`
3. Go back to the app
4. Click "Test Connection" button in dialog OR wait 30 seconds

### Expected Results
- ✅ Status changes to: "● AI Models Ready"
- ✅ Button turns **GREEN**
- ✅ Models appear in list
- ✅ Diagnostics shows:
  ```
  ✅ Connected to http://localhost:11434
  ✅ Found N model(s)
  ✅ Active model 'llama3.2' is available
  ```

### Pass Criteria
All checkboxes above are ✅

---

## ⚠️ Test 4: Model Missing Warning

### Prerequisites
- Ollama is running
- Configured model is NOT installed

### Setup
1. Change model in settings to something not installed (e.g., `llama99`)
2. Restart app

### Expected Results
- ✅ Button is **RED**
- ✅ Dialog shows warning:
  ```
  ⚠️ Active model 'llama99' NOT found!
     Run: ollama pull llama99
  ```
- ✅ Diagnostics shows model missing error

### Pass Criteria
Warning message appears correctly

---

## 🔄 Test 5: Auto-Refresh (Background Monitoring)

### Prerequisites
- App is running with GREEN status

### Steps
1. Note current status: GREEN
2. Stop Ollama service (`ollama serve` terminal)
3. **Wait 30-35 seconds** (background check interval)
4. Observe button

### Expected Results
- ✅ Button automatically turns RED (without clicking anything)
- ✅ Tooltip updates to "Not Connected"

### Recovery Test
5. Start Ollama again: `ollama serve`
6. **Wait 30-35 seconds**
7. Observe button

### Expected Results
- ✅ Button automatically turns GREEN
- ✅ Tooltip updates to "Connected"

### Pass Criteria
Auto-refresh works in both directions

---

## 📥 Test 6: Model Pull Instructions

### Steps
1. Open AI Model Manager dialog
2. Type a model name in the text box: `mistral`
3. Click "📥 Pull Model" button

### Expected Results
- ✅ Diagnostics console shows:
  ```
  To pull model 'mistral':
  1. Open a terminal
  2. Run: ollama pull mistral
  3. Click 'Refresh Status' when complete
  ```
- ✅ Text box is cleared
- ✅ Instructions are clear and actionable

### Pass Criteria
Instructions appear as expected

---

## 🎨 Test 7: Visual Design

### Button Appearance
1. Check button is visible in status bar
2. Check colors match specification:
   - GREEN: `#4CAF50`
   - RED: `#F44336`
3. Check hover effect works
4. Check button is clickable

### Dialog Appearance
1. Open dialog
2. Check layout:
   - Status header at top
   - Large dot (32px) clearly visible
   - Sections properly grouped
   - Buttons aligned
3. Check diagnostics console:
   - Dark background (#1e1e1e)
   - Light text (#d4d4d4)
   - Monospace font
   - Readable contrast

### Pass Criteria
- ✅ Button looks professional
- ✅ Dialog is well-organized
- ✅ Colors are correct
- ✅ Text is readable

---

## ⏱️ Test 8: Performance

### Startup Time
1. Start app
2. Time how long until status check completes

### Expected Results
- ✅ Check starts after 1 second
- ✅ Check completes in <2 seconds (with working connection)
- ✅ UI remains responsive during check

### Background Checks
1. Open Task Manager / Activity Monitor
2. Watch CPU usage

### Expected Results
- ✅ CPU usage <1% during checks
- ✅ No noticeable lag or freezing
- ✅ Checks happen every 30 seconds

### Pass Criteria
No performance issues observed

---

## 🧵 Test 9: Threading (Non-Blocking)

### Steps
1. Open AI Model Manager dialog
2. Click "Test Connection" button
3. **Immediately** try to:
   - Move the dialog window
   - Click other buttons
   - Type in the text box

### Expected Results
- ✅ UI remains responsive during check
- ✅ Can interact with dialog while checking
- ✅ No freezing or lag
- ✅ Status updates after check completes

### Pass Criteria
UI never freezes or becomes unresponsive

---

## 📱 Test 10: Tooltips and Messages

### Tooltips
1. Hover over button in different states:
   - GREEN state
   - RED state
   - During check (gray)

### Expected Results
- ✅ GREEN: "AI Models: Connected ✓\nClick to manage models"
- ✅ RED: "AI Models: Not Connected ✕\nClick to troubleshoot"
- ✅ Tooltips appear after 1 second hover

### Dialog Messages
1. Check all status messages are clear
2. Check error messages provide solutions

### Pass Criteria
All messages are user-friendly and actionable

---

## 🔧 Test 11: Error Handling

### Test A: Network Timeout
1. Configure wrong host: `http://localhost:99999`
2. Click "Test Connection"

### Expected Results
- ✅ Timeout after 5 seconds
- ✅ Shows error message
- ✅ Button turns RED
- ✅ No crash

### Test B: Invalid URL
1. Configure invalid host: `not-a-url`
2. Click "Test Connection"

### Expected Results
- ✅ Shows error message
- ✅ Button turns RED
- ✅ No crash

### Pass Criteria
All errors handled gracefully

---

## 🔁 Test 12: State Persistence

### Steps
1. Note current status (GREEN or RED)
2. Close dialog
3. Reopen dialog

### Expected Results
- ✅ Status is the same
- ✅ Model list is cached (loads instantly)
- ✅ No unnecessary re-checks

### Pass Criteria
State is preserved correctly

---

## 📋 Test 13: Multiple Models

### Prerequisites
- Install multiple models:
  ```powershell
  ollama pull llama3.2
  ollama pull llama2
  ollama pull mistral
  ```

### Steps
1. Open AI Model Manager
2. Check model list

### Expected Results
- ✅ All installed models appear
- ✅ Active model has "(active)" label
- ✅ Active model has green background
- ✅ Other models listed without highlight

### Pass Criteria
Model list is accurate and clear

---

## ✅ Test 14: Integration with Main App

### Steps
1. Start processing with GREEN status
2. Verify processing works
3. Stop Ollama during processing
4. Observe behavior

### Expected Results
- ✅ Processing completes if already started
- ✅ New items may fail with LLM errors
- ✅ Status button shows RED
- ✅ Error messages reference AI connection

### Pass Criteria
Status indicator accurately reflects LLM availability

---

## 🎯 Full System Test

### Complete Workflow
```
1. Fresh start:
   - App not running
   - Ollama not running
   
2. Start app → See RED button
3. Click button → See troubleshooting
4. Open terminal → Run: ollama serve
5. Click "Test Connection" → Turns GREEN
6. See model list → llama3.2 (active)
7. Type "mistral" → Click "Pull Model"
8. Get instructions → Follow in terminal
9. Click "Refresh Status" → See mistral in list
10. Close dialog → Button stays GREEN
11. Wait 30 seconds → Button still GREEN
12. Stop Ollama → Wait 30 seconds → Button RED
13. Start Ollama → Wait 30 seconds → Button GREEN
```

### Pass Criteria
Entire workflow works smoothly

---

## 📊 Test Results Template

```
Test Date: _______________
Tester: __________________

┌────────────────────────────────────────────┐
│ TEST RESULTS                               │
├────────────────────────────────────────────┤
│ Test 1:  Basic Functionality      [ ]     │
│ Test 2:  Ollama Not Running       [ ]     │
│ Test 3:  Recovery from Error      [ ]     │
│ Test 4:  Model Missing Warning    [ ]     │
│ Test 5:  Auto-Refresh             [ ]     │
│ Test 6:  Model Pull Instructions  [ ]     │
│ Test 7:  Visual Design            [ ]     │
│ Test 8:  Performance              [ ]     │
│ Test 9:  Threading                [ ]     │
│ Test 10: Tooltips and Messages    [ ]     │
│ Test 11: Error Handling           [ ]     │
│ Test 12: State Persistence        [ ]     │
│ Test 13: Multiple Models          [ ]     │
│ Test 14: Integration              [ ]     │
├────────────────────────────────────────────┤
│ OVERALL STATUS:            [  PASS/FAIL  ] │
└────────────────────────────────────────────┘

Notes:
_____________________________________________
_____________________________________________
_____________________________________________
```

---

## 🚨 Known Issues / Limitations

### Expected Behavior (Not Bugs)
- **30-second delay:** Status won't update instantly (by design)
- **Startup delay:** 1-second delay before first check (intentional)
- **Network timeout:** 5-second timeout may seem slow on bad networks

### Future Improvements
- One-click model download (currently shows instructions)
- Real-time download progress
- Model switching without Settings
- Performance metrics

---

## 💡 Testing Tips

1. **Be Patient:** Background checks take 30 seconds
2. **Use "Test Connection":** For immediate feedback
3. **Check Diagnostics:** They show exactly what's happening
4. **Read Tooltips:** They provide quick status info
5. **Test Both States:** GREEN and RED paths equally important

---

## ✅ Sign-Off Checklist

Before marking feature as "Production Ready":

- [ ] All 14 tests pass
- [ ] Visual design matches specification
- [ ] No performance issues
- [ ] Error handling works correctly
- [ ] Documentation is complete
- [ ] User guide is clear
- [ ] No crashes or exceptions
- [ ] Threading is non-blocking
- [ ] Auto-refresh works reliably
- [ ] Integration with main app verified

---

**Ready to test!** Follow the tests in order for best results. 🚀
