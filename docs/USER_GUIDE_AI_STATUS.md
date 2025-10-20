# AI Model Status - Quick User Guide

## What is it?

A **color-coded button** in the bottom-right corner of the window that shows if your AI models are working correctly.

---

## The Status Button

### Location
Look at the **bottom-right** of the window (status bar):
```
┌────────────────────────────────────┐
│                                    │
│         Your Content Here          │
│                                    │
└────────────────────────────────────┘
  Ready        [● AI Models] ← Here!
```

### What the Colors Mean

| Color | Meaning | What to Do |
|-------|---------|------------|
| 🟢 **Green** | Everything is working! | Nothing - you're good to go |
| 🔴 **Red** | Something needs attention | Click the button to see what's wrong |
| ⚪ **Gray** | Checking status... | Wait a moment |

---

## Using the AI Model Manager

### Opening the Dialog
**Click the "● AI Models" button** in the status bar.

### What You'll See

#### 1. Big Status Indicator at Top
```
● AI Models Ready
  Connected • 2 model(s) available
```
- **Green dot:** Everything working
- **Red dot:** Problems detected

#### 2. Your Current Settings
Shows what models you're using:
- Ollama server address
- Active model name
- AI settings (temperature, tokens)

#### 3. Available Models List
Lists all AI models you have installed:
- ✓ **llama3.2 (active)** ← Your current model
- ✓ llama2

#### 4. Diagnostics Console
Black box at bottom shows what's happening:
```
✅ Connected to http://localhost:11434
✅ Found 2 model(s)
✅ Active model 'llama3.2' is available
```

---

## Common Scenarios

### ✅ Everything Working (Green)
**What you see:**
- Green dot
- "AI Models Ready" message
- List of available models

**What to do:**
- Nothing! Just close the dialog

---

### ❌ Ollama Not Running (Red)

**What you see:**
```
❌ AI Models Not Available
  Cannot connect to Ollama service
```

**Diagnostics shows:**
```
❌ Cannot connect to http://localhost:11434

Troubleshooting steps:
1. Check if Ollama is installed
2. Start Ollama service:
   • Run: ollama serve
```

**How to fix:**
1. Open a **terminal** (Command Prompt or PowerShell)
2. Type: `ollama serve`
3. Press Enter
4. Keep that window open
5. Click **"Test Connection"** button in the dialog
6. Should turn green! ✅

---

### ⚠️ Model Not Installed (Red)

**What you see:**
```
⚠️ Active model 'llama3.2' NOT found!
   Run: ollama pull llama3.2
```

**How to fix:**
1. Open a **terminal**
2. Type: `ollama pull llama3.2`
3. Press Enter (this will download ~2GB - takes a few minutes)
4. Wait for download to complete
5. Click **"Refresh Status"** button
6. Should turn green! ✅

---

## Installing a New Model

### Using the Dialog

1. Open the AI Model Manager (click the status button)
2. Look for the **text box** near the model list
3. Type a model name (e.g., `llama3.2` or `llama2`)
4. Click **"📥 Pull Model"** button
5. The dialog will show you the exact command:
   ```
   To pull model 'llama3.2':
   1. Open a terminal
   2. Run: ollama pull llama3.2
   3. Click 'Refresh Status' when complete
   ```
6. Follow those instructions in a terminal

### Popular Models
- `llama3.2` - Latest Llama (recommended)
- `llama2` - Previous version
- `mistral` - Fast and efficient
- `codellama` - Specialized for code

**Tip:** Each model is 2-7GB. Make sure you have space!

---

## Buttons Explained

| Button | What It Does |
|--------|--------------|
| **🔍 Test Connection** | Check if Ollama is working right now |
| **🔄 Refresh Status** | Update the model list |
| **📥 Pull Model** | Get instructions to download a model |
| **Close** | Close the dialog |

---

## Automatic Monitoring

The status button **automatically checks** every 30 seconds:
- If Ollama stops → Button turns red
- If Ollama starts → Button turns green

You don't need to do anything - it just works!

---

## Troubleshooting Tips

### Problem: Button is always red

**Check these things:**

1. **Is Ollama installed?**
   - Download from: https://ollama.ai
   - Install and restart your computer

2. **Is Ollama running?**
   - Open terminal
   - Type: `ollama serve`
   - Keep it running

3. **Do you have a model?**
   - Open terminal
   - Type: `ollama pull llama3.2`
   - Wait for download

4. **Still not working?**
   - Click the button
   - Read the diagnostics console
   - Follow the troubleshooting steps shown

---

### Problem: Button turns red while I'm working

**What happened:**
- Ollama probably crashed or stopped

**How to fix:**
1. Open a terminal
2. Type: `ollama serve`
3. Wait ~30 seconds
4. Button should turn green automatically

---

### Problem: "Model not found" but I downloaded it

**Try this:**
1. Click the button to open the dialog
2. Click **"Refresh Status"**
3. Check if the model appears in the list
4. If not, download again: `ollama pull model-name`

---

## Quick Reference

### Status Colors
- 🟢 = Good
- 🔴 = Problem
- ⚪ = Checking

### Essential Commands
```powershell
# Start Ollama
ollama serve

# Download a model
ollama pull llama3.2

# List your models
ollama list
```

### When to Check
- Before starting a big batch process
- After restarting your computer
- When you see processing errors
- Anytime the button is red

---

## Advanced: Changing the Active Model

**To use a different model:**
1. Go to **Tools → Settings**
2. Click the **LLM** tab
3. Change "Default Model" to your preferred model
4. Click **OK**
5. Restart the application

**Note:** The new model must be installed first!

---

## Need More Help?

### Check the Diagnostics
The black console box in the dialog shows:
- ✅ What's working
- ❌ What's broken
- 💡 How to fix it

### Read the Error Messages
They tell you exactly what to do:
```
⚠️ Active model 'llama3.2' NOT found!
   Run: ollama pull llama3.2
```
↑ Just do what it says!

### Still Stuck?
1. Check that Ollama is running: `ollama serve`
2. Check you have a model: `ollama list`
3. Check the full logs in `logs/insite.log`

---

**Remember:** The AI Model Status button is your friend! 
- **Green = Happy** 😊
- **Red = Need Help** 🔧

Click it whenever you're unsure!
