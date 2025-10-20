# AI Model Dialog Fix - Previewless Insight Viewer

## Issue

When attempting to open the AI Model Manager from the menu, the application was encountering an error:

```
AttributeError: 'MainWindow' object has no attribute 'host'
```

This occurred because the `_show_ai_models` method in `MainWindow` was incorrectly passing the `self` (MainWindow) object to the `AIModelDialog` constructor instead of the required `llm_adapter`.

## Root Cause Analysis

1. The `AIModelDialog` constructor requires an `OllamaAdapter` instance as its first parameter
2. The `_show_ai_models` method was incorrectly passing `self` (the MainWindow object)
3. During initialization of the dialog, it attempted to access `self.adapter.host`, but `self.adapter` was the MainWindow object which has no `host` attribute

## Solution

The fix involved updating the `_show_ai_models` method in `MainWindow` to:

1. Pass the correct `llm_adapter` as the first parameter to the `AIModelDialog` constructor
2. Pass `self` as the parent parameter to maintain proper parent-child widget relationship
3. Add error handling for cases when the LLM adapter is not available

## Implementation

```python
def _show_ai_models(self):
    """Show AI model management dialog."""
    from src.ui.ai_model_dialog import AIModelDialog
    
    if not self.llm_adapter:
        self._show_notification("LLM adapter not available", "error")
        return
        
    # Pass the LLM adapter and self as parent
    dialog = AIModelDialog(self.llm_adapter, self)
    dialog.exec()
```

## Verification

The fix was verified by:

1. Running the application
2. Clicking on the "AI Model Manager" menu item in the Tools menu
3. Confirming that the dialog opens without errors
4. Testing the dialog's functionality

## Related Components

This fix ensures proper integration between:

1. **MainWindow** class in `src/ui/main_window.py`
2. **AIModelDialog** class in `src/ui/ai_model_dialog.py`
3. **OllamaAdapter** class in `src/services/llm_adapter.py`

## Lessons Learned

When creating dialogs that require specific service objects:

1. Always check parameter types and ensure correct objects are being passed
2. Implement error handling for cases when required services are unavailable
3. Maintain proper parent-child relationships for modal dialogs
4. Ensure consistent implementation across the codebase (other methods like `_show_ai_model_dialog` were correctly implemented)

## Status

✅ Fixed and verified