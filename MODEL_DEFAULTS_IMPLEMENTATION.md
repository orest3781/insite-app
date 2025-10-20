# Model Defaults - Quick Implementation Guide

## TL;DR

**YES**, you should add separate defaults for:
- 🖼️ Vision (image analysis)
- 🤖 Text/Tags (descriptions & classification)
- 📄 OCR (document text)

Currently only Text has a default, and it doesn't persist!

---

## Quick Fix (30 minutes)

Update `config/settings.json`:

```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "default_model_text": "llama3.2",
    "default_model_vision": "qwen2.5vl:7b",
    "default_model_ocr": null,
    "temperature": 0.4,
    "max_tokens": 270
  }
}
```

Update `src/services/llm_adapter.py`:

```python
def __init__(self, config_manager):
    self.config = config_manager
    self.host = self.config.get('ollama_host', 'http://localhost:11434')
    
    # Three separate defaults
    self.model_text = self.config.get('ollama_default_model_text', 'llama3.2')
    self.model_vision = self.config.get('ollama_default_model_vision', 'qwen2.5vl:7b')
    self.model_ocr = self.config.get('ollama_default_model_ocr', None)
    
    # Backward compatibility
    self.model_name = self.model_text
```

---

## Full Implementation (2-3 hours)

### 1. Config Structure ✓ (10 min)
**File:** `config/settings.json`

```json
"ollama": {
  "host": "http://localhost:11434",
  "default_model_text": "llama3.2",      ← For descriptions
  "default_model_vision": "qwen2.5vl:7b", ← For images
  "default_model_ocr": null,              ← For documents (null=Tesseract)
  "temperature": 0.4,
  "max_tokens": 270,
  "fallback_models": {
    "vision": ["llava:7b", "llava:34b"],
    "text": ["qwen2.5:14b", "mistral:7b"]
  }
}
```

### 2. Update LLMAdapter ✓ (20 min)
**File:** `src/services/llm_adapter.py`

Add these methods to the `OllamaAdapter` class:

```python
def get_text_model(self) -> str:
    """Get model for text generation (descriptions, classifications)."""
    available = self.list_models()
    
    # Try primary choice
    if self.model_text in available:
        return self.model_text
    
    # Try fallbacks
    fallbacks = self.config.get('ollama_fallback_models.text', ['qwen2.5:14b', 'mistral:7b'])
    for model in fallbacks:
        if model in available:
            logger.info(f"Text model {self.model_text} not found, using fallback: {model}")
            return model
    
    # Last resort
    logger.warning("No suitable text model found, using first available")
    return available[0] if available else self.model_text

def get_vision_model(self) -> str:
    """Get model for vision tasks (image analysis)."""
    available = self.list_models()
    
    # Try primary choice
    if self.model_vision in available:
        return self.model_vision
    
    # Try fallbacks
    fallbacks = self.config.get('ollama_fallback_models.vision', ['llava:7b', 'llava:34b'])
    for model in fallbacks:
        if model in available:
            logger.info(f"Vision model {self.model_vision} not found, using fallback: {model}")
            return model
    
    # Last resort - find any vision model
    vision_keywords = ['vision', 'vl', 'llava', 'qwen2.5vl', 'qwen2-vl', 'minicpm-v']
    for model in available:
        if any(kw in model.lower() for kw in vision_keywords):
            logger.warning(f"Vision model {self.model_vision} not found, using: {model}")
            return model
    
    # Ultimate fallback - use text model as vision (not ideal but works)
    logger.warning("No vision models found, using text model as fallback")
    return self.get_text_model()

def get_ocr_model(self) -> Optional[str]:
    """Get model for OCR (None = use Tesseract)."""
    if self.model_ocr is None:
        return None  # Use Tesseract
    
    available = self.list_models()
    if self.model_ocr in available:
        return self.model_ocr
    
    logger.warning(f"OCR model {self.model_ocr} not found, falling back to Tesseract")
    return None
```

### 3. Update Settings Dialog ✓ (30 min)
**File:** `src/ui/settings_dialog.py`

In `_create_ollama_group()` method:

