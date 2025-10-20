# Enhancement: Clear Model Usage Display

## 🎯 Goal

Make it crystal clear which AI models are used for what purpose:
- **Vision models** for image analysis (photos, screenshots, etc.)
- **LLM models** for text generation (descriptions, classifications)
- **OCR** for document text extraction (PDFs, scans)

---

## ✨ What Changed

### 1. Enhanced Connection Settings Panel

**Before:**
```
Connection Settings
├─ Ollama Host: http://localhost:11434
├─ Default Model: llama3.2
├─ Temperature: 0.4
└─ Max Tokens: 270
```

**After:**
```
Connection Settings & Model Usage
├─ Ollama Host: http://localhost:11434
│
├─ Model Usage:
│  ├─ 🖼️ Vision (images): qwen2.5vl:7b, llava:7b (+2 more)
│  ├─ 🤖 LLM (text/tags): llama3.2 (for descriptions, classifications)
│  └─ 📄 OCR (documents): Tesseract (external OCR engine, not Ollama)
│
└─ LLM Settings:
   ├─ Temperature: 0.4
   └─ Max Tokens: 270
```

---

## 🎨 Visual Enhancements

### Color-Coded Model List

**Models are now clearly tagged and color-coded:**

```
Available Models
┌─────────────────────────────────────────┐
│ ⭐ llama3.2 (default LLM)              │ ← Green background
│ qwen2.5vl:7b (vision)                   │ ← Cyan text
│ llava:7b (vision)                       │ ← Cyan text
│ llava:34b (vision)                      │ ← Cyan text
│ ✓ qwen2.5:14b                           │ ← Normal
└─────────────────────────────────────────┘

Legend:
⭐ Green background = Default LLM (used for text/descriptions)
Cyan text = Vision model (auto-selected for images)
📄 OCR uses Tesseract (external, not Ollama)
```

---

## 🔍 Detection Logic

### Vision Model Detection

Models are automatically detected as vision-capable if they contain these keywords:
- `vision`
- `vl` (vision-language)
- `llava`
- `qwen2.5vl`
- `qwen2-vl`
- `minicpm-v`

**Examples:**
- ✅ `qwen2.5vl:7b` → Vision model
- ✅ `llava:34b` → Vision model
- ✅ `llama3.2-vision` → Vision model
- ❌ `llama3.2` → Regular LLM
- ❌ `qwen2.5:14b` → Regular LLM

---

## 📊 Model Usage in Processing

### How Models Are Selected

**For Image Files** (.jpg, .png, .gif, .webp, .bmp):
```python
# Vision models are tried in order of preference:
priority_order = [
    'qwen2.5vl:7b',     # Best balance of speed/quality
    'llava:7b',         # Fast and reliable
    'llava:34b',        # High quality (slower)
    'qwen2.5vl:72b',    # Maximum quality (very slow)
    # ... fallback models
]

# First available model is automatically selected
# No user configuration needed!
```

**For Document Files** (.pdf, .docx, .txt):
```python
# Step 1: Extract text with Tesseract OCR
text = tesseract.process_document(file)

# Step 2: Use default LLM for understanding
tags = llm_model.generate_tags(text)
description = llm_model.generate_description(text)
```

**For Text Processing** (tags, descriptions, classifications):
```python
# Always uses the default LLM model
model = config.get('ollama_default_model')  # e.g., "llama3.2"
```

---

## 💡 User Benefits

### Clear Understanding

**Before:**
- ❓ "Which model analyzes my photos?"
- ❓ "Is OCR using Ollama?"
- ❓ "Why do I need multiple models?"

**After:**
- ✅ "Vision models (cyan) handle my images"
- ✅ "OCR uses Tesseract, not Ollama"
- ✅ "Default LLM (green) generates descriptions"

### Smart Auto-Selection

**Users don't need to manually choose:**
- Vision models are automatically tried for images
- Best available vision model is selected
- Falls back gracefully if no vision models installed

### Easy Identification

**At a glance, users can see:**
- Which models are for vision (cyan)
- Which model is the default LLM (green ⭐)
- That OCR is separate (Tesseract)

---

## 🛠️ Implementation Details

### Code Changes

**File:** `src/ui/ai_model_dialog.py`

#### 1. Enhanced Connection Group
```python
def _create_connection_group(self) -> QGroupBox:
    # Added three usage labels with emojis
    self.vision_model_label = QLabel()  # 🖼️ Vision (images)
    self.llm_model_label = QLabel()     # 🤖 LLM (text/tags)
    self.ocr_model_label = QLabel()     # 📄 OCR (documents)
    
    # Set OCR label (static)
    self.ocr_model_label.setText(
        "<b>Tesseract</b> (external OCR engine, not Ollama)"
    )
```

#### 2. Vision Model Detection
```python
def _on_status_checked(self, success: bool, message: str, models: List[str]):
    # Detect vision models
    vision_model_keywords = ['vision', 'vl', 'llava', 'qwen2.5vl', 'qwen2-vl', 'minicpm-v']
    available_vision_models = []
    for model in models:
        model_lower = model.lower()
        if any(keyword in model_lower for keyword in vision_model_keywords):
            available_vision_models.append(model)
    
    # Update vision label
    if available_vision_models:
        vision_display = ", ".join(available_vision_models[:2])
        if len(available_vision_models) > 2:
            vision_display += f" (+{len(available_vision_models) - 2} more)"
        self.vision_model_label.setText(
            f"<b>{vision_display}</b> (auto-selected for images)"
        )
```

