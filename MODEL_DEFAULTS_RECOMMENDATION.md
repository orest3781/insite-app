# Model Defaults Analysis - Vision, OCR, Text & Tags

## 📋 Current State

Based on my analysis of the codebase, here's what I found:

### Current Model Configuration

**In `config/settings.json`:**
```json
"ollama": {
  "host": "http://localhost:11434",
  "default_model": "llama3.2",     ← Only ONE default (used for text/tags)
  "temperature": 0.4,
  "max_tokens": 270
}
```

**Current Behavior:**
- ✅ **LLM Model (Text/Tags):** Has default (`llama3.2`)
- ⚠️ **Vision Model (Images):** Auto-detected from available models (first match)
- ❌ **OCR (Documents):** Fixed to Tesseract (no Ollama model)
- ❌ **No separate defaults** for each task type

---

## 🎯 Recommendation: YES, Add Separate Defaults!

You **absolutely should** have separate configurable defaults for:
1. **Vision Model** - For image analysis (currently auto-detected)
2. **Text/Tags Model** - For descriptions and classifications (currently `llama3.2`)
3. **OCR Model** - For document text extraction (currently Tesseract only)

### Why This Matters

**Current Problem:**
```
Vision Model:  Auto-selected (user can't choose preference)
Text Model:    Always llama3.2 (can't be changed without config file edit)
               User has to double-click in dialog to change it
               BUT changes don't persist!

Result: Users can't easily customize which model to use for what
```

**With Separate Defaults:**
```
Vision Model:  User can set their preferred vision model ✓
               Falls back if not available ✓
               Persists in config ✓

Text Model:    User can set preferred LLM ✓
               Used for descriptions and classifications ✓
               Persists in config ✓

OCR Model:     Could support Ollama OCR if available ✓
               Fallback to Tesseract ✓
```

---

## 🔧 Implementation Plan

### Step 1: Update Config Structure

**File:** `config/settings.json`

**Before:**
```json
"ollama": {
  "host": "http://localhost:11434",
  "default_model": "llama3.2",
  "temperature": 0.4,
  "max_tokens": 270
}
```

**After:**
```json
"ollama": {
  "host": "http://localhost:11434",
  "default_model_text": "llama3.2",      ← For descriptions, classifications
  "default_model_vision": "qwen2.5vl:7b", ← For image analysis
  "default_model_ocr": null,               ← For OCR (null = use Tesseract)
  "temperature": 0.4,
  "max_tokens": 270,
  "fallback_models": {                     ← Fallback options
    "vision": ["llava:7b", "llava:34b"],
    "text": ["qwen2.5:14b", "mistral:7b"],
    "ocr": ["tesseract"]
  }
}
```

### Step 2: Update LLMAdapter

**File:** `src/services/llm_adapter.py`

```python
def __init__(self, config_manager):
    self.config = config_manager
    
    # Host and connection
    self.host = self.config.get('ollama_host', 'http://localhost:11434')
    
    # Separate defaults for each use case
    self.model_text = self.config.get('ollama_default_model_text', 'llama3.2')
    self.model_vision = self.config.get('ollama_default_model_vision', 'qwen2.5vl:7b')
    self.model_ocr = self.config.get('ollama_default_model_ocr', None)  # None = Tesseract
    
    # Fallbacks
    self.fallback_models = self.config.get('ollama_fallback_models', {
        'vision': ['llava:7b', 'llava:34b'],
        'text': ['qwen2.5:14b', 'mistral:7b'],
        'ocr': ['tesseract']
    })
    
    # Keep for backward compatibility
    self.model_name = self.model_text
    
    logger.info(f"Models: text={self.model_text}, vision={self.model_vision}, ocr={self.model_ocr}")
```

### Step 3: Update Settings Dialog

**File:** `src/ui/settings_dialog.py`

Add three separate dropdowns:
```python
# Text/Tags Model
self.ollama_model_text = QComboBox()
self.ollama_model_text.addItems(available_models)

# Vision Model
self.ollama_model_vision = QComboBox()
self.ollama_model_vision.addItems(available_models)

# OCR Model
self.ollama_model_ocr = QComboBox()
self.ollama_model_ocr.addItem("Tesseract (Default)")
self.ollama_model_ocr.addItems(available_models)
```

### Step 4: Update AI Model Manager Dialog

**File:** `src/ui/ai_model_dialog.py`

Show all three defaults clearly:
```
Connection Settings & Model Usage
─────────────────────────────────────
Ollama Host: http://localhost:11434

Default Models:
🖼️  Vision (images):        [qwen2.5vl:7b ⭐ default]
🤖 Text (descriptions):     [llama3.2 ⭐ default]
📄 OCR (documents):         [Tesseract]

[Set as Default] buttons for each type
```

### Step 5: Update Processing Logic

**File:** `src/services/processing_orchestrator.py`

```python
# Use the right model for the right job
if task == 'vision_analysis':
    model = self.llm_adapter.get_vision_model()  # Gets model_vision
elif task == 'text_generation':
    model = self.llm_adapter.get_text_model()    # Gets model_text
elif task == 'ocr':
    model = self.llm_adapter.get_ocr_model()     # Gets Tesseract or model_ocr
```

