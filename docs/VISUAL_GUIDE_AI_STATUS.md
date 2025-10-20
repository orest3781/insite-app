# AI Model Status - Visual Guide

## Status Bar Button Location

```
┌─────────────────────────────────────────────────────────────────┐
│  Previewless Insight Viewer                            ─ □ ✕    │
├─────────────────────────────────────────────────────────────────┤
│  File   View   Tools   Help                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  📁 Watch  │  📋 Queue  │  ⚙️ Processing  │  📊 Results  │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │                                                           │  │
│  │                  Your Content Here                        │  │
│  │                                                           │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Ready                                          ● [● AI Models] │◄─ HERE!
└─────────────────────────────────────────────────────────────────┘
```

---

## Button States

### 🟢 Green - Everything Working
```
┌──────────────────┐
│  ● AI Models  │  ← Green dot (#4CAF50)
└──────────────────┘
   Tooltip: "AI Models: Connected ✓
            Click to manage models"
```

### 🔴 Red - Problem Detected
```
┌──────────────────┐
│  ● AI Models  │  ← Red dot (#F44336)
└──────────────────┘
   Tooltip: "AI Models: Not Connected ✕
            Click to troubleshoot"
```

### ⚪ Gray - Checking...
```
┌──────────────────┐
│  ● AI Models  │  ← Gray dot (#888888)
└──────────────────┘
   Tooltip: "Checking AI Model status..."
```

---

## AI Model Manager Dialog

### Full Dialog Layout
```
┌────────────────────────────────────────────────────────┐
│  AI Model Manager                             ─ □ ✕   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ●  AI Models Ready                    [🔍 Test Conn] │◄─ Status Header
│     Connected • 2 model(s) available                   │   (Large dot)
│                                                         │
├────────────────────────────────────────────────────────┤
│  ┌─ Connection Settings ─────────────────────────────┐│
│  │  Ollama Host:      http://localhost:11434        ││◄─ Config Display
│  │  Default Model:    llama3.2                      ││
│  │  Temperature:      0.4                           ││
│  │  Max Tokens:       270                           ││
│  └──────────────────────────────────────────────────┘│
│                                                         │
│  ┌─ Available Models ─────────────────────────────────┐│
│  │  ✓ llama3.2 (active)                             ││◄─ Model List
│  │  ✓ llama2                                        ││   (Green highlight
│  │                                                   ││    for active)
│  │                                                   ││
│  │  [Enter model name...       ] [📥 Pull Model]   ││◄─ Download UI
│  │  💡 Tip: Pull models using: ollama pull model   ││
│  └──────────────────────────────────────────────────┘│
│                                                         │
│  ┌─ Diagnostics ──────────────────────────────────────┐│
│  │  ✅ Connected to http://localhost:11434          ││◄─ Console
│  │  ✅ Found 2 model(s)                             ││   (Dark theme)
│  │  ✅ Active model 'llama3.2' is available         ││
│  │                                                   ││
│  └──────────────────────────────────────────────────┘│
│                                                         │
│            [🔄 Refresh Status]              [Close]   │
└────────────────────────────────────────────────────────┘
```

---

## Dialog - Error State

### When Ollama Not Running
```
┌────────────────────────────────────────────────────────┐
│  AI Model Manager                             ─ □ ✕   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ●  AI Models Not Available           [🔍 Test Conn]  │
│     Cannot connect to Ollama service                   │◄─ RED dot
│                                                         │
├────────────────────────────────────────────────────────┤
│  ┌─ Connection Settings ─────────────────────────────┐│
│  │  Ollama Host:      http://localhost:11434        ││
│  │  Default Model:    llama3.2                      ││
│  │  Temperature:      0.4                           ││
│  │  Max Tokens:       270                           ││
│  └──────────────────────────────────────────────────┘│
│                                                         │
│  ┌─ Available Models ─────────────────────────────────┐│
│  │  No models found - Ollama may not be running     ││◄─ Empty state
│  │                                                   ││   (Red text)
│  │                                                   ││
│  │  [Enter model name...       ] [📥 Pull Model]   ││
│  │  💡 Tip: Pull models using: ollama pull model   ││
│  └──────────────────────────────────────────────────┘│
│                                                         │
│  ┌─ Diagnostics ──────────────────────────────────────┐│
│  │  ❌ Cannot connect to http://localhost:11434     ││◄─ Error messages
│  │                                                   ││   with steps
│  │  Troubleshooting steps:                          ││
│  │  1. Check if Ollama is installed                 ││
│  │     • Download from: https://ollama.ai           ││
│  │  2. Start Ollama service:                        ││
│  │     • Run: ollama serve                          ││
│  │  3. Verify the host URL in Settings              ││
│  │  4. Pull a model:                                ││
│  │     • Run: ollama pull llama3.2                  ││
│  └──────────────────────────────────────────────────┘│
│                                                         │
│            [🔄 Refresh Status]              [Close]   │
└────────────────────────────────────────────────────────┘
```

---

## User Interaction Flow

