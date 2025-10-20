# Export Functionality Improvements - Previewless Insight Viewer

## Overview

The export functionality in Previewless Insight Viewer has been enhanced to provide better user experience and more robust handling of file formats. This document details the improvements made to the export system.

## Improvements

### 1. Format-Specific Export Options

The export functionality now provides dedicated options for different formats:
- CSV export for tabular data
- JSON export for structured data

These options are accessible through a dedicated submenu in the File menu.

### 2. Enhanced Format Selection Logic

The export system has been improved to handle file format selection in several ways:
- Format parameter passed from menu selection
- File extension in user-specified path
- Filter selection in file dialog

### 3. Fixed Logic Flow

The export method now correctly:
- Handles format selection from multiple sources
- Applies the appropriate extension when needed
- Properly routes to the correct format-specific export method
- Provides clear feedback to the user

### 4. Code Quality Improvements

The `_export_results` method has been refactored to fix:
- Indentation issues that could cause unexpected behavior
- Logical flow to ensure proper extension handling
- Conditional checks to verify the format before exporting

## Implementation Details

```python
def _export_results(self, format=None):
    """Export analysis results to CSV or JSON file."""
    from PySide6.QtWidgets import QFileDialog
    
    # Determine file filters based on format parameter
    if format == "csv":
        file_filter = "CSV Files (*.csv)"
        default_extension = ".csv"
    elif format == "json":
        file_filter = "JSON Files (*.json)"
        default_extension = ".json"
    else:
        file_filter = "CSV Files (*.csv);;JSON Files (*.json)"
        default_extension = None
        
    # Get export path from user
    export_path, selected_filter = QFileDialog.getSaveFileName(
        self,
        "Export Results",
        "",
        file_filter
    )
    
    if not export_path:
        return  # User cancelled
    
    try:
        if export_path.lower().endswith('.csv'):
            self._export_to_csv(export_path)
        elif export_path.lower().endswith('.json'):
            self._export_to_json(export_path)
        else:
            # Add default extension based on format or filter
            if default_extension:
                export_path += default_extension
                if export_path.lower().endswith('.csv'):
                    self._export_to_csv(export_path)
                elif export_path.lower().endswith('.json'):
                    self._export_to_json(export_path)
            elif "CSV" in selected_filter:
                export_path += ".csv"
                self._export_to_csv(export_path)
            else:
                export_path += ".json"
                self._export_to_json(export_path)
        
        self._show_notification(f"Results exported to {export_path}", "info")
        
    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        self._show_notification(f"Export failed: {str(e)}", "error")
```

## Benefits

These improvements provide:

1. More intuitive export workflow for users
2. Better error handling and user feedback
3. Consistent file naming and extension handling
4. More robust format selection logic

## Future Enhancements

Potential future improvements could include:
- Additional export formats (Excel, PDF, HTML)
- Export templates for different data views
- Customizable export options (columns, filters)
- Export presets for common use cases