```python
def _create_ollama_group(self) -> QGroupBox:
    """Create Ollama settings group."""
    group = QGroupBox("Ollama LLM Settings")
    layout = QFormLayout(group)
    
    # Host
    self.ollama_host = QLineEdit()
    self.ollama_host.setText(self.config.get("ollama.host", "http://localhost:11434"))
    layout.addRow("Host:", self.ollama_host)
    
    # Get available models
    try:
        adapter = OllamaAdapter(self.config)
        available_models = adapter.list_models()
    except:
        available_models = ["llama3.2", "qwen2.5:14b", "qwen2.5vl:7b", "llava:7b"]
    
    # TEXT MODEL (descriptions, classifications)
    self.ollama_model_text = QComboBox()
    self.ollama_model_text.addItems(available_models)
    current_text = self.config.get("ollama.default_model_text", "llama3.2")
    index = self.ollama_model_text.findText(current_text)
    if index >= 0:
        self.ollama_model_text.setCurrentIndex(index)
    self.ollama_model_text.setToolTip("Model for generating descriptions and classifications")
    layout.addRow("🤖 Text Model:", self.ollama_model_text)
    
    # VISION MODEL (image analysis)
    self.ollama_model_vision = QComboBox()
    self.ollama_model_vision.addItems(available_models)
    current_vision = self.config.get("ollama.default_model_vision", "qwen2.5vl:7b")
    index = self.ollama_model_vision.findText(current_vision)
    if index >= 0:
        self.ollama_model_vision.setCurrentIndex(index)
    self.ollama_model_vision.setToolTip("Model for analyzing images")
    layout.addRow("🖼️ Vision Model:", self.ollama_model_vision)
    
    # OCR MODEL (document text extraction)
    self.ollama_model_ocr = QComboBox()
    self.ollama_model_ocr.addItem("Tesseract (Default - Fast)")
    self.ollama_model_ocr.addItems([f"{m} (Ollama)" for m in available_models])
    current_ocr = self.config.get("ollama.default_model_ocr", None)
    if current_ocr:
        index = self.ollama_model_ocr.findText(f"{current_ocr} (Ollama)")
        if index >= 0:
            self.ollama_model_ocr.setCurrentIndex(index)
    self.ollama_model_ocr.setToolTip("Model for OCR - Tesseract recommended")
    layout.addRow("📄 OCR Model:", self.ollama_model_ocr)
    
    # Temperature
    self.ollama_temperature = QDoubleSpinBox()
    self.ollama_temperature.setMinimum(0.0)
    self.ollama_temperature.setMaximum(1.0)
    self.ollama_temperature.setSingleStep(0.1)
    self.ollama_temperature.setValue(self.config.get("ollama.temperature", 0.4))
    layout.addRow("Temperature:", self.ollama_temperature)
    
    # Max tokens
    self.ollama_max_tokens = QSpinBox()
    self.ollama_max_tokens.setMinimum(100)
    self.ollama_max_tokens.setMaximum(2000)
    self.ollama_max_tokens.setValue(self.config.get("ollama.max_tokens", 270))
    layout.addRow("Max Tokens:", self.ollama_max_tokens)
    
    return group
```

Then in `save_settings()`:

```python
settings["ollama.host"] = self.ollama_host.text()
settings["ollama.default_model_text"] = self.ollama_model_text.currentText()
settings["ollama.default_model_vision"] = self.ollama_model_vision.currentText()

# Parse OCR model (remove " (Default - Fast)" or " (Ollama)" suffix)
ocr_text = self.ollama_model_ocr.currentText()
if "Tesseract" in ocr_text:
    settings["ollama.default_model_ocr"] = None
else:
    settings["ollama.default_model_ocr"] = ocr_text.replace(" (Ollama)", "")

settings["ollama.temperature"] = self.ollama_temperature.value()
settings["ollama.max_tokens"] = self.ollama_max_tokens.value()
```

### 4. Update AI Model Manager Dialog ✓ (20 min)
**File:** `src/ui/ai_model_dialog.py`

In `_create_connection_group()`:

```python
# Replace the model usage section with:
self.text_model_label = QLabel()
self.text_model_label.setWordWrap(True)
layout.addRow("🤖 Text (descriptions):", self.text_model_label)

self.vision_model_label = QLabel()
self.vision_model_label.setWordWrap(True)
layout.addRow("🖼️ Vision (images):", self.vision_model_label)

self.ocr_model_label = QLabel()
self.ocr_model_label.setWordWrap(True)
layout.addRow("📄 OCR (documents):", self.ocr_model_label)
```

