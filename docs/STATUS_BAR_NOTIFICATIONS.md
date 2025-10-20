# Status Bar Notifications

## Overview

The notification system has been updated to display messages in the status bar at the very bottom of the application, replacing the previous overlay notification banner. This change provides a cleaner, more standard interface that follows desktop application best practices.

## Changes Made

1. Removed the overlay notification banner:
   - Removed `_create_notification_banner()` method
   - Removed `_position_notification_banner()` method
   - Removed `resizeEvent()` override that was positioning the banner

2. Enhanced the status bar to include notification functionality:
   - Updated `_create_status_bar()` to include notification components
   - Added `status_notification_icon` and `status_notification_message` labels
   - Set up styling for different notification types (info, success, warning, error)

3. Updated notification display and hiding:
   - Modified `_show_notification()` to use status bar components
   - Updated `_hide_notification()` to clear status bar notification area

## Implementation Details

The status bar now includes a dedicated notification area on the left side that stretches to fill available space. Notifications include an icon and message with color coding based on the notification type:

- Info: Blue (ℹ)
- Success: Green (✓)
- Warning: Orange (⚠)
- Error: Red (✕)

Notifications can be set to auto-hide after a specified duration (default: 5 seconds) or remain visible until the next notification.

## Benefits

1. More consistent with desktop application conventions
2. Cleaner interface without overlays covering content
3. Permanent location that users can expect to find notifications
4. Doesn't require special positioning logic on window resize
5. Integrates with existing status indicators (AI model status, etc.)

## Usage

The notification system API remains unchanged. Display notifications using:

```python
self._show_notification("Your message here", notification_type="info", auto_hide=5000)
```

Valid notification types:
- "info" (default)
- "success" 
- "warning"
- "error"

Set `auto_hide` to 0 to prevent the notification from automatically hiding.