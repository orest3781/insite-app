# How to Pull (Download) AI Models

## Quick Guide: Using the Pull Model Feature

The AI Model Manager now has a **built-in model downloader** so you don't need to use the terminal!

---

## 📥 Method 1: Pull Model Button (EASIEST)

### Step-by-Step Instructions:

1. **Open the AI Model Manager**
   - Click the AI status button in the bottom-right corner of the main window
   - Or go to: Settings → AI Model Manager (if available)

2. **Enter the Model Name**
   - In the "Available Models" section, find the text box at the bottom
   - Type the model name you want to download
   - Examples:
     - `llama3.2` (recommended for general use)
     - `llama3.2:3b` (smaller, faster version)
     - `llama3.2:7b` (larger, more capable)
     - `qwen2.5:14b` (excellent alternative)
     - `llava:7b` (for vision analysis)

3. **Click "📥 Pull Model"**
   - A confirmation dialog will appear
   - Click "Yes" to start the download

4. **Wait for Download**
   - A progress bar will appear showing download status
   - Watch the Diagnostics section for real-time progress
   - Messages will show download stages:
     ```
     📥 Pulling model: llama3.2
        pulling manifest
        pulling 8eeb52dfb3bb... 100%
        pulling 73b313b5552d... 100%
        verifying sha256 digest
        writing manifest
        success
     ✅ Successfully pulled llama3.2
     ```

5. **Model is Ready!**
   - The model will automatically appear in your model list
   - It's immediately available for use

---

## 📋 Method 2: Copy Command (For Terminal Users)

If you prefer using the terminal or if the automatic pull doesn't work:

1. **Enter Model Name** in the text box (e.g., `llama3.2`)

2. **Click "📋 Copy Command"**
   - The command `ollama pull llama3.2` is copied to your clipboard
   - You'll see a confirmation in the Diagnostics:
     ```
     📋 Copied to clipboard: ollama pull llama3.2
        Paste in terminal to pull model
     ```

3. **Open a Terminal**
   - Windows: Press `Win+R`, type `cmd` or `powershell`, press Enter
   - Or use the built-in VS Code terminal
   - Mac/Linux: Open Terminal app

4. **Paste and Run**
   - Right-click and paste (or Ctrl+V)
   - Press Enter
   - Wait for download to complete

5. **Return to AI Model Manager**
   - Click "🔄 Refresh Status" button
   - Your new model will appear in the list

---

## 🎯 Recommended Models

### For General Document Processing (Current Use)
- **`llama3.2`** (Default, balanced)
- **`llama3.2:3b`** (Faster, uses less RAM)
- **`qwen2.5:7b`** (Great alternative, fast)
- **`qwen2.5:14b`** (More accurate, slower)

### For Vision Analysis (Images)
- **`llava:7b`** (Current vision model)
- **`llava:13b`** (Better quality, needs more RAM)

### For Fast Testing
- **`llama3.2:1b`** (Smallest, quickest responses)

### For Best Quality
- **`qwen2.5:32b`** (Highest quality, slowest)
- **`llama3.1:70b`** (Enterprise-grade, requires 64GB+ RAM)

---

## ⏱️ Download Times (Approximate)

Model size depends on parameters and quantization:

| Model | Size | Fast Internet | Slow Internet |
|-------|------|---------------|---------------|
| llama3.2:1b | ~800 MB | 2-3 min | 10-15 min |
| llama3.2:3b | ~2.0 GB | 5-7 min | 20-30 min |
| llama3.2:7b | ~4.7 GB | 10-15 min | 40-60 min |
| qwen2.5:14b | ~9.0 GB | 20-30 min | 1-2 hours |
| llama3.1:70b | ~40 GB | 1-2 hours | 4-6 hours |

**Tip:** Start with smaller models (1b-3b) for testing, then upgrade if needed.

---

## 🔧 Troubleshooting

### ❌ "Ollama command not found"

**Problem:** Ollama is not installed or not in PATH.

**Solution:**
1. Download Ollama from: https://ollama.ai
2. Install it (Windows: run installer, Mac: drag to Applications)
3. Restart the application
4. Try again

---

### ❌ "Cannot connect to Ollama service"

**Problem:** Ollama is installed but not running.

**Solution:**

**Option A - Auto-start (Recommended):**
- Ollama usually starts automatically on system boot
- Restart your computer

**Option B - Manual start:**
1. Open terminal
2. Run: `ollama serve`
3. Keep terminal window open
4. Return to AI Model Manager and click "🔄 Refresh Status"

---

### ❌ Download Stuck or Very Slow

**Problem:** Network issues or large model.

**Solutions:**
- Check your internet connection
- Wait longer (large models can take 30-60 minutes)
- Try a smaller model first (e.g., `llama3.2:3b` instead of `qwen2.5:32b`)
- Close and reopen AI Model Manager, then click Refresh
- Use terminal method instead (Method 2 above)

---

### ❌ "Model 'llama3.2' NOT found" (After Installing)