---

## 📊 What Each Model Should Do

### Vision Model (for images)
- **Purpose:** Analyze images, extract visual information
- **Best Models:**
  - `qwen2.5vl:7b` - Best overall
  - `llava:7b` - Good alternative
  - `llava:34b` - Highest quality (slow)
- **Current:** Auto-detected (not user-configurable)
- **Should:** Be user-selectable and persistent

### Text Model (for descriptions & tags)
- **Purpose:** Generate descriptions, classify, extract tags
- **Best Models:**
  - `llama3.2` - Current default, good for instructions
  - `qwen2.5:14b` - Better quality, slower
  - `mistral:7b` - Fast alternative
- **Current:** Hardcoded to `llama3.2`
- **Should:** Be user-selectable and configurable

### OCR Model (for documents)
- **Purpose:** Extract text from images/documents
- **Options:**
  - `Tesseract` - Current default, fast, no internet needed
  - `qwen2.5vl:7b` - Could do OCR, but overkill
  - Could have Ollama-based OCR in future
- **Current:** Always Tesseract
- **Should:** Stay Tesseract by default, but configurable

---

## ✨ Benefits of Separate Defaults

### For Users
✅ Can optimize for their hardware
- Slow computer? Use smaller models
- Powerful GPU? Use larger models

✅ Can optimize for quality vs. speed
- Need speed? Use fast models
- Need quality? Use larger models

✅ Can use different models for different tasks
- Vision: `llava:7b` (fast)
- Text: `qwen2.5:14b` (highest quality)
- OCR: Tesseract (specialized)

✅ Settings persist
- Changes saved to config
- Survive app restart
- No confusion

### For Developers
✅ More flexible architecture
✅ Easier to add new task types
✅ Clearer code intent
✅ Better error handling per task

---

## 🎯 Priority Implementation

### Phase 1: Critical (1-2 hours)
- [ ] Update config structure (add three defaults)
- [ ] Update LLMAdapter to use separate defaults
- [ ] Update Settings Dialog UI
- [ ] Make defaults actually persist (fixing the broken feature!)

### Phase 2: Enhancement (1-2 hours)
- [ ] Update AI Model Manager dialog
- [ ] Update processing logic
- [ ] Add fallback logic
- [ ] Test all combinations

### Phase 3: Polish (optional)
- [ ] Add presets ("Balanced", "Quality", "Speed")
- [ ] Add recommendations
- [ ] Add validation

---

## 📝 Configuration Examples

### Example 1: Balanced Setup
```json
{
  "default_model_text": "llama3.2",      // Fast
  "default_model_vision": "llava:7b",    // Balanced
  "default_model_ocr": null              // Tesseract
}
```

### Example 2: Quality Setup
```json
{
  "default_model_text": "qwen2.5:14b",   // High quality
  "default_model_vision": "qwen2.5vl:7b", // High quality
  "default_model_ocr": null              // Tesseract
}
```

### Example 3: Speed Setup
```json
{
  "default_model_text": "mistral:7b",    // Fast
  "default_model_vision": "llava:7b",    // Fast
  "default_model_ocr": null              // Tesseract
}
```

---

## 🔄 Backward Compatibility

The implementation should:
- ✅ Support old `default_model` setting (migrate to `default_model_text`)
- ✅ Auto-detect if only one default is set
- ✅ Fall back to Tesseract for OCR
- ✅ Handle missing models gracefully

---

## 🧪 Testing Checklist

- [ ] Config loads correctly
- [ ] Defaults persist on restart
- [ ] Can change vision model
- [ ] Can change text model
- [ ] OCR works with Tesseract
- [ ] Fallback logic works
- [ ] Old config files migrate correctly
- [ ] No models set uses reasonable defaults
- [ ] Invalid models gracefully downgrade to fallback

---

## 🎓 Why This Matters

Right now, users are confused:
```
"Why do some images not work?"
→ Because vision model isn't configured

"Can I use a different model for descriptions?"
→ Yes, but only via config file or double-clicking (which doesn't save!)

"What model should I use?"
→ You have to guess...
```

With separate defaults:
```
"Want better image analysis?"
→ Settings → Vision Model → Choose → Done ✓

"Want faster descriptions?"
→ Settings → Text Model → Choose faster one → Done ✓

"Which model am I using?"
→ Dialog shows all three clearly → Obvious ✓
```

---

## Summary

**Your Question:** Should there be defaults for vision, OCR, and text/tags?

**Answer:** **YES! Absolutely.**

**Current State:** Only text has a "default" (hardcoded), vision is auto-detected, OCR is fixed to Tesseract

**Recommendation:** Implement three separate configurable defaults that:
- Show clearly in the UI
- Are user-selectable
- Persist to config
- Have sensible fallbacks
- Work for different use cases

**Effort:** 2-4 hours total (depends on how thorough you want to be)

**Impact:** Major improvement to user experience and flexibility

This should be **Priority 2** after fixing the config persistence bug in the AI Model Manager!
