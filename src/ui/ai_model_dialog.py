"""
AI Model Manager Dialog.

Provides interface for managing Ollama models with real-time status monitoring.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import subprocess
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QTextEdit,
    QProgressBar, QWidget, QFormLayout, QLineEdit, QMessageBox,
    QApplication, QScrollArea, QTextBrowser, QComboBox,
    QTabWidget, QSplitter, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QColor

from src.services.llm_adapter import OllamaAdapter
from src.utils.logging_utils import get_logger

logger = get_logger("ui.ai_model_dialog")


class ModelPullThread(QThread):
    """Thread for pulling Ollama models without blocking UI."""
    
    pull_started = Signal(str)  # model_name
    pull_progress = Signal(str, str)  # model_name, progress_text
    pull_completed = Signal(str, bool, str)  # model_name, success, message
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self._process = None
    
    def run(self):
        """Pull model using ollama CLI."""
        try:
            self.pull_started.emit(self.model_name)
            
            # Run ollama pull command
            self._process = subprocess.Popen(
                ['ollama', 'pull', self.model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Read output line by line
            for line in self._process.stdout:
                line = line.strip()
                if line:
                    self.pull_progress.emit(self.model_name, line)
            
            # Wait for completion
            return_code = self._process.wait()
            
            if return_code == 0:
                self.pull_completed.emit(self.model_name, True, f"Successfully pulled {self.model_name}")
            else:
                error = self._process.stderr.read()
                self.pull_completed.emit(self.model_name, False, f"Failed to pull model: {error}")
                
        except FileNotFoundError:
            self.pull_completed.emit(self.model_name, False, "Ollama command not found. Is Ollama installed?")
        except Exception as e:
            self.pull_completed.emit(self.model_name, False, f"Error: {str(e)}")
    
    def stop(self):
        """Stop the pull process."""
        if self._process:
            self._process.terminate()


class ModelPullHelpDialog(QDialog):
    """Help dialog for pulling AI models."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup help dialog UI."""
        self.setWindowTitle("How to Pull AI Models")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📥 Guide: Downloading AI Models")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Help content
        help_html = """
        <style>
            body { 
                font-size: 11pt; 
                line-height: 1.6; 
                color: #333; 
                background-color: #ffffff;
            }
            h2 { 
                color: #1976D2; 
                margin-top: 20px; 
                margin-bottom: 10px;
                font-weight: bold;
            }
            h3 { 
                color: #388E3C; 
                margin-top: 15px; 
                margin-bottom: 8px;
                font-weight: bold;
            }
            .step { 
                background: #E3F2FD; 
                color: #0D47A1;
                padding: 12px; 
                margin: 10px 0; 
                border-left: 5px solid #2196F3;
                border-radius: 4px;
                font-weight: 500;
            }
            .tip { 
                background: #FFF9C4; 
                color: #F57F17;
                padding: 12px; 
                margin: 10px 0; 
                border-left: 5px solid #FFA000;
                border-radius: 4px;
                font-weight: 500;
            }
            .warning { 
                background: #FFEBEE; 
                color: #C62828;
                padding: 12px; 
                margin: 10px 0; 
                border-left: 5px solid #E53935;
                border-radius: 4px;
                font-weight: 500;
            }
            .success { 
                background: #E8F5E9; 
                color: #2E7D32;
                padding: 12px; 
                margin: 10px 0; 
                border-left: 5px solid #4CAF50;
                border-radius: 4px;
                font-weight: 500;
            }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            th, td { 
                border: 1px solid #ddd; 
                padding: 10px; 
                text-align: left; 
            }
            th { 
                background-color: #1976D2; 
                color: white; 
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #F5F5F5;
            }
            code { 
                background: #263238; 
                color: #4DD0E1;
                padding: 3px 8px; 
                border-radius: 4px; 
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: 500;
            }
            ul, ol {
                color: #424242;
            }
            strong {
                color: #1565C0;
            }
            em {
                color: #616161;
            }
        </style>
        
        <h2>🚀 Quick Start (30 Seconds)</h2>
        <div class="step">
            <strong>Step 1:</strong> Type a model name in the text box<br>
            <strong>Step 2:</strong> Click <strong>📥 Pull Model</strong> button<br>
            <strong>Step 3:</strong> Click <strong>Yes</strong> to confirm<br>
            <strong>Step 4:</strong> Wait 5-30 minutes (watch progress bar)<br>
            <strong>Step 5:</strong> Done! Model appears automatically ✅
        </div>
        
        <h2>🎯 Recommended Models to Try</h2>
        <table>
            <tr>
                <th>Model Name</th>
                <th>Size</th>
                <th>Speed</th>
                <th>Quality</th>
                <th>Best For</th>
            </tr>
            <tr>
                <td><code>llama3.2:3b</code></td>
                <td>2 GB</td>
                <td>⚡⚡⚡</td>
                <td>⭐⭐⭐</td>
                <td>Testing, fast results</td>
            </tr>
            <tr>
                <td><code>llama3.2:7b</code></td>
                <td>5 GB</td>
                <td>⚡⚡</td>
                <td>⭐⭐⭐⭐</td>
                <td>Balanced use</td>
            </tr>
            <tr>
                <td><code>qwen2.5:14b</code></td>
                <td>9 GB</td>
                <td>⚡</td>
                <td>⭐⭐⭐⭐⭐</td>
                <td>Best quality</td>
            </tr>
            <tr>
                <td><code>llava:7b</code></td>
                <td>5 GB</td>
                <td>⚡⚡</td>
                <td>⭐⭐⭐⭐</td>
                <td>Vision/images</td>
            </tr>
        </table>
        
        <div class="tip">
            💡 <strong>Tip:</strong> Start with <code>llama3.2:3b</code> for quick testing - it downloads fast and works well!
        </div>
        
        <h2>⏱️ How Long Does It Take?</h2>
        <ul>
            <li><strong>Small models (1b-3b):</strong> 5-15 minutes</li>
            <li><strong>Medium models (7b):</strong> 15-30 minutes</li>
            <li><strong>Large models (14b-32b):</strong> 30-90 minutes</li>
        </ul>
        
        <p><em>Time depends on your internet speed. Larger models = longer downloads.</em></p>
        
        <h2>🔧 After Pulling a Model</h2>
        
        <h3>To Set as Default:</h3>
        <div class="step">
            <strong>Option 1:</strong> Double-click the model in the list<br>
            <strong>Option 2:</strong> Select model → Click <strong>⭐ Set as Default</strong> button
        </div>
        
        <div class="success">
            ✅ Default model will be used for all future AI processing tasks!
        </div>
        
        <h2>❌ Troubleshooting</h2>
        
        <h3>Error: "Cannot connect to Ollama"</h3>
        <div class="warning">
            <strong>Problem:</strong> Ollama is not installed or not running<br><br>
            <strong>Solution:</strong>
            <ol>
                <li>Download Ollama from: <a href="https://ollama.ai">https://ollama.ai</a></li>
                <li>Install it (run the installer)</li>
                <li>Restart your computer</li>
                <li>Try again</li>
            </ol>
        </div>
        
        <h3>Error: "Ollama command not found"</h3>
        <div class="warning">
            <strong>Problem:</strong> Ollama CLI not in system PATH<br><br>
            <strong>Solution:</strong> Same as above - install Ollama first
        </div>
        
        <h3>Download is Very Slow or Stuck</h3>
        <ul>
            <li>Check your internet connection</li>
            <li>Wait longer - large models take time!</li>
            <li>Try a smaller model (3b instead of 14b)</li>
            <li>Use the <strong>📋 Copy Command</strong> button and run in terminal manually</li>
        </ul>
        
        <h2>📋 Alternative: Terminal Method</h2>
        <p>If the Pull Model button doesn't work:</p>
        <div class="step">
            <strong>1.</strong> Type model name in text box<br>
            <strong>2.</strong> Click <strong>📋 Copy Command</strong> button<br>
            <strong>3.</strong> Open terminal (CMD or PowerShell)<br>
            <strong>4.</strong> Right-click and paste<br>
            <strong>5.</strong> Press Enter<br>
            <strong>6.</strong> Wait for download to complete<br>
            <strong>7.</strong> Click <strong>🔄 Refresh Status</strong> in this dialog
        </div>
        
        <h2>💾 Where Are Models Stored?</h2>
        <ul>
            <li><strong>Windows:</strong> <code>C:\\Users\\YourName\\.ollama\\models\\</code></li>
            <li><strong>Mac:</strong> <code>~/.ollama/models/</code></li>
            <li><strong>Linux:</strong> <code>~/.ollama/models/</code></li>
        </ul>
        
        <h2>🗑️ Deleting Models</h2>
        <p>To remove unwanted models and free up disk space:</p>
        <div class="step">
            <strong>1.</strong> Select a model from the list<br>
            <strong>2.</strong> Click <strong>🗑️ Delete Model</strong> button<br>
            <strong>3.</strong> Confirm deletion<br>
            <strong>4.</strong> Model is removed from your system
        </div>
        
        <div class="warning">
            ⚠️ <strong>Note:</strong> You cannot delete the currently active default model. Set a different model as default first.
        </div>
        
        <h2>✅ Success Checklist</h2>
        <p>After pulling a model, verify:</p>
        <ul>
            <li>✓ Model appears in "Available Models" list</li>
            <li>✓ Has a checkmark (✓) next to it</li>
            <li>✓ No error messages in Diagnostics section</li>
            <li>✓ Can select it in the list</li>
            <li>✓ Can set it as default (double-click works)</li>
        </ul>
        
        <div class="success">
            If all items are checked, you're ready to go! 🎉
        </div>
        
        <h2>❓ Common Questions</h2>
        
        <p><strong>Q: Can I use the app while downloading?</strong><br>
        A: Yes! Downloads happen in the background.</p>
        
        <p><strong>Q: Do I need to keep this dialog open?</strong><br>
        A: No, you can close it. The download continues.</p>
        
        <p><strong>Q: How much disk space do I need?</strong><br>
        A: At least 10-20 GB free for multiple models.</p>
        
        <p><strong>Q: Can I download multiple models?</strong><br>
        A: Yes! Pull as many as you need and switch between them.</p>
        
        <p><strong>Q: Do models work offline?</strong><br>
        A: Yes! Once downloaded, they work without internet.</p>
        
        <h2>🌐 More Information</h2>
        <ul>
            <li><strong>Ollama Website:</strong> <a href="https://ollama.ai">https://ollama.ai</a></li>
            <li><strong>Model Library:</strong> <a href="https://ollama.ai/library">https://ollama.ai/library</a></li>
            <li><strong>Ollama Documentation:</strong> <a href="https://github.com/ollama/ollama">GitHub</a></li>
        </ul>
        
        <p style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #ddd; color: #666;">
            <em>Need more help? Check the Diagnostics section in the main dialog for detailed status messages.</em>
        </p>
        """
        
        help_text = QTextBrowser()
        help_text.setReadOnly(True)
        help_text.setHtml(help_html)
        help_text.setOpenExternalLinks(True)
        content_layout.addWidget(help_text)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        docs_btn = QPushButton("📖 Open Full Documentation")
        docs_btn.clicked.connect(self._open_docs)
        docs_btn.setToolTip("Open detailed guides in your default browser")
        button_layout.addWidget(docs_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _open_docs(self):
        """Open full documentation files."""
        import os
        from pathlib import Path
        
        # Get the app directory
        app_dir = Path(__file__).parent.parent.parent
        
        # Documentation files
        docs = [
            app_dir / "PULL_MODEL_QUICKSTART.md",
            app_dir / "HOW_TO_PULL_MODELS.md",
            app_dir / "PULL_MODEL_VISUAL_GUIDE.md"
        ]
        
        # Find which docs exist
        existing_docs = [doc for doc in docs if doc.exists()]
        
        if existing_docs:
            # Open the first available doc
            doc_path = existing_docs[0]
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(doc_path)))
            logger.info(f"Opened documentation: {doc_path}")
        else:
            QMessageBox.information(
                self,
                "Documentation",
                "Documentation files are located in the app folder:\n"
                "- PULL_MODEL_QUICKSTART.md\n"
                "- HOW_TO_PULL_MODELS.md\n"
                "- PULL_MODEL_VISUAL_GUIDE.md\n\n"
                "Open these files in a text editor or Markdown viewer."
            )