### Happy Path (Everything Working)
```
Step 1: User sees green dot
        ┌──────────────────┐
        │  ● AI Models  │  ← GREEN
        └──────────────────┘

Step 2: User hovers
        Shows: "AI Models: Connected ✓"
        
Step 3: User continues work
        (No action needed!)
```

### Problem Path (Troubleshooting)
```
Step 1: User sees red dot
        ┌──────────────────┐
        │  ● AI Models  │  ← RED
        └──────────────────┘

Step 2: User clicks button
        ↓
        Dialog opens showing:
        ●  AI Models Not Available
           Cannot connect to Ollama service

Step 3: User reads diagnostics
        ❌ Cannot connect to http://localhost:11434
        
        Troubleshooting steps:
        1. Check if Ollama is installed
        2. Start Ollama service: ollama serve
        ...

Step 4: User opens terminal
        > ollama serve
        
Step 5: User clicks "Test Connection"
        ↓
        Status updates to GREEN ✓
        
Step 6: User closes dialog
        Button is now green in status bar
```

### Model Installation Path
```
Step 1: User clicks button
        ↓
Step 2: Dialog shows "Model not found" warning
        ⚠️ Active model 'llama3.2' NOT found!
           Run: ollama pull llama3.2

Step 3: User types model name
        [llama3.2                      ]

Step 4: User clicks "Pull Model"
        ↓
        Diagnostics show:
        To pull model 'llama3.2':
        1. Open a terminal
        2. Run: ollama pull llama3.2
        3. Click 'Refresh Status' when complete

Step 5: User opens terminal
        > ollama pull llama3.2
        pulling manifest
        pulling 2af3b81862c6... 100% ▕████████████████▏ 1.3 GB
        ...

Step 6: User clicks "Refresh Status"
        ↓
        Model appears in list:
        ✓ llama3.2 (active)
        
Step 7: Status turns GREEN ✓
```

---

## Color Palette

### Status Colors
```
GREEN (Success):    #4CAF50   ████  Material Green 500
RED (Error):        #F44336   ████  Material Red 500
GRAY (Checking):    #888888   ████  Neutral Gray
YELLOW (Warning):   #FF9800   ████  Material Orange 500
```

### Dialog Colors
```
Background:         #FFFFFF   ████  White (light mode)
Console BG:         #1e1e1e   ████  VS Code dark
Console Text:       #d4d4d4   ████  Light gray
Active Model BG:    #2d5f2d   ████  Dark green
```

---

## Status Indicators

### Connection Status
```
✅  Connected and working
❌  Not connected / Error
⚠️  Connected but warning (model missing)
ℹ️  Information / Tip
💡  Helpful hint
```

### Buttons
```
🔍  Test Connection    - Check connection now
🔄  Refresh Status     - Update model list
📥  Pull Model         - Get download instructions
✕   Close             - Close dialog
```

---

## Timeline - Background Monitoring

```
Time: 0s      App Starts
              ↓
Time: 1s      Initial Check (QTimer.singleShot)
              ↓
              [Check Status]
              ↓
Time: 2s      Result: GREEN or RED
              ↓
              Button updates color
              ↓
Time: 31s     Background Check #1 (QTimer every 30s)
              ↓
              [Check Status]
              ↓
Time: 61s     Background Check #2
              ↓
Time: 91s     Background Check #3
              ↓
              ... (continues every 30s)
```

---

## Threading Model

```
Main Thread (UI)                   Background Thread (Checks)
─────────────                      ────────────────────────────
                                   
Timer triggers                     
   │                               
   ├─ Start ModelCheckThread ────► Thread starts
   │                                  │
   │                                  ├─ verify_connection()
   │                                  │   (Network call)
   │                                  │
   │                                  ├─ list_models()
   │                                  │   (Network call)
   │                                  │
   │◄─ status_checked signal ─────────┤
   │   (success, message, models)     │
   │                                  Thread ends
   ├─ Update UI colors               
   ├─ Update tooltips                
   └─ Emit status_changed            
```

---

## Size Specifications

### Button
- Height: Status bar height (~22px)
- Padding: 4px vertical, 12px horizontal
- Font: Bold, default size
- Dot: Unicode bullet (●)

### Dialog
- Minimum Size: 700x600 pixels
- Status Dot: 32px font size
- Title Font: 14pt bold
- Console Height: 150px max

---

## Accessibility

### Color Blind Support
- Not color-only: Uses ✓ and ✕ symbols
- Tooltips: Descriptive text
- Console: Text-based diagnostics

### Keyboard Navigation
- Tab: Navigate between controls
- Space: Activate buttons
- Enter: Accept dialog
- Escape: Close dialog

---

## Quick Reference

### When Button is GREEN
```
Everything is working correctly!
- Ollama is running
- Model is installed
- Ready for AI processing
```

### When Button is RED
```
Something needs attention:
- Click button to see what's wrong
- Read diagnostics console
- Follow troubleshooting steps
```

### When to Check
- Before starting batch processing
- After restarting computer
- When seeing processing errors
- Anytime you're unsure

---

**Visual Design Goal:** 
Make AI model status **impossible to miss** and **easy to understand** at a glance!
