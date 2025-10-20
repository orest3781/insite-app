# Visual Guide: Pull Model Feature

## 🎨 Step-by-Step with Screenshots Description

### Step 1: Open AI Model Manager
```
┌─────────────────────────────────────────┐
│  Main Window                    [Status]│
│                                          │
│  [Processing Queue]                     │
│                                          │
│  Bottom Right Corner:                   │
│  ┌──────────────────────────┐          │
│  │ ● AI Status: Connected   │ ← CLICK! │
│  └──────────────────────────┘          │
└─────────────────────────────────────────┘
```

### Step 2: AI Model Manager Dialog Opens
```
┌─────────────────────────────────────────────────────┐
│  AI Model Manager                         [🔄][❌]  │
├─────────────────────────────────────────────────────┤
│  ● AI Models Ready                                  │
│  Connected • 8 model(s) available                   │
│                                                      │
│  [Connection Settings]                              │
│  Ollama Host: http://localhost:11434                │
│  Default Model: llama3.2                            │
│                                                      │
│  [Available Models]  ← YOU'LL SEE YOUR MODELS HERE  │
│  ⭐ llama3.2:latest (default)                       │
│  ✓ qwen2.5:14b                                      │
│  ✓ qwen2.5:32b                                      │
│  ✓ llava:7b                                         │
│                                                      │
│  ┌─────────────────────────────────┐                │
│  │ Type model name here...         │ ← STEP 3      │
│  └─────────────────────────────────┘                │
│  [📥 Pull Model] [📋 Copy Command] ← CLICK THIS!   │
│                                                      │
│  [Diagnostics]                                      │
│  ✅ Connected to http://localhost:11434            │
│  ✅ Found 8 model(s)                               │
└─────────────────────────────────────────────────────┘
```

### Step 3: Enter Model Name
```
┌─────────────────────────────────────────────────────┐
│  Available Models                                   │
│  ⭐ llama3.2:latest (default)                       │
│  ✓ qwen2.5:14b                                      │
│                                                      │
│  ┌─────────────────────────────────┐                │
│  │ llama3.2:3b                     │ ← TYPE HERE   │
│  └─────────────────────────────────┘                │
│  [📥 Pull Model] [📋 Copy Command]                 │
└─────────────────────────────────────────────────────┘

Common Model Names to Try:
• llama3.2:3b    (Small, fast)
• llama3.2:7b    (Balanced)
• qwen2.5:7b     (Alternative)
• qwen2.5:14b    (High quality)
• llava:7b       (Vision)
```

### Step 4: Click Pull Model Button
```
┌─────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────┐                │
│  │ llama3.2:3b                     │                │
│  └─────────────────────────────────┘                │
│  [📥 Pull Model] ← CLICK!                          │
│                                                      │
│  A dialog will appear:                              │
│  ┌─────────────────────────────────────────┐       │
│  │  Pull Model                       [❌]  │       │
│  ├─────────────────────────────────────────┤       │
│  │  Download model 'llama3.2:3b' from      │       │
│  │  Ollama?                                │       │
│  │                                         │       │
│  │  This may take several minutes          │       │
│  │  depending on model size.               │       │
│  │                                         │       │
│  │        [Yes]  [No] ← CLICK YES!        │       │
│  └─────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Step 5: Download in Progress
```
┌─────────────────────────────────────────────────────┐
│  Available Models                                   │
│  ⭐ llama3.2:latest (default)                       │
│  ✓ qwen2.5:14b                                      │
│                                                      │
│  [📥 Pull Model] (disabled)                        │
│                                                      │
│  ╔═══════════════════════════════════════╗          │
│  ║ Downloading llama3.2:3b...           ║ ← PROGRESS│
│  ╚═══════════════════════════════════════╝          │
│                                                      │
│  [Diagnostics]                                      │
│  📥 Pulling model: llama3.2:3b                     │
│     This may take a few minutes...                  │
│     pulling manifest                                │
│     pulling 8eeb52dfb3bb... 10% ▓░░░░░░░░░         │
│     pulling 8eeb52dfb3bb... 50% ▓▓▓▓▓░░░░░         │
│     pulling 8eeb52dfb3bb... 100% ▓▓▓▓▓▓▓▓▓▓        │
│     verifying sha256 digest                         │
│     writing manifest                                │
│     success                                         │
└─────────────────────────────────────────────────────┘