class ModelCheckThread(QThread):
    """Thread for checking Ollama status without blocking UI."""
    
    status_checked = Signal(bool, str, list)  # success, message, models
    
    def __init__(self, adapter: OllamaAdapter):
        super().__init__()
        self.adapter = adapter
    
    def run(self):
        """Check Ollama connection and available models."""
        try:
            # Check connection
            is_connected = self.adapter.verify_connection()
            
            if is_connected:
                # Get models
                models = self.adapter.list_models()
                self.status_checked.emit(True, "Connected to Ollama", models)
            else:
                self.status_checked.emit(False, "Cannot connect to Ollama service", [])
        except Exception as e:
            logger.error(f"Error checking Ollama status: {e}")
            self.status_checked.emit(False, f"Error: {str(e)}", [])


class AIModelDialog(QDialog):
    """
    AI Model Manager dialog.
    
    Features:
    - Real-time connection status
    - Model list and management
    - Quick diagnostics
    - Model download/pull
    - Configuration display
    """
    
    status_changed = Signal(bool)  # Emitted when status changes (True=OK, False=Error)
    
    def __init__(self, llm_adapter: OllamaAdapter, parent: Optional[QWidget] = None):
        """
        Initialize AI Model dialog.
        
        Args:
            llm_adapter: OllamaAdapter instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.adapter = llm_adapter
        self._status_ok = False
        self._check_thread = None
        self._pull_thread = None
        self._available_models = []
        
        self._setup_ui()
        self._apply_style_system()
        self._check_status()
        
        logger.debug("AI Model dialog initialized")
    
    def _setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("AI Model Manager")
        self.setMinimumSize(750, 650)
        
        layout = QVBoxLayout(self)
        
        # Status header with color-coded indicator
        status_header = self._create_status_header()
        layout.addWidget(status_header)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Models
        models_tab = QWidget()
        models_layout = QVBoxLayout(models_tab)
        
        # Dashboard
        dashboard = self._create_dashboard_widget()
        models_layout.addWidget(dashboard)
        
        # Model list
        model_group = self._create_model_group()
        models_layout.addWidget(model_group, 1)
        
        # Model type defaults
        model_defaults_group = self._create_model_defaults_group()
        models_layout.addWidget(model_defaults_group)
        
        self.tab_widget.addTab(models_tab, "🤖 Models")
        
        # Tab 2: Connection & Settings
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # Connection info
        connection_group = self._create_connection_group()
        settings_layout.addWidget(connection_group)
        
        # Add LLM settings from original layout
        settings_layout.addStretch()
        self.tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        # Tab 3: Diagnostics
        diagnostics_tab = QWidget()
        diagnostics_layout = QVBoxLayout(diagnostics_tab)
        
        # Diagnostics section
        diagnostics_group = self._create_diagnostics_group()
        diagnostics_layout.addWidget(diagnostics_group)
        
        diagnostics_layout.addStretch()
        self.tab_widget.addTab(diagnostics_tab, "🔍 Diagnostics")
        
        layout.addWidget(self.tab_widget, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh Status")
        self.refresh_btn.clicked.connect(self._check_status)
        button_layout.addWidget(self.refresh_btn)
        
        help_btn = QPushButton("❓ How to Pull Models")
        help_btn.clicked.connect(self._show_help)
        help_btn.setToolTip("Show guide on downloading and using AI models")
        button_layout.addWidget(help_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_status_header(self) -> QWidget:
        """Create status header with large indicator."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Large status dot
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #888888; font-size: 32px;")
        layout.addWidget(self.status_dot)
        
        # Status text
        status_text_layout = QVBoxLayout()
        self.status_title = QLabel("Checking AI Model Status...")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.status_title.setFont(title_font)
        status_text_layout.addWidget(self.status_title)
        
        self.status_subtitle = QLabel("Please wait...")
        self.status_subtitle.setStyleSheet("color: #888888;")
        status_text_layout.addWidget(self.status_subtitle)
        
        layout.addLayout(status_text_layout, 1)
        
        # Test connection button
        self.test_btn = QPushButton("🔍 Test Connection")
        self.test_btn.clicked.connect(self._check_status)
        layout.addWidget(self.test_btn)
        
        return widget
    
    def _create_connection_group(self) -> QGroupBox:
        """Create connection info group."""
        group = QGroupBox("Connection Settings & Model Usage")
        layout = QFormLayout(group)
        
        self.host_label = QLabel()
        layout.addRow("Ollama Host:", self.host_label)
        
        # Divider
        divider1 = QLabel()
        divider1.setStyleSheet("color: #888888;")
        divider1.setText("─" * 50)
        layout.addRow("", divider1)
        
        # Model usage section
        usage_label = QLabel("<b>Model Usage:</b>")
        layout.addRow("", usage_label)
        
        self.vision_model_label = QLabel()
        self.vision_model_label.setWordWrap(True)
        layout.addRow("🖼️ Vision (images):", self.vision_model_label)
        
        self.llm_model_label = QLabel()
        self.llm_model_label.setWordWrap(True)
        layout.addRow("🤖 LLM (text/tags):", self.llm_model_label)
        
        self.ocr_model_label = QLabel()
        self.ocr_model_label.setWordWrap(True)
        layout.addRow("📄 OCR (documents):", self.ocr_model_label)
        
        # Divider
        divider2 = QLabel()
        divider2.setStyleSheet("color: #888888;")
        divider2.setText("─" * 50)
        layout.addRow("", divider2)
        
        # LLM settings
        settings_label = QLabel("<b>LLM Settings:</b>")
        layout.addRow("", settings_label)
        
        self.temperature_label = QLabel()
        layout.addRow("Temperature:", self.temperature_label)
        
        self.max_tokens_label = QLabel()
        layout.addRow("Max Tokens:", self.max_tokens_label)
        
        # Update labels
        self.host_label.setText(self.adapter.host)
        self.llm_model_label.setText(f"<b>{self.adapter.model_name}</b> (for descriptions, classifications)")
        self.temperature_label.setText(str(self.adapter.temperature))
        self.max_tokens_label.setText(str(self.adapter.max_tokens))
        
        # Vision models info (will be updated after status check)
        self.vision_model_label.setText("<i>Checking available models...</i>")
        
        # OCR info
        self.ocr_model_label.setText("<b>Tesseract</b> (external OCR engine, not Ollama)")
        
        return group
    
    def _create_model_group(self) -> QGroupBox:
        """Create model list group with enhanced filtering."""
        group = QGroupBox("Available Models")
        layout = QVBoxLayout(group)
        
        # Enhanced search and filter toolbar
        filter_toolbar = QHBoxLayout()
        
        # Search with integrated icon
        search_layout = QHBoxLayout()
        search_icon = QLabel("🔍")
        search_layout.addWidget(search_icon)
        
        self.model_search = QLineEdit()
        self.model_search.setPlaceholderText("Search models...")
        self.model_search.textChanged.connect(self._filter_model_list)
        self.model_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
                background-color: #2a2a2a;
            }
        """)
        search_layout.addWidget(self.model_search, 1)
        filter_toolbar.addLayout(search_layout, 1)
        
        # Model type filter dropdown
        self.model_type_filter = QComboBox()
        self.model_type_filter.addItem("All Models", None)
        self.model_type_filter.addItem("Vision Models", "vision")
        self.model_type_filter.addItem("Text Models", "text")
        self.model_type_filter.currentIndexChanged.connect(self._filter_model_list)
        filter_toolbar.addWidget(self.model_type_filter)
        
        layout.addLayout(filter_toolbar)
        
        # Model list with improved styling
        self.model_list = QListWidget()
        self.model_list.setAlternatingRowColors(True)
        self.model_list.itemDoubleClicked.connect(self._on_model_double_clicked)
        self.model_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
                background-color: #1e1e1e;
                alternate-background-color: #282828;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #2a5d8c;
                color: white;
            }
        """)
        layout.addWidget(self.model_list, 1)
        
        # Model action buttons
        model_btn_layout = QHBoxLayout()
        
        self.set_default_btn = QPushButton("⭐ Set as Default")
        self.set_default_btn.setEnabled(False)
        self.set_default_btn.clicked.connect(self._set_default_model)
        self.set_default_btn.setToolTip("Set selected model as the default for processing")
        model_btn_layout.addWidget(self.set_default_btn)
        
        self.delete_model_btn = QPushButton("🗑️ Delete Model")
        self.delete_model_btn.setEnabled(False)
        self.delete_model_btn.clicked.connect(self._delete_model)
        self.delete_model_btn.setToolTip("Remove selected model from system")
        model_btn_layout.addWidget(self.delete_model_btn)
        
        model_btn_layout.addStretch()
        
        layout.addLayout(model_btn_layout)
        
        # Enable buttons when selection changes
        self.model_list.itemSelectionChanged.connect(self._on_model_selection_changed)
        
        # Pull model section
        pull_layout = QHBoxLayout()
        
        self.pull_input = QLineEdit()
        self.pull_input.setPlaceholderText("Enter model name (e.g., llama3.2)")
        pull_layout.addWidget(self.pull_input, 1)
        
        self.pull_btn = QPushButton("📥 Pull Model")
        self.pull_btn.clicked.connect(self._pull_model)
        pull_layout.addWidget(self.pull_btn)
        
        self.copy_cmd_btn = QPushButton("📋 Copy Command")
        self.copy_cmd_btn.clicked.connect(self._copy_pull_command)
        self.copy_cmd_btn.setToolTip("Copy ollama pull command to clipboard")
        pull_layout.addWidget(self.copy_cmd_btn)
        
        layout.addLayout(pull_layout)
        
        # Pull progress bar
        self.pull_progress = QProgressBar()
        self.pull_progress.setVisible(False)
        self.pull_progress.setTextVisible(True)
        layout.addWidget(self.pull_progress)
        
        # Legend
        legend_label = QLabel(
            "<div style='padding: 8px; background-color: #2a2a2a; border-radius: 4px;'>"
            "<b>Legend:</b><br>"
            "<span style='color: #4CAF50;'>⭐ Green background</span> = Default LLM (used for text/descriptions)<br>"
            "<span style='color: cyan;'>Cyan text</span> = Vision model (auto-selected for images)<br>"
            "📄 OCR uses Tesseract (external, not Ollama)"
            "</div>"
        )
        legend_label.setWordWrap(True)
        layout.addWidget(legend_label)
        
        # Help text
        help_label = QLabel("💡 Tip: Double-click a model to set it as default LLM, or pull new models above")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888888; padding: 5px;")
        layout.addWidget(help_label)
        
        return group
    
    def _create_model_defaults_group(self) -> QGroupBox:
        """Create model type defaults group with cards layout."""
        group = QGroupBox("Model Type Defaults")
        group.setToolTip("Set specific models for each task type")
        
        # Use a grid layout for card arrangement
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # Vision card
        vision_card = QGroupBox("👁️ Vision")
        vision_card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3949AB;
                border-radius: 6px;
                background-color: rgba(57, 73, 171, 0.1);
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #3949AB;
            }
        """)
        vision_layout = QVBoxLayout(vision_card)
        self.vision_default_combo = QComboBox()
        self.vision_default_combo.addItem("(Use general default)", None)
        self.vision_default_combo.currentIndexChanged.connect(self._on_vision_default_changed)
        self.vision_default_combo.setMinimumWidth(150)
        vision_desc = QLabel("For image analysis")
        vision_desc.setStyleSheet("color: #888888; font-style: italic;")
        vision_layout.addWidget(self.vision_default_combo)
        vision_layout.addWidget(vision_desc)
        layout.addWidget(vision_card, 0, 0)
        
        # OCR card
        ocr_card = QGroupBox("📝 OCR")
        ocr_card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #43A047;
                border-radius: 6px;
                background-color: rgba(67, 160, 71, 0.1);
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #43A047;
            }
        """)
        ocr_layout = QVBoxLayout(ocr_card)
        self.ocr_default_combo = QComboBox()
        self.ocr_default_combo.addItem("(Use general default)", None)
        self.ocr_default_combo.currentIndexChanged.connect(self._on_ocr_default_changed)
        self.ocr_default_combo.setMinimumWidth(150)
        ocr_desc = QLabel("For text classification")
        ocr_desc.setStyleSheet("color: #888888; font-style: italic;")
        ocr_layout.addWidget(self.ocr_default_combo)
        ocr_layout.addWidget(ocr_desc)
        layout.addWidget(ocr_card, 0, 1)
        
        # Text card
        text_card = QGroupBox("📄 Text")
        text_card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #FB8C00;
                border-radius: 6px;
                background-color: rgba(251, 140, 0, 0.1);
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #FB8C00;
            }
        """)
        text_layout = QVBoxLayout(text_card)
        self.text_default_combo = QComboBox()
        self.text_default_combo.addItem("(Use general default)", None)
        self.text_default_combo.currentIndexChanged.connect(self._on_text_default_changed)
        self.text_default_combo.setMinimumWidth(150)
        text_desc = QLabel("For descriptions")
        text_desc.setStyleSheet("color: #888888; font-style: italic;")
        text_layout.addWidget(self.text_default_combo)
        text_layout.addWidget(text_desc)
        layout.addWidget(text_card, 0, 2)
        
        return group
    
    def _create_diagnostics_group(self) -> QGroupBox:
        """Create diagnostics group with controls."""
        group = QGroupBox("Diagnostics")
        layout = QVBoxLayout(group)
        
        # TOOLBAR WITH BUTTONS (NEW)
        toolbar = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setToolTip("Clear all diagnostic messages")
        clear_btn.clicked.connect(self._clear_diagnostics)
        toolbar.addWidget(clear_btn)
        
        export_btn = QPushButton("💾 Save Log")
        export_btn.setToolTip("Save diagnostics to file")
        export_btn.clicked.connect(self._export_diagnostics)
        toolbar.addWidget(export_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Diagnostics text with HTML support
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
    
    def _check_status(self):
        """Check Ollama status in background thread."""
        self.status_title.setText("Checking AI Model Status...")
        self.status_subtitle.setText("Please wait...")
        self.status_dot.setStyleSheet("color: #888888; font-size: 32px;")
        self.test_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        
        # Clear diagnostics
        self.diagnostics_text.clear()
        self._add_diagnostic("Checking Ollama connection...")
        
        # Start check thread
        self._check_thread = ModelCheckThread(self.adapter)
        self._check_thread.status_checked.connect(self._on_status_checked)
        self._check_thread.start()
    
    def _on_status_checked(self, success: bool, message: str, models: List[str]):
        """Handle status check result."""
        self.test_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        
        self._status_ok = success
        self._available_models = models
        
        if success:
            # Check if default model is available (with flexible matching)
            default_model = self.adapter.model_name
            model_found = self._find_matching_model(default_model, models)
            
            # Detect vision models
            vision_model_keywords = ['vision', 'vl', 'llava', 'qwen2.5vl', 'qwen2-vl', 'minicpm-v']
            available_vision_models = []
            for model in models:
                model_lower = model.lower()
                if any(keyword in model_lower for keyword in vision_model_keywords):
                    available_vision_models.append(model)
            
            # Green status
            self.status_dot.setStyleSheet("color: #4CAF50; font-size: 32px;")
            self.status_title.setText("✅ AI Models Ready")
            self.status_subtitle.setText(f"Connected • {len(models)} model(s) available")
            
            # Update dashboard metrics
            if hasattr(self, 'total_models_label'):
                self.total_models_label.setText(str(len(models)))
                self.vision_models_label.setText(str(len(available_vision_models)))
                self.default_model_label.setText(model_found or "Not Found")
            
            # Update vision model label
            if available_vision_models:
                # Show first 2 vision models
                vision_display = ", ".join(available_vision_models[:2])
                if len(available_vision_models) > 2:
                    vision_display += f" (+{len(available_vision_models) - 2} more)"
                self.vision_model_label.setText(f"<b>{vision_display}</b> (auto-selected for images)")
            else:
                self.vision_model_label.setText("<span style='color: orange;'>⚠️ No vision models found</span> (images will use fallback)")
            
            # Update model list
            self.model_list.clear()
            
            # Find the best matching default model (prefer exact match, then first match)
            default_model_item = None
            for model in models:
                # Check for exact match first
                if model == default_model:
                    default_model_item = model
                    break
            
            # If no exact match, find first fuzzy match
            if not default_model_item:
                default_model_item = self._find_matching_model(default_model, models)
            
            # Now populate the list, marking models by type
            for model in models:
                is_default = (model == default_model_item)
                is_vision = model in available_vision_models
                
                # Build display text with emoji indicators
                display_text = f"✓ {model}"
                tags = []
                
                if is_default:
                    tags.append("default LLM")
                if is_vision:
                    tags.append("vision")
                
                if tags:
                    display_text += f" ({', '.join(tags)})"
                    if is_default:
                        display_text = f"⭐ {model} ({', '.join(tags)})"
                
                item = QListWidgetItem(display_text)
                
                # Color coding
                if is_default:
                    item.setBackground(Qt.GlobalColor.darkGreen)
                elif is_vision:
                    item.setForeground(Qt.GlobalColor.cyan)
                
                self.model_list.addItem(item)
            
            # Diagnostics
            self._add_diagnostic(f"✅ Connected to {self.adapter.host}")
            self._add_diagnostic(f"✅ Found {len(models)} model(s)")
            
            if model_found:
                self._add_diagnostic(f"✅ Default LLM model '{default_model}' is available (as '{model_found}')")
            else:
                self._add_diagnostic(f"⚠️  Default LLM model '{default_model}' NOT found!")
                self._add_diagnostic(f"   Available models: {', '.join(models[:3])}")
                if len(models) > 3:
                    self._add_diagnostic(f"   ...and {len(models) - 3} more")
                self._add_diagnostic(f"   To pull: ollama pull {default_model}")
            
            # Vision model diagnostics
            if available_vision_models:
                self._add_diagnostic(f"✅ Found {len(available_vision_models)} vision model(s): {', '.join(available_vision_models)}")
                self._add_diagnostic("   Vision models are auto-selected when processing images")
            else:
                self._add_diagnostic("⚠️  No vision models detected")
                self._add_diagnostic("   Recommended: ollama pull qwen2.5vl:7b")
                self._add_diagnostic("   Or: ollama pull llava:7b")
            
            # Populate model defaults combo boxes
            self._populate_model_defaults_combos()
        else:
            # Red status
            self.status_dot.setStyleSheet("color: #F44336; font-size: 32px;")
            self.status_title.setText("❌ AI Models Not Available")
            self.status_subtitle.setText(message)
            
            # Clear model list
            self.model_list.clear()
            item = QListWidgetItem("No models found - Ollama may not be running")
            item.setForeground(Qt.GlobalColor.red)
            self.model_list.addItem(item)
            
            # Diagnostics
            self._add_diagnostic(f"❌ Cannot connect to {self.adapter.host}")
            self._add_diagnostic("")
            self._add_diagnostic("Troubleshooting steps:")
            self._add_diagnostic("1. Check if Ollama is installed")
            self._add_diagnostic("   • Download from: https://ollama.ai")
            self._add_diagnostic("2. Start Ollama service:")
            self._add_diagnostic("   • Run: ollama serve")
            self._add_diagnostic("3. Verify the host URL in Settings")
            self._add_diagnostic(f"   • Current: {self.adapter.host}")
            self._add_diagnostic("4. Pull a model:")
            self._add_diagnostic(f"   • Run: ollama pull {self.adapter.model_name}")
        
        # Emit status signal
        self.status_changed.emit(self._status_ok)
    
    def _models_match(self, model1: str, model2: str) -> bool:
        """
        Check if two model names match (handles :latest tag).
        
        Args:
            model1: First model name
            model2: Second model name
            
        Returns:
            True if models match
        """
        # Normalize names by removing :latest suffix
        name1 = model1.split(':')[0]
        name2 = model2.split(':')[0]
        return name1 == name2
    
    def _find_matching_model(self, model_name: str, available_models: List[str]) -> Optional[str]:
        """
        Find a matching model in the available models list.
        
        Args:
            model_name: Model name to find
            available_models: List of available models
            
        Returns:
            Matching model name or None
        """
        for model in available_models:
            if self._models_match(model, model_name):
                return model
        return None
    
    def _add_diagnostic(self, message: str):
        """Add diagnostic message with timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add timestamp prefix
        timestamped_msg = f"[{timestamp}] {message}"
        
        # Append with auto-scroll to bottom
        cursor = self.diagnostics_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.diagnostics_text.setTextCursor(cursor)
        self.diagnostics_text.insertPlainText(timestamped_msg + "\n")
        
        # Auto-scroll to latest message
        scrollbar = self.diagnostics_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _filter_model_list(self):
        """Filter model list by search text and model type."""
        search_text = self.model_search.text().lower()
        
        # Get selected model type filter (if any)
        model_type = None
        if hasattr(self, 'model_type_filter'):
            model_type = self.model_type_filter.currentData()
        
        for i in range(self.model_list.count()):
            item = self.model_list.item(i)
            text = item.text().lower()
            
            # Text matching
            text_matches = search_text in text or not search_text
            
            # Model type matching
            type_matches = True
            if model_type:
                if model_type == "vision":
                    # Check for vision keywords
                    type_matches = any(keyword in text for keyword in 
                                     ['vision', 'vl', 'llava', 'qwen2.5vl', 'qwen2-vl', 'minicpm-v'])
                elif model_type == "text":
                    # Anything that's not explicitly marked as vision
                    type_matches = not any(keyword in text for keyword in 
                                         ['vision', 'vl', 'llava', 'qwen2.5vl', 'qwen2-vl', 'minicpm-v'])
            
            # Show item only if it matches both filters
            item.setHidden(not (text_matches and type_matches))
    
    def _on_model_selection_changed(self):
        """Handle model list selection change."""
        has_selection = len(self.model_list.selectedItems()) > 0
        self.set_default_btn.setEnabled(has_selection)
        self.delete_model_btn.setEnabled(has_selection)
    
    def _on_model_double_clicked(self, item: QListWidgetItem):
        """Handle model double-click to set as default."""
        self._set_default_model()
    
    def _set_default_model(self):
        """Set selected model as default."""
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            return
        
        # Extract model name from item text (remove emoji and labels)
        item_text = selected_items[0].text()
        # Remove emojis and (default) label
        model_name = re.sub(r'^[⭐✓]\s+', '', item_text)
        model_name = re.sub(r'\s+\(default\)$', '', model_name)
        
        # Confirm change
        reply = QMessageBox.question(
            self,
            "Set Default Model",
            f"Set '{model_name}' as the default model?\n\n"
            f"This will be used for all AI processing tasks.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Update adapter
            self.adapter.model_name = model_name
            
            # PERSIST TO CONFIG FILE (FIX: Actually save now!)
            try:
                self.adapter.config.set("ollama.default_model", model_name, save=True)
                self._add_diagnostic(f"✅ Default model changed to: {model_name} (saved)")
            except Exception as e:
                self._add_diagnostic(f"⚠️ Model changed but failed to save: {str(e)}")
                logger.error(f"Failed to save default model: {e}")
            
            # Refresh display
            self._check_status()
    
    def _delete_model(self):
        """Delete selected model."""
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            return
        
        # Extract model name
        item_text = selected_items[0].text()
        model_name = re.sub(r'^[⭐✓]\s+', '', item_text)
        model_name = re.sub(r'\s+\(default\)$', '', model_name)
        
        # Prevent deleting default model
        if self._models_match(model_name, self.adapter.model_name):
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"Cannot delete the default model '{model_name}'.\n\n"
                f"Set a different model as default first."
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Model",
            f"Are you sure you want to delete '{model_name}'?\n\n"
            f"This will remove the model from your system.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._add_diagnostic(f"Deleting model: {model_name}...")
            try:
                result = subprocess.run(
                    ['ollama', 'rm', model_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self._add_diagnostic(f"✅ Successfully deleted: {model_name}")
                    # Refresh model list
                    QTimer.singleShot(500, self._check_status)
                else:
                    self._add_diagnostic(f"❌ Failed to delete: {result.stderr}")
            except Exception as e:
                self._add_diagnostic(f"❌ Error deleting model: {str(e)}")
    
    def _copy_pull_command(self):
        """Copy ollama pull command to clipboard."""
        model_name = self.pull_input.text().strip()
        if not model_name:
            model_name = self.adapter.model_name
        
        command = f"ollama pull {model_name}"
        clipboard = QApplication.clipboard()
        clipboard.setText(command)
        
        self._add_diagnostic(f"📋 Copied to clipboard: {command}")
        QTimer.singleShot(2000, lambda: self._add_diagnostic("   Paste in terminal to pull model"))
    
    def _pull_model(self):
        """Pull a model using ollama CLI."""
        model_name = self.pull_input.text().strip()
        if not model_name:
            self._add_diagnostic("")
            self._add_diagnostic("⚠️  Please enter a model name")
            return
        
        # Confirm pull
        reply = QMessageBox.question(
            self,
            "Pull Model",
            f"Download model '{model_name}' from Ollama?\n\n"
            f"This may take several minutes depending on model size.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._add_diagnostic("")
            self._add_diagnostic(f"📥 Pulling model: {model_name}")
            self._add_diagnostic("   This may take a few minutes...")
            
            # Show progress bar
            self.pull_progress.setVisible(True)
            self.pull_progress.setRange(0, 0)  # Indeterminate
            self.pull_progress.setFormat(f"Downloading {model_name}...")
            
            # Disable pull button during download
            self.pull_btn.setEnabled(False)
            self.pull_input.setEnabled(False)
            
            # Start pull thread
            self._pull_thread = ModelPullThread(model_name)
            self._pull_thread.pull_progress.connect(self._on_pull_progress)
            self._pull_thread.pull_completed.connect(self._on_pull_completed)
            self._pull_thread.start()
    
    def _on_pull_progress(self, model_name: str, progress_text: str):
        """Handle pull progress update."""
        # Update progress bar text
        self.pull_progress.setFormat(progress_text)
        self._add_diagnostic(f"   {progress_text}")
    
    def _on_pull_completed(self, model_name: str, success: bool, message: str):
        """Handle pull completion."""
        self.pull_progress.setVisible(False)
        self.pull_btn.setEnabled(True)
        self.pull_input.setEnabled(True)
        self.pull_input.clear()
        
        if success:
            self._add_diagnostic(f"✅ {message}")
            self._add_diagnostic("   Refreshing model list...")
            # Refresh model list after successful pull
            QTimer.singleShot(1000, self._check_status)
        else:
            self._add_diagnostic(f"❌ {message}")
    
    def _pull_model_old(self):
        """Provide instructions for pulling a model (old method)."""
        model_name = self.pull_input.text().strip()
        if not model_name:
            self._add_diagnostic("")
            self._add_diagnostic("⚠️  Please enter a model name")
            return
        
        self._add_diagnostic("")
        self._add_diagnostic(f"To pull model '{model_name}':")
        self._add_diagnostic(f"1. Open a terminal")
        self._add_diagnostic(f"2. Run: ollama pull {model_name}")
        self._add_diagnostic(f"3. Click 'Refresh Status' when complete")
        self.pull_input.clear()
    
    def _clear_diagnostics(self):
        """Clear all diagnostic messages."""
        reply = QMessageBox.question(
            self,
            "Clear Diagnostics",
            "Clear all diagnostic messages?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.diagnostics_text.clear()
    
    def _export_diagnostics(self):
        """Export diagnostics to file."""
        import datetime
        from pathlib import Path
        
        try:
            # Create logs directory if needed
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / f"diagnostics_{timestamp}.log"
            
            # Save diagnostics
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(self.diagnostics_text.toPlainText())
            
            QMessageBox.information(
                self,
                "Diagnostics Saved",
                f"Diagnostics saved to:\n{log_file}"
            )
            logger.info(f"Diagnostics exported to {log_file}")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save diagnostics: {str(e)}"
            )
            logger.error(f"Failed to export diagnostics: {e}")
    
    def _populate_model_defaults_combos(self):
        """Populate the model type defaults combo boxes with available models."""
        # Get list of available models
        available_models = self.adapter.list_models()
        
        # Clear and populate each combo
        for combo in [self.vision_default_combo, self.ocr_default_combo, self.text_default_combo]:
            # Keep the "Use general default" option
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("(Use general default)", None)
            
            for model in available_models:
                combo.addItem(model, model)
            
            combo.blockSignals(False)
        
        # Load current defaults
        self._load_model_defaults()
    
    def _load_model_defaults(self):
        """Load current model defaults from config."""
        try:
            vision_default = self.adapter.config.get('ollama_default_model_vision', None)
            ocr_default = self.adapter.config.get('ollama_default_model_ocr', None)
            text_default = self.adapter.config.get('ollama_default_model_text', None)
            
            # Set combo box selections
            self._set_combo_value(self.vision_default_combo, vision_default)
            self._set_combo_value(self.ocr_default_combo, ocr_default)
            self._set_combo_value(self.text_default_combo, text_default)
            
            # Update adapter properties
            self.adapter.default_model_vision = vision_default
            self.adapter.default_model_ocr = ocr_default
            self.adapter.default_model_text = text_default
            
        except Exception as e:
            logger.error(f"Failed to load model defaults: {e}")
    
    def _set_combo_value(self, combo: QComboBox, value: Optional[str]):
        """Set combo box to a specific value."""
        if value is None:
            combo.setCurrentIndex(0)
        else:
            index = combo.findData(value)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                combo.setCurrentIndex(0)
    
    def _on_vision_default_changed(self, index: int):
        """Handle vision model default change."""
        model = self.vision_default_combo.currentData()
        self.adapter.default_model_vision = model
        try:
            self.adapter.config.set('ollama_default_model_vision', model, save=True)
            model_name = model or "(general default)"
            self._add_diagnostic(f"✅ Vision model default set to: {model_name} (saved)")
        except Exception as e:
            self._add_diagnostic(f"⚠️ Failed to save vision default: {str(e)}")
            logger.error(f"Failed to save vision default: {e}")
    
    def _on_ocr_default_changed(self, index: int):
        """Handle OCR model default change."""
        model = self.ocr_default_combo.currentData()
        self.adapter.default_model_ocr = model
        try:
            self.adapter.config.set('ollama_default_model_ocr', model, save=True)
            model_name = model or "(general default)"
            self._add_diagnostic(f"✅ OCR model default set to: {model_name} (saved)")
        except Exception as e:
            self._add_diagnostic(f"⚠️ Failed to save OCR default: {str(e)}")
            logger.error(f"Failed to save OCR default: {e}")
    
    def _on_text_default_changed(self, index: int):
        """Handle text model default change."""
        model = self.text_default_combo.currentData()
        self.adapter.default_model_text = model
        try:
            self.adapter.config.set('ollama_default_model_text', model, save=True)
            model_name = model or "(general default)"
            self._add_diagnostic(f"✅ Text model default set to: {model_name} (saved)")
        except Exception as e:
            self._add_diagnostic(f"⚠️ Failed to save text default: {str(e)}")
            logger.error(f"Failed to save text default: {e}")
    
    def _create_dashboard_widget(self) -> QWidget:
        """Create a dashboard widget with key metrics."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Total models card
        models_card = QGroupBox("Total Models")
        models_card.setStyleSheet("QGroupBox { background-color: rgba(25, 118, 210, 0.1); border-radius: 6px; }")
        models_layout = QVBoxLayout(models_card)
        self.total_models_label = QLabel("0")
        self.total_models_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_models_label.setStyleSheet("font-size: 24pt; color: #1976D2; font-weight: bold;")
        models_layout.addWidget(self.total_models_label)
        models_layout.addWidget(QLabel("Available Models"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(models_card)
        
        # Vision models card
        vision_card = QGroupBox("Vision Models")
        vision_card.setStyleSheet("QGroupBox { background-color: rgba(0, 150, 136, 0.1); border-radius: 6px; }")
        vision_layout = QVBoxLayout(vision_card)
        self.vision_models_label = QLabel("0")
        self.vision_models_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vision_models_label.setStyleSheet("font-size: 24pt; color: #009688; font-weight: bold;")
        vision_layout.addWidget(self.vision_models_label)
        vision_layout.addWidget(QLabel("Vision-capable"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(vision_card)
        
        # Default model card
        default_card = QGroupBox("Current Default")
        default_card.setStyleSheet("QGroupBox { background-color: rgba(76, 175, 80, 0.1); border-radius: 6px; }")
        default_layout = QVBoxLayout(default_card)
        self.default_model_label = QLabel("None")
        self.default_model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_model_label.setStyleSheet("font-size: 12pt; color: #4CAF50; font-weight: bold;")
        default_layout.addWidget(self.default_model_label)
        default_layout.addWidget(QLabel("Default Model"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(default_card)
        
        return widget
        
    def _show_help(self):
        """Show help dialog with model pulling guide."""
        help_dialog = ModelPullHelpDialog(self)
        help_dialog.exec()
    
    def _apply_style_system(self):
        """Apply consistent design system to the dialog."""
        # Base style
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QLineEdit, QComboBox {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 4px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #333333;
                color: #b0b0b0;
                border: 1px solid #555;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #404040;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        
    def get_status(self) -> bool:
        """
        Get current AI model status.
        
        Returns:
            True if everything is working correctly
        """
        return self._status_ok