**Problem:** Model name mismatch or refresh needed.

**Solution:**
1. Click "🔄 Refresh Status" button
2. Check if model appears in the list
3. If model is "llama3.2:latest", it should automatically match "llama3.2"
4. Try setting it as default (double-click the model)

---

### ❌ Out of Disk Space

**Problem:** Models are large and disk is full.

**Solutions:**
- Free up disk space (models store in `~/.ollama/models/`)
- Delete unused models using "🗑️ Delete Model" button
- Choose smaller models (1b or 3b versions)

**Check disk space:**
- Windows: Open File Explorer, right-click C: drive → Properties
- Mac/Linux: Run `df -h` in terminal

---

## 🎓 Advanced Tips

### 1. Multiple Models for Different Tasks

You can install multiple models and switch between them:

```
llama3.2:3b     → Fast processing for simple documents
qwen2.5:14b     → High quality for complex documents  
llava:7b        → Vision analysis for images
```

**How to Switch:**
1. In AI Model Manager, select the model you want
2. Double-click it (or click "⭐ Set as Default")
3. Confirm the change
4. New files will use this model

### 2. Check What's Downloaded

In terminal, run:
```bash
ollama list
```

You'll see all installed models with their sizes and last used dates.

### 3. Clean Up Old Models

If you have many models eating disk space:

1. Open AI Model Manager
2. Select an unused model
3. Click "🗑️ Delete Model"
4. Confirm deletion
5. Repeat for other unused models

**Note:** You cannot delete the currently active default model.

### 4. Verify Model Quality

After pulling a new model, test it:

1. In AI Model Manager, set it as default
2. Process a test document
3. Check the quality of tags and descriptions
4. If quality is poor, try a larger model
5. If speed is slow, try a smaller model

---

## 📊 Choosing the Right Model

### Ask Yourself:

**Speed or Quality?**
- Need fast processing? → Use 1b or 3b models
- Need best results? → Use 14b or 32b models

**RAM Available?**
- 8GB RAM → Use 1b-3b models
- 16GB RAM → Use 3b-7b models
- 32GB RAM → Use 7b-14b models
- 64GB+ RAM → Any model works

**Document Type?**
- Simple text (emails, notes) → 3b models fine
- Complex documents (reports, legal) → 7b+ models
- Images and photos → llava models

---

## 🚀 Quick Start Example

**Scenario:** You want to try a faster model for testing.

**Steps:**

1. Click AI status button (bottom-right)
2. In the text box, type: `llama3.2:3b`
3. Click "📥 Pull Model"
4. Click "Yes" in the confirmation dialog
5. Wait 5-7 minutes (watch progress in Diagnostics)
6. When complete, double-click "llama3.2:3b" in the model list
7. Click "Yes" to set as default
8. Close the dialog
9. Process some files to test it!

---

## 💡 Pro Tips

1. **Pull models during breaks** - Large downloads take time, start them before lunch or meetings

2. **Test with small models first** - Don't wait 2 hours for a 70b model if a 3b works fine

3. **Use Copy Command for scripting** - You can pull multiple models at once in terminal:
   ```bash
   ollama pull llama3.2:3b && ollama pull qwen2.5:7b && ollama pull llava:7b
   ```

4. **Check available models** - Visit https://ollama.ai/library to see all available models

5. **Match model to task** - Vision tasks need llava, text tasks need llama/qwen

---

## 📞 Still Need Help?

### Check These Resources:

1. **Ollama Documentation:** https://github.com/ollama/ollama/blob/main/README.md
2. **Model Library:** https://ollama.ai/library
3. **AI Model Manager Diagnostics** - The diagnostics section shows detailed error messages

### Common Questions:

**Q: Can I use models from Hugging Face?**
A: Not directly. Ollama has its own model format. Check ollama.ai/library for compatible models.

**Q: Do I need internet to use models?**
A: You need internet to download (pull) models. Once downloaded, they work offline.

**Q: Can I use multiple models at once?**
A: The app uses one default model at a time, but you can switch between them easily.

**Q: Where are models stored?**
A: 
- Windows: `C:\Users\YourName\.ollama\models\`
- Mac: `~/.ollama/models/`
- Linux: `~/.ollama/models/`

---

## ✅ Success Checklist

After pulling a model, verify:

- [ ] Model appears in the Available Models list
- [ ] Model has a ✓ checkmark
- [ ] No error messages in Diagnostics
- [ ] "🔄 Refresh Status" shows model correctly
- [ ] Can set model as default (double-click works)
- [ ] Model works when processing files

If all checkboxes are ✓, you're ready to go! 🎉

---

## 📝 Summary

**To pull a model:**
1. Open AI Model Manager (click AI status button)
2. Type model name (e.g., `llama3.2:3b`)
3. Click "📥 Pull Model"
4. Wait for download (watch progress bar)
5. Model appears in list automatically
6. Double-click to set as default (optional)
7. Start processing files!

**That's it!** No terminal commands needed. The app handles everything for you.
