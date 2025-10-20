# Bottom Notification Bar - Status Bar Style

**Date:** October 13, 2025  
**Status:** ✅ COMPLETE - Notification bar repositioned to bottom with status bar styling

---

## Summary

Moved the notification banner from the top to the bottom of the application window, positioned just above the status bar. Resized and restyled to match the compact, single-line appearance of a status bar.

---

## Changes Made

### 1. Position Change
**Before:** Top of window (above tabs)
```
┌──────────────────────────────┐
│ [Notification Banner]        │ ← Was here
├──────────────────────────────┤
│ ┌─────┬─────┬──────────┐    │
│ │Watch│Queue│Processing│    │
│ └─────┴─────┴──────────┘    │
│                              │
│ [Tab Content]                │
│                              │
├──────────────────────────────┤
│ Ready | Files: 0 | Idle     │
└──────────────────────────────┘
```

**After:** Bottom of window (above status bar)
```
┌──────────────────────────────┐
│ ┌─────┬─────┬──────────┐    │
│ │Watch│Queue│Processing│    │
│ └─────┴─────┴──────────┘    │
│                              │
│ [Tab Content]                │
│                              │
├──────────────────────────────┤
│ [Notification Banner]        │ ← Now here
├──────────────────────────────┤
│ Ready | Files: 0 | Idle     │
└──────────────────────────────┘
```

### 2. Size & Styling Changes

**Previous (Top Banner Style):**
- Height: Auto (varied based on content)
- Word wrap: Enabled (multi-line)
- Padding: 12px 8px
- Font size: 11pt
- Border radius: 4px
- Icon size: Variable
- Close button: 24x24px

**Current (Status Bar Style):**
- Height: **28px (fixed)** - matches typical status bar
- Word wrap: **Disabled (single line only)**
- Padding: 8px 4px (compact)
- Font size: **10pt** (smaller, status bar appropriate)
- Border: **None** (flat design)
- Icon size: **20px (fixed width)**
- Close button: **20x20px** (smaller, more subtle)

### 3. Layout Structure

```
notification_banner (QWidget)
├── banner_layout (QHBoxLayout)
│   ├── spacing: 8px
│   ├── margins: 8px 4px 8px 4px
│   │
│   ├── notification_icon (QLabel)
│   │   └── Fixed width: 20px
│   │
│   ├── notification_label (QLabel)
│   │   ├── Word wrap: False
│   │   ├── Stretch factor: 1
│   │   └── Single line text
│   │
│   └── close_btn (QPushButton)
│       ├── Fixed size: 20x20px
│       ├── Transparent background
│       └── Hover effect
```

---

## Code Changes

### src/ui/main_window.py

**1. Layout Order (Line ~118):**
```python
# Before
main_layout.addWidget(self.notification_banner)  # Top
main_layout.addWidget(self.tabs)

# After  
main_layout.addWidget(self.tabs)
main_layout.addWidget(self.notification_banner)  # Bottom
```

**2. Banner Creation (Line ~125):**
```python
def _create_notification_banner(self):
    """Create inline notification banner (status bar style at bottom)."""
    self.notification_banner = QWidget()
    self.notification_banner.setVisible(False)
    self.notification_banner.setFixedHeight(28)  # Match status bar height
    
    banner_layout = QHBoxLayout(self.notification_banner)
    banner_layout.setContentsMargins(8, 4, 8, 4)  # Compact padding
    banner_layout.setSpacing(8)
    
    self.notification_icon = QLabel()
    self.notification_icon.setFixedWidth(20)  # Compact icon
    
    self.notification_label = QLabel()
    self.notification_label.setWordWrap(False)  # Single line only
    
    close_btn = QPushButton("✕")
    close_btn.setFixedSize(20, 20)  # Smaller button
```

**3. Styling (Line ~162):**
```python
self.notification_banner.setStyleSheet(f"""
    QWidget {{
        background-color: {bg_color};
        color: white;
        border: none;           # Flat design
        font-size: 10pt;        # Smaller font
    }}
""")
```

**4. Message Format (Line ~778):**
```python
# Single line format for compact display
message = (
    f"Processing completed - "
    f"Processed: {count} | Failed: {failed} | Skipped: {skipped}"
)
```

---

## Visual Comparison

### Notification Examples

**Success (Green):**
```
┌──────────────────────────────────────────────────────────┐
│ ✓  Processing completed - Processed: 5 | Failed: 0 | Skipped: 0  [✕]│
└──────────────────────────────────────────────────────────┘
```

**Info (Blue):**
```
┌──────────────────────────────────────────────────────────┐
│ ℹ  Queue cleared successfully                        [✕]│
└──────────────────────────────────────────────────────────┘
```

