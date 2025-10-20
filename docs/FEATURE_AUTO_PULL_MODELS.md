# Feature: Auto-Pull Ollama Models

**Date:** October 13, 2025  
**Status:** ✅ IMPLEMENTED

---

## 🎯 Overview

Models are now **automatically downloaded** when not found! No more manual intervention needed.

---

## ✨ How It Works

### Before (Manual Process)
```
1. User tries to process file
2. Error: "Model 'llama3.2' not found"
3. User opens terminal
4. User runs: ollama pull llama3.2
5. User waits for download
6. User retries processing
```

### After (Automatic)
```
1. User tries to process file
2. System detects model missing
3. System automatically downloads model (shows progress in logs)
4. System retries processing
5. Success! ✅
```

---

## 🔧 Implementation Details

### New Method: `pull_model()`

Added to `OllamaAdapter` class:

```python
def pull_model(self, model_name: Optional[str] = None, timeout: int = 600) -> bool:
    """
    Pull (download) a model from Ollama.
    
    Args:
        model_name: Model name to pull (default: configured model)
        timeout: Timeout in seconds (default: 600 = 10 minutes)
    
    Returns:
        True if model was pulled successfully
    """
```

**Features:**
- Streams download progress
- Logs status updates
- 10-minute timeout (adjustable)
- Returns True on success

---

### Auto-Pull Integration

When a 404 error occurs (model not found):

1. **Check config:** Is `ollama_auto_pull_models` enabled? (default: `true`)
2. **Attempt pull:** Download the missing model
3. **Retry request:** If pull succeeds, retry the original request automatically
4. **Return result:** Either success (with `auto_pulled: true` metadata) or error

**Code Flow:**
```python
if response.status_code == 404:
    auto_pull = self.config.get('ollama_auto_pull_models', True)
    
    if auto_pull:
        if self.pull_model(self.model_name):
            # Retry the request with newly pulled model
            # Return success!
        else:
            # Pull failed, return error
```

---

## 📋 Configuration

### New Setting in `settings.json`

```json
"ollama": {
  "host": "http://localhost:11434",
  "default_model": "llama3.2",
  "temperature": 0.4,
  "max_tokens": 270,
  "top_p": 0.7,
  "timeout_s": 30,
  "auto_pull_models": true  ← NEW!
}
```

### Configuration Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `auto_pull_models` | boolean | `true` | Automatically download missing models |

**To disable auto-pull:**
```json
"auto_pull_models": false
```

---

## 📊 User Experience

### First-Time Processing with Missing Model

**With auto-pull enabled (default):**

```
[INFO] Processing: wallpaper.jpg
[INFO] OCR completed: 150 chars
[ERROR] Ollama request failed: 404
[INFO] Model 'llama3.2' not found. Attempting auto-pull...
[INFO] Pulling model 'llama3.2' from Ollama (this may take several minutes)...
[INFO] Pull status: pulling manifest
[INFO] Pull status: downloading sha256:...
[INFO] Pull status: verifying sha256
[INFO] Pull status: success
[INFO] Successfully pulled model 'llama3.2'
[INFO] Model 'llama3.2' pulled successfully. Retrying request...
[INFO] Retry successful after auto-pull
[INFO] Classification: wallpaper, scenic, nature
✅ Success!
```

**With auto-pull disabled:**

```
[INFO] Processing: wallpaper.jpg
[INFO] OCR completed: 150 chars
[ERROR] Ollama request failed: 404
[ERROR] Model 'llama3.2' not found. Please ensure Ollama is running 
        and the model is downloaded: ollama pull llama3.2
❌ Failed
```

---

## 🚀 Benefits

### For Users
✅ **Zero manual intervention** - Models download automatically  
✅ **Seamless experience** - First run "just works"  
✅ **No terminal commands** - Everything handled in background  
✅ **Progress visibility** - Status logged in real-time  

### For Support
✅ **Fewer support tickets** - "Model not found" errors eliminated  
✅ **Better onboarding** - New users don't need setup instructions  
✅ **Self-healing** - System recovers from missing models automatically  

---

## ⚙️ Technical Details

### Download Times (Typical)

| Model | Size | Download Time (100 Mbps) |
|-------|------|--------------------------|
| llama3.2 | ~2 GB | ~3-5 minutes |
| llama2 | ~3.8 GB | ~5-8 minutes |
| mistral | ~4.1 GB | ~6-9 minutes |

### Timeout Configuration

Default timeout: **600 seconds (10 minutes)**

To change timeout, modify the method call:
```python
self.pull_model(self.model_name, timeout=900)  # 15 minutes
```

### Progress Logging

The pull operation logs status updates:
```
[INFO] Pull status: pulling manifest
[INFO] Pull status: downloading sha256:abc123...
[INFO] Pull status: verifying sha256
[INFO] Pull status: success
```

---

## 🔒 Safety Features

