# Troubleshooting Guide - Quick Fixes

## 🚨 Common Errors & Solutions

### Error: "Ollama request failed: 404"

**What it means:** The LLM model isn't available

**Solution:**
```powershell
# 1. Check if Ollama is running
ollama list

# 2. If model not listed, download it
ollama pull llama3.2

# 3. Verify it's there
ollama list

# Should see:
# NAME        ID          SIZE    MODIFIED
# llama3.2:latest  abc123...   2.0 GB  X days ago
```

**If Ollama isn't installed:**
1. Download from: https://ollama.ai
2. Install and run
3. Download model: `ollama pull llama3.2`

---

### Error: "Cannot identify image file '...analysis.json'"

**What it means:** System tried to process a JSON metadata file as an image

**Solution:** This is now fixed! The system automatically excludes `.analysis.json` files.

**If you still see this:**
1. Clear the queue: Queue tab → Clear Queue
2. Remove watch folder temporarily
3. Restart application
4. Re-add watch folder

---

### Error: "OCR_NO_TEXT - No text extracted"

**What it means:** Image has no readable text (wallpaper, photo, artwork)

**Solution:** This is now handled automatically! Images without text are:
- Tagged as `no-text`, `visual-content`
- Saved to database with description
- Searchable in Results tab

**Nothing to fix!** This is expected behavior for visual-only images.

---

### Issue: "All files showing as 'failed'"

**Possible causes:**
1. Ollama not running
2. Model not downloaded
3. Wrong Tesseract path

**Solution:**

**Check 1: Ollama**
```powershell
ollama serve  # Start Ollama if not running
```

**Check 2: Model**
```powershell
ollama pull llama3.2
```

**Check 3: Tesseract**
1. Settings → OCR → Tesseract Path
2. Should be: `S:\Tesseract-OCR\tesseract.exe`
3. Click "Test" button to verify

---

### Issue: "Queue has files but processing shows 0/0/0"

**Cause:** Files might not be queued properly

**Solution:**
1. Queue tab → Check if files listed
2. If empty: Watch tab → Refresh Inventory
3. Files should auto-enqueue
4. Processing tab → Start Processing

---

### Issue: "Green dot stays on Queue tab but queue is empty"

**Cause:** Badge not updating

**Solution:**
1. Click Queue tab
2. Visual refresh should fix it
3. If not: Restart application

---

## 🔧 Settings to Check

### OCR Settings
- **Tesseract Path:** `S:\Tesseract-OCR\tesseract.exe`
- **Mode:** Fast (default) or Thorough
- **Language:** eng (English)

### Ollama Settings
- **Host:** `http://localhost:11434`
- **Model:** `llama3.2`
- **Temperature:** 0.4 (default)
- **Max Tokens:** 270 (default)

### Watch Settings
- **Folders:** At least one folder added
- **Recursive:** Off (unless you want subdirectories)

---

## 🎯 Quick Health Check

**Run these checks to verify system:**

**1. Ollama Running?**
```powershell
# Open browser to:
http://localhost:11434

# Should see:
"Ollama is running"
```

**2. Model Downloaded?**
```powershell
ollama list

# Should show llama3.2
```

**3. Tesseract Working?**
```powershell
S:\Tesseract-OCR\tesseract.exe --version

# Should show version info
```

**4. Database Created?**
```powershell
# Check if file exists:
dir S:\insite-app\data\previewless.db

# Should show file
```

---

## 📝 Logs & Diagnostics

### Check Log Files

**Location:** `S:\insite-app\logs\`

**Latest log:**
```powershell
# Find most recent log
dir S:\insite-app\logs\ | sort LastWriteTime | select -last 1

# View it
notepad S:\insite-app\logs\app_2025-10-13_123456.log
```

**Look for:**
- `ERROR` messages (red flags)
- `WARNING` messages (yellow flags)
- `Ollama request failed` (model issues)
- `OCR failed` (Tesseract issues)

---

### Enable Debug Mode

**In `config/settings.json`:**
```json
{
  "logging": {
    "level": "DEBUG",  // Change from INFO
    ...
  }
}
```

**Restart app** - logs will be more verbose

---

## 🔄 Reset & Clean Start

### Nuclear Option: Fresh Start

**If everything is broken:**

```powershell
# 1. Close application

# 2. Backup database (optional)
copy S:\insite-app\data\previewless.db S:\insite-app\data\previewless.db.backup

# 3. Delete database
del S:\insite-app\data\previewless.db

# 4. Delete logs
del S:\insite-app\logs\*.log

# 5. Restart application
python main.py

# Database will be recreated fresh
```

---

## 🆘 Still Having Issues?

### Collect This Information:

1. **Error message** (exact text)
2. **Log file** (last 50 lines)
3. **System info:**
   ```powershell
   python --version
   ollama version
   S:\Tesseract-OCR\tesseract.exe --version
   ```
4. **What you were doing** when error occurred
5. **File type** you were processing

### Check Documentation:

- `docs/WORKFLOW_GUIDE.md` - Complete workflow
- `docs/ERROR_HANDLING_IMPROVEMENTS.md` - Detailed error info
- `docs/CHECKLIST.md` - Setup verification

---

## ✅ Expected Behavior

### Normal Processing

**Watch Tab:**
```
Total Files: 100
Unanalyzed: 50
```

**Queue Tab with Badge:**
```
📋 Queue 🟢  (glowing green dot)
```

**Processing:**
```
Processed: 1
Failed: 0
Skipped: 0
```

**Results Tab:**
```
150 files found
Search: <type to search>
```

### Normal Wallpaper Processing

**These are NOT errors:**
- "No text found in wallpaper.jpg, treating as image without text"
- Tags: `image, no-text, visual-content`
- Status: Completed ✅

---

## 🎉 Success Indicators

**You know it's working when:**

✅ Green dot appears on Queue tab  
✅ Files process without errors  
✅ Review dialog shows for each file  
✅ Results tab shows completed files  
✅ Search returns results  
✅ No red error messages in console  

**Congratulations! You're processing successfully!** 🎊
