# ⚡ Quick Reference: Three Model Defaults

## 🎯 What Was Built

Three separate, configurable model defaults (Vision, OCR, Text) in the AI Model Manager with auto-save and intelligent fallback.

## 📍 Where to Find It

**UI Location:** AI Model Manager Dialog → "Model Type Defaults (Optional)" section
**Config Location:** `config/settings.json` under `"ollama"` section

## 🎮 How to Use

### Setting Defaults (User Guide)

1. **Open AI Model Manager**
   - Click model button in main app

2. **Find "Model Type Defaults" section**
   - Located between model list and diagnostics
   - Shows: 👁️ Vision, 📝 OCR, 📄 Text

3. **Select models from dropdowns**
   - Each shows all available models
   - Each can be set to "(Use general default)"
   - Changes auto-save instantly

### Configuration Examples

**Example 1: Set Vision Model**
```
👁️ Vision: [qwen2.5vl:7b ▼]
  Image processing will use qwen2.5vl:7b
```

**Example 2: Set OCR Model**
```
📝 OCR: [llama3.2:7b ▼]
  Text classification will use llama3.2:7b
```

**Example 3: Set Text Model**
```
📄 Text: [llama3.2 ▼]
  Description generation will use llama3.2
```

## 💻 How It Works (Technical)

### Model Selection Priority

```
Vision Processing:
  1. default_model_vision (if set)
  2. Standard vision models (qwen2.5vl:7b, llava:7b, etc.)
  3. General default

Text Classification:
  1. default_model_ocr (if set)
  2. default_model_text (if set)
  3. General default

Description Generation:
  1. default_model_text (if set)
  2. General default
```

### Configuration Structure

**`config/settings.json`:**
```json
{
  "ollama": {
    "default_model": "llama3.2",
    "default_model_vision": "qwen2.5vl:7b",  // NEW
    "default_model_ocr": "llama3.2:7b",      // NEW
    "default_model_text": "llama3.2",        // NEW
    ...
  }
}
```

### API Usage

```python
# Get defaults
vision_model = adapter.default_model_vision
ocr_model = adapter.default_model_ocr
text_model = adapter.default_model_text

# Set defaults (auto-saves)
adapter.config.set('ollama_default_model_vision', 'qwen2.5vl:7b', save=True)

# Use in processing (automatic)
adapter.analyze_image_vision(path)        # Uses vision default
adapter.generate_classification(text)     # Uses OCR default → text default
adapter.generate_description(text, tags)  # Uses text default
```

## 📊 Files Changed

| File | What Changed | Why |
|------|-------------|-----|
| `config/settings.json` | Added 3 new fields | Storage |
| `src/core/config.py` | Updated schema | Config management |
| `src/services/llm_adapter.py` | Enhanced model selection | Backend logic |
| `src/ui/ai_model_dialog.py` | New UI section + methods | User interface |

## ✅ Features

- ✅ **Three Independent Defaults** - Vision, OCR, Text
- ✅ **Auto-Save** - Changes persist instantly
- ✅ **Intelligent Fallback** - Always has a model to use
- ✅ **Backward Compatible** - Doesn't break existing code
- ✅ **Clean UI** - Simple dropdowns, easy to understand
- ✅ **Diagnostic Feedback** - Shows what's happening
- ✅ **Real-time Updates** - Reflects model changes immediately

## 🧪 Quick Test

### 5-Minute Test
1. Open AI Model Manager
2. See "Model Type Defaults" section
3. Select a vision model
4. See diagnostic: "✅ Vision model default set to: ..."
5. Close/reopen → verify it persisted

### 15-Minute Test
1. Set all three defaults
2. Close app
3. Reopen app
4. Verify all three still set
5. Check `config/settings.json`

## ⚙️ Configuration Options

### Option 1: Use General Default (Default)
```json
"default_model_vision": null,
"default_model_ocr": null,
"default_model_text": null
```
→ Everything uses general default

### Option 2: Specialized Vision
```json
"default_model_vision": "qwen2.5vl:7b",
"default_model_ocr": null,
"default_model_text": null
```
→ Images use qwen2.5vl:7b, text uses general default

### Option 3: Full Specialization
```json
"default_model_vision": "qwen2.5vl:7b",
"default_model_ocr": "llama3.2:7b",
"default_model_text": "llama3.2"
```
→ Each task uses optimized model

## 🎯 Use Cases

| Use Case | Config |
|----------|--------|
| **General Purpose** | All null (use general default) |
| **Image Focus** | Vision set, OCR/Text null |
| **Text Focus** | Text set, Vision null, OCR null |
| **Mixed** | Vision + Text set, OCR null |
| **Maximum Quality** | All set to largest models |
| **Speed Optimized** | All set to smallest models |

## 🔍 Troubleshooting

### Models not appearing in dropdowns?
- Pull models first: Use "How to Pull Models" button
- Or: `ollama pull qwen2.5vl:7b`

### Changes not saving?
- Check Ollama service is running
- Look for error in diagnostics section
- Restart app and try again

### Wrong model being used?
- Check which default is set in dialog
- Review diagnostics messages
- Verify config file has correct value

## 📞 Need Help?

**See detailed guides:**
- `THREE_MODEL_DEFAULTS_USER_GUIDE.md` - Full user guide
- `THREE_MODEL_DEFAULTS_IMPLEMENTATION.md` - Technical details
- `FEATURE_COMPLETE_THREE_DEFAULTS.md` - Executive summary

## ✨ Summary

- **What:** Three separate model defaults (Vision, OCR, Text)
- **Where:** AI Model Manager → "Model Type Defaults" section
- **How:** Select from dropdowns, auto-saves
- **Why:** Optimize model selection per task type
- **Status:** ✅ Production ready

---

**Feature Status: ✅ COMPLETE AND OPERATIONAL**

