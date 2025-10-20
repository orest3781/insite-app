# Quick Implementation Guide: AI Model Manager Improvements

## 🎯 5 Quick Wins to Implement First

### 1. Fix Config Persistence (15 minutes) ⭐ CRITICAL
**Current Issue:** Setting default model doesn't save
**File:** `src/ui/ai_model_dialog.py`, line ~907

**Before:**
```python
self.adapter.model_name = model_name
self._add_diagnostic(f"✅ Default model changed to: {model_name}")
self._add_diagnostic(f"   Note: Restart app or update config to persist")
```

**After:**
```python
self.adapter.model_name = model_name
# Persist to config
try:
    self.adapter.config.set("models", "default_llm", model_name)
    self.adapter.config.save()
    self._add_diagnostic(f"✅ Default model changed to: {model_name} (saved)")
except Exception as e:
    self._add_diagnostic(f"⚠️ Model changed but save failed: {str(e)}")
```

---

### 2. Add Model Search/Filter (45 minutes) ⭐⭐
**Location:** `_create_model_group()` method
**What to add:** Search box above model list

**Code to add after line ~550:**
```python
# Add search box before model list
search_layout = QHBoxLayout()
search_label = QLabel("🔍 Search:")
self.model_search = QLineEdit()
self.model_search.setPlaceholderText("Filter by name...")
self.model_search.textChanged.connect(self._filter_model_list)
search_layout.addWidget(search_label)
search_layout.addWidget(self.model_search, 1)
layout.addLayout(search_layout)

# Add filter buttons
filter_layout = QHBoxLayout()
self.filter_vision_cb = QCheckBox("Vision Models")
self.filter_vision_cb.stateChanged.connect(self._filter_model_list)
filter_layout.addWidget(self.filter_vision_cb)
filter_layout.addStretch()
layout.addLayout(filter_layout)
```

**Add method:**
```python
def _filter_model_list(self):
    """Filter model list by search and filters."""
    search_text = self.model_search.text().lower()
    show_vision = self.filter_vision_cb.isChecked()
    
    for i in range(self.model_list.count()):
        item = self.model_list.item(i)
        text = item.text().lower()
        
        # Search match
        matches_search = search_text in text or not search_text
        
        # Vision filter
        matches_vision = not show_vision or 'vision' in text
        
        item.setHidden(not (matches_search and matches_vision))
```

---

### 3. Improve Diagnostics Section (30 minutes) ⭐
**Location:** `_create_diagnostics_group()` method
**What to add:** Clear button, timestamps, color coding

**Replace current diagnostics group:**
```python
def _create_diagnostics_group(self) -> QGroupBox:
    """Create diagnostics group with clear button and formatting."""
    group = QGroupBox("Diagnostics")
    layout = QVBoxLayout(group)
    
    # Toolbar
    toolbar = QHBoxLayout()
    clear_btn = QPushButton("🗑️ Clear")
    clear_btn.clicked.connect(self._clear_diagnostics)
    toolbar.addWidget(clear_btn)
    
    export_btn = QPushButton("💾 Save Log")
    export_btn.clicked.connect(self._export_diagnostics)
    toolbar.addWidget(export_btn)
    
    toolbar.addStretch()
    layout.addLayout(toolbar)
    
    # Text area with HTML support for color coding
    self.diagnostics_text = QTextEdit()
    self.diagnostics_text.setReadOnly(True)
    self.diagnostics_text.setMaximumHeight(150)
    self.diagnostics_text.setStyleSheet("""
        QTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
            padding: 8px;
        }
    """)
    layout.addWidget(self.diagnostics_text)
    
    return group

def _add_diagnostic(self, message: str, msg_type: str = "info"):
    """Add diagnostic message with color coding.
    
    Args:
        message: Message text
        msg_type: 'error' (red), 'warning' (yellow), 'success' (green), 'info' (default)
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Color coding
    colors = {
        'error': '#FF6B6B',
        'warning': '#FFA500',
        'success': '#4CAF50',
        'info': '#d4d4d4'
    }
    color = colors.get(msg_type, colors['info'])
    
    # Format with timestamp
    formatted = f'<span style="color: {color};">[{timestamp}] {message}</span>'
    self.diagnostics_text.append(formatted)
    
    # Auto-scroll to bottom
    scrollbar = self.diagnostics_text.verticalScrollBar()
    scrollbar.setValue(scrollbar.maximum())

def _clear_diagnostics(self):
    """Clear diagnostics text."""
    self.diagnostics_text.clear()

def _export_diagnostics(self):
    """Export diagnostics to file."""
    from pathlib import Path
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path("logs") / f"diagnostics_{timestamp}.log"
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'w') as f:
        f.write(self.diagnostics_text.toPlainText())
    
    QMessageBox.information(self, "Diagnostics Saved", f"Saved to: {log_file}")
```

---

### 4. Add Model Size Display (1 hour) ⭐⭐
**Location:** `_on_status_checked()` method around line ~850