In `_on_status_checked()`:

```python
# Update labels to show all three
self.text_model_label.setText(f"<b>{self.adapter.model_text}</b> (for descriptions, classifications)")
self.vision_model_label.setText(f"<b>{self.adapter.model_vision}</b> (for image analysis)")
self.ocr_model_label.setText("<b>Tesseract</b> (external, optimized for document text)")
```

### 5. Update Processing Orchestrator ✓ (30 min)
**File:** `src/services/processing_orchestrator.py`

Wherever you call the LLM adapter:

```python
# Instead of:
result = self.llm_adapter.generate_description(image_data)

# Use:
if task_type == 'vision':
    model = self.llm_adapter.get_vision_model()
    result = self.llm_adapter.generate_description(image_data, model=model)
elif task_type == 'text':
    model = self.llm_adapter.get_text_model()
    result = self.llm_adapter.generate_classification(tags_data, model=model)
elif task_type == 'ocr':
    model = self.llm_adapter.get_ocr_model()
    if model is None:
        result = tesseract_process(image_data)
    else:
        result = self.llm_adapter.process_ocr(image_data, model=model)
```

### 6. Add Set-as-Default Buttons ✓ (20 min)
**File:** `src/ui/ai_model_dialog.py`

Add buttons in the model group:

```python
# In model list section, add this layout:
button_layout = QHBoxLayout()

set_text_btn = QPushButton("⭐ Set as Text Default")
set_text_btn.clicked.connect(lambda: self._set_model_default('text'))
button_layout.addWidget(set_text_btn)

set_vision_btn = QPushButton("⭐ Set as Vision Default")
set_vision_btn.clicked.connect(lambda: self._set_model_default('vision'))
button_layout.addWidget(set_vision_btn)

button_layout.addStretch()

# Add method:
def _set_model_default(self, model_type: str):
    """Set selected model as default for the given type."""
    selected = self.model_list.selectedItems()
    if not selected:
        return
    
    model_name = selected[0].text().replace("⭐ ", "").replace("✓ ", "").split(" ")[0]
    
    if model_type == 'text':
        self.adapter.model_text = model_name
        self.config.set("ollama.default_model_text", model_name)
        self._add_diagnostic(f"✅ Default text model set to: {model_name}")
    elif model_type == 'vision':
        self.adapter.model_vision = model_name
        self.config.set("ollama.default_model_vision", model_name)
        self._add_diagnostic(f"✅ Default vision model set to: {model_name}")
    
    self.config.save()
    self._check_status()
```

---

## Testing Checklist

- [ ] Config loads with new settings
- [ ] Settings Dialog shows all three models
- [ ] Can change text model
- [ ] Can change vision model
- [ ] Can change OCR model
- [ ] Changes persist on restart
- [ ] Fallbacks work if model not available
- [ ] AI Model Manager shows all three defaults
- [ ] Can set defaults from dialog
- [ ] Processing uses correct model for each task

---

## Before/After

### BEFORE (Current)
```
What model for images? 🤷
What model for descriptions? Always llama3.2 (can't change without restart)
What model for OCR? Always Tesseract (can't change)
Can I change them? Not really... and changes don't save anyway
```

### AFTER (With This Implementation)
```
What model for images? User can choose ✓
What model for descriptions? User can choose ✓
What model for OCR? User can choose Tesseract or Ollama ✓
Can I change them? Yes! Settings → Change model → Done ✓
Do changes persist? Yes! ✓✓✓
```

---

## Files to Modify

1. `config/settings.json` - Add three defaults
2. `src/services/llm_adapter.py` - Add getter methods
3. `src/ui/settings_dialog.py` - Add three combo boxes
4. `src/ui/ai_model_dialog.py` - Show and set defaults
5. `src/services/processing_orchestrator.py` - Use correct model per task

**Total Changes:** ~150-200 lines of code
**Complexity:** Low-Medium
**Time:** 2-3 hours

This is a **great next improvement** after fixing the config persistence bug! 🚀