### Network Error Handling
- Catches timeouts gracefully
- Returns `False` on failure
- Falls back to error message

### Timeout Protection
- Default 10-minute timeout prevents hanging
- Configurable for slow connections
- Logs timeout clearly

### Retry Logic
- Only retries if pull succeeds
- Uses same payload as original request
- Metadata marks auto-pulled requests

---

## 📝 Metadata Tracking

Successful auto-pull adds metadata:

```python
{
  'auto_pulled': True,  # Indicates model was auto-downloaded
  'duration_ns': 12345678,
  'prompt_eval_count': 45,
  'eval_count': 89
}
```

This helps track:
- Which requests triggered auto-pulls
- Performance impact of auto-pulling
- Model download frequency

---

## 🧪 Testing Scenarios

### Test 1: Fresh Install (No Models)
```
Prerequisites: Ollama installed, no models pulled
Steps:
  1. Start app
  2. Process first file
Expected:
  ✅ Model auto-downloads
  ✅ Processing succeeds
  ✅ Logs show pull progress
```

### Test 2: Model Changed in Settings
```
Prerequisites: llama2 installed, settings changed to mistral
Steps:
  1. Change default_model to "mistral"
  2. Process file
Expected:
  ✅ mistral auto-downloads
  ✅ Processing succeeds with mistral
```

### Test 3: Auto-Pull Disabled
```
Prerequisites: auto_pull_models: false
Steps:
  1. Process file with missing model
Expected:
  ❌ Error message
  📝 Manual pull instructions shown
```

### Test 4: Network Timeout
```
Prerequisites: Very slow or no internet
Steps:
  1. Try to process file
Expected:
  ❌ Timeout after 10 minutes
  📝 Error logged
  ⚠️ Original error message shown
```

---

## 🎛️ Settings UI Integration

To add to Settings dialog (future enhancement):

```python
# In LLM tab
self.auto_pull_checkbox = QCheckBox("Automatically download missing models")
self.auto_pull_checkbox.setChecked(
    self.config.get('ollama_auto_pull_models', True)
)
self.auto_pull_checkbox.setToolTip(
    "When enabled, missing models will be downloaded automatically. "
    "This may take several minutes on first use."
)
```

---

## 📈 Performance Impact

### First Request with Missing Model
- **Extra time:** Model download time (3-10 minutes typically)
- **User impact:** One-time delay, then normal speed
- **Benefit:** No manual intervention required

### Subsequent Requests
- **Extra time:** 0 seconds (model already cached)
- **User impact:** None
- **Benefit:** Seamless operation

---

## 🔄 Comparison: Before vs After

### Before Auto-Pull

**User Experience:**
```
Process file → Error → Terminal → ollama pull → Wait → Retry → Success
⏱️ Time: 5-10 minutes + manual steps
😞 Frustration: High
```

**Developer Experience:**
```
Support ticket → Explain ollama pull → Wait for user → Close ticket
⏱️ Time: 15-30 minutes per user
😞 Frustration: High
```

### After Auto-Pull

**User Experience:**
```
Process file → Wait (auto-download) → Success
⏱️ Time: 5-10 minutes (automated)
😊 Frustration: None
```

**Developer Experience:**
```
No tickets for missing models!
⏱️ Time: 0 minutes
😊 Frustration: None
```

---

## 🐛 Troubleshooting

### Problem: Auto-pull fails

**Possible causes:**
1. No internet connection
2. Ollama service not running
3. Disk space full
4. Firewall blocking downloads

**Solution:**
Check logs for specific error, manually run:
```bash
ollama pull llama3.2
```

### Problem: Auto-pull takes too long

**Possible causes:**
1. Slow internet connection
2. Large model size
3. Server congestion

**Solution:**
Increase timeout or pull manually:
```python
# In code
self.pull_model(timeout=1800)  # 30 minutes
```

### Problem: Want to disable auto-pull

**Solution:**
Edit `config/settings.json`:
```json
"auto_pull_models": false
```

---

## ✅ Summary

### What Changed
- ✅ Added `pull_model()` method to `OllamaAdapter`
- ✅ Integrated auto-pull into error handling
- ✅ Added `auto_pull_models` setting (default: `true`)
- ✅ Automatic retry after successful pull

### Files Modified
1. **`src/services/llm_adapter.py`** (+70 lines)
   - New `pull_model()` method
   - Enhanced error handling with auto-pull
   
2. **`config/settings.json`** (+1 line)
   - Added `"auto_pull_models": true`

### User Impact
- 🎉 **Zero-config first run** - Models download automatically
- ⏱️ **One-time delay** - First request downloads model
- 🔄 **Seamless thereafter** - All subsequent requests fast
- 🛠️ **Optional disable** - Can turn off if desired

---

**Status:** ✅ **PRODUCTION READY**

Models will now auto-download! Just restart the app and try processing. 🚀
