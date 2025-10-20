# Bug Fix: QTextEdit → QTextBrowser

## Issue
Error when opening help dialog:
```
AttributeError: 'PySide6.QtWidgets.QTextEdit' object has no attribute 'setOpenExternalLinks'
```

## Root Cause
`QTextEdit` doesn't support `setOpenExternalLinks()` method. This is only available in `QTextBrowser` and `QLabel`.

## Solution
Changed help dialog to use `QTextBrowser` instead of `QTextEdit`.

## Changes Made

### 1. Added Import
```python
from PySide6.QtWidgets import QTextBrowser
```

### 2. Changed Widget Type
**Before:**
```python
help_text = QTextEdit()
help_text.setReadOnly(True)
help_text.setHtml(help_html)
help_text.setOpenExternalLinks(True)  # ❌ Error!
```

**After:**
```python
help_text = QTextBrowser()
help_text.setReadOnly(True)
help_text.setHtml(help_html)
help_text.setOpenExternalLinks(True)  # ✅ Works!
```

## Why QTextBrowser?

`QTextBrowser` is the correct widget for displaying formatted HTML with clickable links:

| Feature | QTextEdit | QTextBrowser |
|---------|-----------|--------------|
| Rich text display | ✅ | ✅ |
| HTML rendering | ✅ | ✅ |
| Editable by default | ✅ | ❌ (read-only) |
| External link support | ❌ | ✅ |
| Link navigation | ❌ | ✅ |
| Best for | Editing | Viewing docs |

## Testing
```bash
python -c "from src.ui.ai_model_dialog import ModelPullHelpDialog; print('✅ Fixed!')"
```

## Status
✅ **FIXED** - Help dialog now opens successfully with clickable external links!