**Warning (Orange):**
```
┌──────────────────────────────────────────────────────────┐
│ ⚠  Processing not available. Please check OCR and LLM configuration in Settings.  [✕]│
└──────────────────────────────────────────────────────────┘
```

**Error (Red):**
```
┌──────────────────────────────────────────────────────────┐
│ ✕  System issues detected - check logs for details  [✕]│
└──────────────────────────────────────────────────────────┘
```

---

## Benefits of Bottom Placement

### 1. **Non-Intrusive**
- Doesn't push down tab content
- Familiar location (near status bar)
- Easy to ignore if desired

### 2. **Eye-Level Consistency**
- Status information naturally at bottom
- Users look at status bar area for updates
- Logical grouping with permanent status info

### 3. **Content Preservation**
- Top of screen reserved for navigation (tabs)
- Main content area unaffected
- No layout shift when notification appears

### 4. **Quick Scan**
- Single line = instant comprehension
- Color coding = immediate severity recognition
- Close proximity to status bar = easy mental grouping

---

## Behavior

### Show/Hide
- Appears: Slides in from bottom (instant, no animation yet)
- Dismisses: 
  - Auto: After specified timeout (3-8 seconds)
  - Manual: Click X button
- State: Hidden by default, only shows when triggered

### Auto-Hide Timings
| Action | Duration | Reasoning |
|--------|----------|-----------|
| Queue cleared | 3s | Quick confirmation |
| System status | 4s | Brief info |
| Warnings | 6s | Need time to read |
| Processing complete | 8s | Multiple stats to read |

---

## Integration with Status Bar

The notification bar sits **above** the status bar, creating a two-tier information system:

**Tier 1: Permanent Status (Status Bar)**
- Always visible
- Current state: Ready, Files count, Processing state
- Neutral styling (gray/dark)

**Tier 2: Temporary Notifications (Notification Bar)**
- Conditionally visible
- Events and actions: Completed tasks, warnings, confirmations
- Color-coded by severity (green/blue/orange/red)

Together they provide:
- **Persistent context** (status bar)
- **Actionable feedback** (notification bar)

---

## Future Enhancements

### Potential Improvements
1. **Slide Animation** - Smooth slide up/down transition
2. **Progress Indicator** - Show auto-hide countdown
3. **Stacking** - Multiple notifications queue up
4. **Action Buttons** - "View Details", "Undo", etc.
5. **Persistent Option** - Pin important notifications

### Example: Slide Animation
```python
from PySide6.QtCore import QPropertyAnimation

def _show_notification_animated(self, message, type, auto_hide):
    # Start hidden below window
    self.notification_banner.move(0, self.height())
    self.notification_banner.setVisible(True)
    
    # Animate slide up
    animation = QPropertyAnimation(self.notification_banner, b"pos")
    animation.setDuration(200)
    animation.setEndValue(QPoint(0, self.height() - 28))
    animation.start()
```

---

## Testing Checklist

✅ **Position**
- [ ] Banner appears at bottom above status bar
- [ ] Doesn't overlap status bar
- [ ] Doesn't cover tab content

✅ **Size**
- [ ] Fixed height of 28px
- [ ] Matches status bar height
- [ ] Full width of window

✅ **Styling**
- [ ] Single line text (no wrapping)
- [ ] Icon visible and sized correctly (20px)
- [ ] Close button clickable (20x20px)
- [ ] Colors match notification type

✅ **Functionality**
- [ ] Shows on processing complete
- [ ] Shows on queue cleared
- [ ] Shows on processing unavailable
- [ ] Shows on diagnostics run
- [ ] Auto-hides after specified time
- [ ] Manual dismiss with X works

---

## Summary of Changes

| Aspect | Before | After |
|--------|--------|-------|
| **Position** | Top (above tabs) | Bottom (above status bar) |
| **Height** | Auto (multi-line) | 28px fixed |
| **Font Size** | 11pt | 10pt |
| **Word Wrap** | Enabled | Disabled |
| **Border** | 4px radius | None (flat) |
| **Icon** | Variable | 20px fixed |
| **Button** | 24x24px | 20x20px |
| **Padding** | 12px 8px | 8px 4px |
| **Style** | Banner-like | Status bar-like |

---

## Files Modified

1. **src/ui/main_window.py**
   - Line ~118: Moved notification widget to bottom of layout
   - Line ~127: Updated _create_notification_banner() for compact design
   - Line ~162: Updated styling to flat, status bar appearance
   - Line ~778: Changed message format to single line

**Total changes:** ~15 lines modified, styling improved

---

**STATUS:** Notification bar successfully repositioned to bottom with status bar styling! 🎉

**User Experience:** Clean, compact, non-intrusive notifications that feel like a natural extension of the status bar.