#### 3. Color-Coded Model List
```python
# Populate list with type indicators
for model in models:
    is_default = (model == default_model_item)
    is_vision = model in available_vision_models
    
    # Build tags
    tags = []
    if is_default:
        tags.append("default LLM")
    if is_vision:
        tags.append("vision")
    
    # Color coding
    if is_default:
        item.setBackground(Qt.GlobalColor.darkGreen)
    elif is_vision:
        item.setForeground(Qt.GlobalColor.cyan)
```

#### 4. Legend Display
```python
legend_label = QLabel(
    "<b>Legend:</b><br>"
    "<span style='color: #4CAF50;'>⭐ Green background</span> = Default LLM<br>"
    "<span style='color: cyan;'>Cyan text</span> = Vision model<br>"
    "📄 OCR uses Tesseract (external, not Ollama)"
)
```

---

## 🎓 Understanding Model Roles

### Vision Models (🖼️)

**Purpose:** Analyze image content directly
**Used for:** Photos, screenshots, charts, diagrams
**Input:** Raw image files
**Output:** Tags, descriptions, content understanding

**Example Models:**
- `qwen2.5vl:7b` - Excellent vision + language understanding
- `llava:7b` - Fast and reliable
- `llava:34b` - High quality, slower
- `llama3.2-vision` - Meta's vision model

**Processing Flow:**
```
Image File → Vision Model → Tags + Description → Database
(no OCR needed!)
```

### LLM Models (🤖)

**Purpose:** Generate text, understand language
**Used for:** Descriptions, tags, classifications
**Input:** Text (from OCR or direct text files)
**Output:** Descriptions, tags, category classifications

**Example Models:**
- `llama3.2` - Fast, general purpose
- `qwen2.5:14b` - Larger, more capable
- `mistral` - Alternative LLM

**Processing Flow:**
```
OCR Text → LLM Model → Tags + Description → Database
```

### OCR Engine (📄)

**Purpose:** Extract text from documents/images
**Used for:** PDFs, scanned documents, text images
**Input:** Document files, images with text
**Output:** Plain text

**Engine:** Tesseract (external tool, not Ollama)

**Processing Flow:**
```
PDF/Document → Tesseract OCR → Text → LLM Model → Database
```

---

## 📋 Diagnostics Output

### With Vision Models
```
✅ Connected to http://localhost:11434
✅ Found 6 model(s)
✅ Default LLM model 'llama3.2' is available
✅ Found 3 vision model(s): qwen2.5vl:7b, llava:7b, llava:34b
   Vision models are auto-selected when processing images
```

### Without Vision Models
```
✅ Connected to http://localhost:11434
✅ Found 2 model(s)
✅ Default LLM model 'llama3.2' is available
⚠️  No vision models detected
   Recommended: ollama pull qwen2.5vl:7b
   Or: ollama pull llava:7b
```

---

## 🚀 Usage Scenarios

### Scenario 1: Processing Photos
```
User adds vacation photos to queue
↓
System detects: .jpg files
↓
Auto-selects: qwen2.5vl:7b (first available vision model)
↓
Result: Rich descriptions without OCR
```

### Scenario 2: Processing PDFs
```
User adds scanned documents to queue
↓
System detects: .pdf files
↓
Step 1: Tesseract extracts text
Step 2: llama3.2 (default LLM) generates tags/description
↓
Result: Searchable, tagged documents
```

### Scenario 3: Mixed Batch
```
User adds 50 photos + 20 PDFs
↓
Photos → Vision models (qwen2.5vl:7b, llava:7b)
PDFs → Tesseract OCR → Default LLM (llama3.2)
↓
Result: All processed with optimal models
```

---

## 📝 Recommendations

### Suggested Model Setup

**Minimal Setup (Fast):**
```bash
ollama pull llama3.2           # Default LLM
ollama pull qwen2.5vl:7b       # Vision model
# Tesseract already installed
```

**Recommended Setup (Balanced):**
```bash
ollama pull llama3.2           # Fast LLM
ollama pull llava:7b           # Fast vision
ollama pull llava:34b          # Quality vision
# Total: 2 LLM + 2 vision models
```

**Power User Setup (Best Quality):**
```bash
ollama pull qwen2.5:14b        # Larger LLM
ollama pull qwen2.5vl:7b       # Fast vision
ollama pull llava:34b          # Quality vision
ollama pull qwen2.5vl:72b      # Premium vision
# Total: 1 large LLM + 3 vision models
```

---

## ✅ Verification

### Check Model Roles
1. Open AI Model Manager
2. Look at "Model Usage" section:
   - 🖼️ Vision line shows available vision models
   - 🤖 LLM line shows default text model
   - 📄 OCR line shows Tesseract (not Ollama)

### Check Model List
1. Scroll through available models
2. Look for color coding:
   - Green background = Default LLM (one model only)
   - Cyan text = Vision models (multiple possible)
   - White text = Other models

### Check Diagnostics
1. Look at diagnostics panel
2. Should show:
   - Connection status
   - Default LLM availability
   - Vision model count
   - Recommendations if missing

---

## 🎉 Summary

**Problem Solved:**
Users were confused about which models do what.

**Solution Implemented:**
- Clear labels: Vision, LLM, OCR
- Color coding: Green (default), Cyan (vision)
- Auto-detection of vision models
- Explicit OCR clarification (Tesseract, not Ollama)
- Helpful diagnostics and recommendations

**User Experience:**
- No guessing which model does what
- Clear understanding of processing pipeline
- Easy to see what's missing
- Recommendations for optimal setup

**Status: COMPLETE** ✅