**Add after getting models list:**
```python
# Get model sizes
model_sizes = self._get_model_sizes(models)

# Then in the loop where you populate model list:
for model in models:
    is_default = (model == default_model_item)
    is_vision = model in available_vision_models
    size_str = model_sizes.get(model, "Unknown")
    
    # Build display text
    display_text = f"✓ {model} ({size_str})"
    tags = []
    
    if is_default:
        tags.append("default LLM")
    if is_vision:
        tags.append("vision")
    
    if tags:
        display_text += f" [{', '.join(tags)}]"
        if is_default:
            display_text = f"⭐ {model} ({size_str}) [{', '.join(tags)}]"
    
    item = QListWidgetItem(display_text)
    # ... rest of code
```

**Add method to get sizes:**
```python
def _get_model_sizes(self, models: List[str]) -> Dict[str, str]:
    """Get size info for models from ollama show command."""
    sizes = {}
    for model in models:
        try:
            result = subprocess.run(
                ['ollama', 'show', model],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Parse output to find size
            for line in result.stdout.split('\n'):
                if 'total size' in line.lower():
                    size_str = line.split(':')[1].strip() if ':' in line else 'Unknown'
                    sizes[model] = size_str
                    break
        except Exception:
            sizes[model] = 'Unknown'
    return sizes
```

---

### 5. Add Download ETA (30 minutes) ⭐⭐
**Location:** `ModelPullThread` class, line ~50

**Track speed and calculate ETA:**
```python
class ModelPullThread(QThread):
    """Thread for pulling Ollama models without blocking UI."""
    
    pull_started = Signal(str)
    pull_progress = Signal(str, str, int, int)  # model_name, progress_text, current, total
    pull_completed = Signal(str, bool, str)
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self._process = None
        self.start_time = None
        self.downloaded_bytes = 0
        self.total_bytes = None
    
    def run(self):
        """Pull model using ollama CLI."""
        try:
            import time
            self.start_time = time.time()
            self.pull_started.emit(self.model_name)
            
            self._process = subprocess.Popen(
                ['ollama', 'pull', self.model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            for line in self._process.stdout:
                line = line.strip()
                if line:
                    # Parse progress from line
                    # Format: "pulling 0c6f73c1e0f2... [=====>                    ] 2.4 GB / 5.0 GB"
                    current_bytes, total_bytes = self._parse_progress(line)
                    if current_bytes and total_bytes:
                        # Calculate speed and ETA
                        elapsed = time.time() - self.start_time
                        if elapsed > 0:
                            speed = current_bytes / elapsed  # bytes/sec
                            remaining = total_bytes - current_bytes
                            eta_seconds = int(remaining / speed) if speed > 0 else 0
                            eta_str = self._format_time(eta_seconds)
                            formatted = f"{line} (~{eta_str} remaining)"
                            self.pull_progress.emit(self.model_name, formatted, current_bytes, total_bytes)
                        else:
                            self.pull_progress.emit(self.model_name, line, current_bytes, total_bytes)
                    else:
                        self.pull_progress.emit(self.model_name, line, 0, 0)
            
            return_code = self._process.wait()
            if return_code == 0:
                self.pull_completed.emit(self.model_name, True, f"Successfully pulled {self.model_name}")
            else:
                error = self._process.stderr.read()
                self.pull_completed.emit(self.model_name, False, f"Failed: {error}")
        except Exception as e:
            self.pull_completed.emit(self.model_name, False, f"Error: {str(e)}")
    
    def _parse_progress(self, line: str) -> tuple:
        """Parse progress line to extract bytes."""
        import re
        # Look for pattern like "2.4 GB / 5.0 GB"
        match = re.search(r'([\d.]+)\s*(GB|MB|KB)\s*/\s*([\d.]+)\s*(GB|MB|KB)', line)
        if match:
            current = self._to_bytes(float(match.group(1)), match.group(2))
            total = self._to_bytes(float(match.group(3)), match.group(4))
            return current, total
        return None, None
    
    def _to_bytes(self, value: float, unit: str) -> int:
        """Convert size to bytes."""
        units = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
        return int(value * units.get(unit, 1))
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds as human-readable string."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}h {mins}m"
```

---

## 📝 Implementation Order

1. **Start:** Fix config persistence (easiest, most impactful)
2. **Then:** Add diagnostics improvements
3. **Then:** Add model search
4. **Then:** Add size display
5. **Finally:** Add ETA calculation

**Total Time:** ~3 hours for all 5 features

---

## 🧪 Testing Checklist

- [ ] Default model selection persists after restart
- [ ] Search box filters models correctly
- [ ] Diagnostics clear button works
- [ ] Model sizes display in list
- [ ] Download ETA updates during pull
- [ ] No crashes with many models
- [ ] Works with no models installed
- [ ] Error messages are helpful

---

## 🔗 Related Files
- Main dialog: `src/ui/ai_model_dialog.py`
- Config handling: `src/services/config_handler.py`
- LLM adapter: `src/services/llm_adapter.py`