⏱️ Wait Time: 2-30 minutes depending on model size
```

### Step 6: Download Complete!
```
┌─────────────────────────────────────────────────────┐
│  Available Models                                   │
│  ⭐ llama3.2:latest (default)                       │
│  ✓ llama3.2:3b          ← NEW MODEL!               │
│  ✓ qwen2.5:14b                                      │
│                                                      │
│  [Diagnostics]                                      │
│  ✅ Successfully pulled llama3.2:3b                │
│     Refreshing model list...                        │
│  ✅ Connected to http://localhost:11434            │
│  ✅ Found 9 model(s)                               │
└─────────────────────────────────────────────────────┘

✅ Your new model is ready to use!
```

### Step 7: Set as Default (Optional)
```
┌─────────────────────────────────────────────────────┐
│  Available Models                                   │
│  ⭐ llama3.2:latest (default)                       │
│  ✓ llama3.2:3b          ← DOUBLE-CLICK THIS!       │
│  ✓ qwen2.5:14b                                      │
│                                                      │
│  OR click once to select, then:                     │
│  [⭐ Set as Default] ← CLICK THIS                  │
│                                                      │
│  Confirmation dialog:                               │
│  ┌─────────────────────────────────────────┐       │
│  │  Set Default Model              [❌]    │       │
│  ├─────────────────────────────────────────┤       │
│  │  Set 'llama3.2:3b' as the default      │       │
│  │  model?                                 │       │
│  │                                         │       │
│  │  This will be used for all AI          │       │
│  │  processing tasks.                      │       │
│  │                                         │       │
│  │        [Yes]  [No]                     │       │
│  └─────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Step 8: New Default Set!
```
┌─────────────────────────────────────────────────────┐
│  Available Models                                   │
│  ✓ llama3.2:latest                                  │
│  ⭐ llama3.2:3b (default) ← NOW DEFAULT!           │
│  ✓ qwen2.5:14b                                      │
│                                                      │
│  [Diagnostics]                                      │
│  ✅ Default model changed to: llama3.2:3b          │
│     Note: Restart app or update config to persist   │
└─────────────────────────────────────────────────────┘

✅ All future processing will use llama3.2:3b!
```

---

## 🎯 Quick Reference Card

### Essential Buttons

| Button | Icon | What It Does |
|--------|------|--------------|
| Pull Model | 📥 | Downloads a new AI model |
| Copy Command | 📋 | Copies terminal command to clipboard |
| Set as Default | ⭐ | Makes selected model the active one |
| Delete Model | 🗑️ | Removes model from your system |
| Refresh Status | 🔄 | Updates the model list |
| Test Connection | 🔍 | Checks if Ollama is working |

---

## 🎬 Animation Flow (Text-Based)

### The Complete Pull Process:

```
START
  ↓
[Open AI Model Manager]
  ↓
[Type model name in text box]
  ↓
[Click 📥 Pull Model]
  ↓
[Confirmation dialog appears]
  ↓
[Click Yes]
  ↓
[Progress bar shows: ░░░░░░░░░░ 0%]
  ↓
[Progress updates: ▓▓▓░░░░░░░ 30%]
  ↓
[Progress updates: ▓▓▓▓▓▓░░░░ 60%]
  ↓
[Progress completes: ▓▓▓▓▓▓▓▓▓▓ 100%]
  ↓
[Success message appears]
  ↓
[Model appears in list with ✓]
  ↓
[Optional: Double-click to set as default]
  ↓
[Model marked with ⭐ (default)]
  ↓
DONE! ✅
```

---

## 🖱️ Mouse Actions Guide

### What You Can Click On:

```
┌─────────────────────────────────────────────────────┐
│  AI Model Manager                    [Button Area]  │
│                                      └─ Close dialog │
│  ● Status Indicator                                 │
│  └─ Shows connection status                         │
│                                                      │
│  [Available Models]                                 │
│  ⭐ llama3.2:latest (default)                       │
│  └─ Double-click: Set as default                    │
│  └─ Single-click: Select for actions                │
│                                                      │
│  ✓ qwen2.5:14b                                      │
│  └─ Double-click: Set as default                    │
│  └─ Single-click: Select for actions                │
│                                                      │
│  [⭐ Set as Default]                                │
│  └─ Sets selected model as active                   │
│                                                      │
│  [🗑️ Delete Model]                                 │
│  └─ Removes selected model                          │
│                                                      │
│  ┌─────────────────────────────────┐                │
│  │ Enter model name...             │                │
│  └─────────────────────────────────┘                │
│  └─ Type model name to download                     │
│                                                      │
│  [📥 Pull Model]                                    │
│  └─ Downloads the model you typed                   │
│                                                      │
│  [📋 Copy Command]                                  │
│  └─ Copies "ollama pull <model>" to clipboard       │
│                                                      │
│  [🔄 Refresh Status]                                │
│  └─ Checks for new/deleted models                   │
│                                                      │
│  [Close]                                            │
│  └─ Closes the dialog                               │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 Color Coding

### Visual Status Indicators:

```
Status Dot Colors:
● Green (🟢)  = Everything working perfectly
● Red (🔴)    = Connection problem / Error
● Gray (⚪)   = Checking status...

Model List Icons:
⭐ = Default/Active model (green background)
✓  = Available model
❌ = Error or unavailable

Progress Bar:
▓▓▓▓▓░░░░░ = Blue during download
▓▓▓▓▓▓▓▓▓▓ = Green when complete
▓▓▓▓▓▓▓▓▓▓ = Red if failed

Diagnostics Colors:
✅ = Success messages (green)
⚠️  = Warning messages (yellow)
❌ = Error messages (red)
📥 = Download progress (blue)
💡 = Tips and hints (gray)
```

---

## 📱 Compact View (For Quick Reference)

```
╔════════════════════════════════════╗
║    HOW TO PULL A MODEL (QUICK)    ║
╠════════════════════════════════════╣
║ 1. Click AI Status button         ║
║ 2. Type model name                 ║
║ 3. Click 📥 Pull Model            ║
║ 4. Click Yes                       ║
║ 5. Wait for download               ║
║ 6. Done! ✅                        ║
╚════════════════════════════════════╝

Popular Models:
├─ llama3.2:3b   (Fast, 2GB)
├─ llama3.2:7b   (Balanced, 5GB)
├─ qwen2.5:14b   (Quality, 9GB)
└─ llava:7b      (Vision, 5GB)
```

---

## 🔥 Pro Tips (Visual Indicators)

### What Each Section Shows You:

```
┌─ CONNECTION SETTINGS ─────────────┐
│  Shows: Where app connects to     │
│  Use: Verify Ollama host is right │
└───────────────────────────────────┘

┌─ AVAILABLE MODELS ────────────────┐
│  Shows: All downloaded models     │
│  Use: Select, set default, delete │
└───────────────────────────────────┘

┌─ PULL MODEL SECTION ──────────────┐
│  Shows: Download controls         │
│  Use: Add new models              │
└───────────────────────────────────┘

┌─ DIAGNOSTICS ─────────────────────┐
│  Shows: Real-time status messages │
│  Use: Debug problems, see progress│
└───────────────────────────────────┘
```

---

## ✨ Success Indicators

### You'll Know It Worked When:

```
BEFORE PULLING:
┌─────────────────────┐
│ Available Models    │
├─────────────────────┤
│ ⭐ llama3.2:latest  │
│ ✓ qwen2.5:14b       │
└─────────────────────┘
        ↓
    [Pull model]
        ↓
AFTER PULLING:
┌─────────────────────┐
│ Available Models    │
├─────────────────────┤
│ ⭐ llama3.2:latest  │
│ ✓ llama3.2:3b       │ ← NEW!
│ ✓ qwen2.5:14b       │
└─────────────────────┘

Diagnostics will show:
✅ Successfully pulled llama3.2:3b
✅ Found 3 model(s)
```

---

## 🎓 Learning Path

### Beginner → Expert

```
Level 1: BEGINNER
└─ Pull your first model using the button
└─ Wait for it to complete
└─ See it appear in the list
└─ ✅ You did it!

Level 2: COMFORTABLE  
└─ Pull multiple different models
└─ Set different models as default
└─ Understand which model for what task
└─ ✅ You're getting good!

Level 3: ADVANCED
└─ Use Copy Command for terminal
└─ Delete unused models to save space
└─ Compare model performance
└─ ✅ You're a pro!

Level 4: EXPERT
└─ Script multiple model pulls
└─ Optimize model selection for workload
└─ Manage model versions
└─ ✅ Master level!
```

---

This visual guide should make it crystal clear how to use the Pull Model feature! 🎉
