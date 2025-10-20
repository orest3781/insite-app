"""
Settings dialog for configuring application preferences.

This module provides a comprehensive settings interface for:
- OCR configuration (Tesseract options)
- LLM configuration (Ollama settings)
- UI preferences (theme, font size)
- Batch processing options
- Search settings
- Path configurations
"""

from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QGroupBox,
    QFileDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QTimer

from src.core.config import ConfigManager
from src.utils.logging_utils import get_logger

logger = get_logger("ui.settings")


class SettingsDialog(QDialog):
    """
    Settings dialog for application configuration.
    
    Provides tabbed interface for editing all configuration options.
    """
    
    settings_changed = Signal()  # Emitted when settings are saved
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        """
        Initialize settings dialog.
        
        Args:
            config_manager: Configuration manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config_manager
        self.pending_changes: Dict[str, Any] = {}
        
        self._setup_ui()
        self._load_settings()
        
        logger.debug("Settings dialog initialized")
    
    def _setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add tabs
        self.tabs.addTab(self._create_ocr_tab(), "OCR")
        self.tabs.addTab(self._create_llm_tab(), "LLM")
        self.tabs.addTab(self._create_ui_tab(), "Interface")
        self.tabs.addTab(self._create_batch_tab(), "Batch Processing")
        self.tabs.addTab(self._create_search_tab(), "Search")
        self.tabs.addTab(self._create_paths_tab(), "Paths")
        
        # Status message label (initially hidden)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(30)
        self.status_label.hide()
        layout.addWidget(self.status_label)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)
    
    def _create_ocr_tab(self) -> QWidget:
        """Create OCR settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tesseract group
        tesseract_group = QGroupBox("Tesseract OCR")
        tesseract_layout = QFormLayout(tesseract_group)
        
        # Tesseract executable path
        tesseract_path_layout = QHBoxLayout()
        self.tesseract_path = QLineEdit()
        self.tesseract_path.setPlaceholderText("Path to tesseract.exe (leave empty for auto-detect)")
        tesseract_browse = QPushButton("Browse...")
        tesseract_browse.clicked.connect(self._browse_tesseract)
        tesseract_path_layout.addWidget(self.tesseract_path)
        tesseract_path_layout.addWidget(tesseract_browse)
        tesseract_layout.addRow("Tesseract Path:", tesseract_path_layout)
        
        self.ocr_mode = QComboBox()
        self.ocr_mode.addItems(["fast", "balanced", "accurate"])
        tesseract_layout.addRow("Default Mode:", self.ocr_mode)
        
        self.ocr_languages = QLineEdit()
        self.ocr_languages.setPlaceholderText("eng, fra, deu")
        tesseract_layout.addRow("Languages:", self.ocr_languages)
        
        self.ocr_psm = QComboBox()
        self.ocr_psm.addItems(["auto", "single_block", "single_line", "single_word"])
        tesseract_layout.addRow("Page Segmentation:", self.ocr_psm)
        
        self.ocr_oem = QComboBox()
        self.ocr_oem.addItems(["auto", "legacy", "lstm", "default"])
        tesseract_layout.addRow("OCR Engine Mode:", self.ocr_oem)
        
        self.ocr_retries = QSpinBox()
        self.ocr_retries.setRange(0, 5)
        tesseract_layout.addRow("Retry Count:", self.ocr_retries)
        
        self.ocr_preproc = QComboBox()
        self.ocr_preproc.addItems(["none", "light", "medium", "aggressive"])
        tesseract_layout.addRow("Preprocessing:", self.ocr_preproc)
        
        layout.addWidget(tesseract_group)
        layout.addStretch()
        
        return widget
    
    def _browse_tesseract(self):
        """Browse for Tesseract executable."""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tesseract Executable",
            "",
            "Executables (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.tesseract_path.setText(file_path)
    
    def _create_llm_tab(self) -> QWidget:
        """Create LLM settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Ollama group
        ollama_group = QGroupBox("Ollama Configuration")
        ollama_layout = QFormLayout(ollama_group)
        
        self.ollama_host = QLineEdit()
        self.ollama_host.setPlaceholderText("http://localhost:11434")
        ollama_layout.addRow("Host URL:", self.ollama_host)
        
        # Model dropdown with best available models
        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.addItems([
            "llama3.2",           # Latest Llama (Recommended)
            "llama3.2:1b",        # Lightweight version
            "llama3.1",           # Previous stable
            "qwen2.5",            # Latest Qwen (Excellent for general tasks)
            "qwen2.5:7b",         # Balanced performance
            "gemma2",             # Google's Gemma 2
            "mistral",            # Mistral AI
            "mistral-nemo",       # Mistral Nemo (12B)
            "phi3",               # Microsoft Phi-3
            "codellama",          # Code-specialized
            "deepseek-coder-v2",  # Advanced coding
            "llama2",             # Legacy support
        ])
        self.ollama_model.setCurrentText("llama3.2")
        ollama_layout.addRow("Default Model:", self.ollama_model)
        
        self.ollama_temperature = QDoubleSpinBox()
        self.ollama_temperature.setRange(0.0, 2.0)
        self.ollama_temperature.setSingleStep(0.1)
        self.ollama_temperature.setDecimals(1)
        ollama_layout.addRow("Temperature:", self.ollama_temperature)
        
        self.ollama_max_tokens = QSpinBox()
        self.ollama_max_tokens.setRange(50, 4096)
        self.ollama_max_tokens.setSingleStep(50)
        ollama_layout.addRow("Max Tokens:", self.ollama_max_tokens)
        
        self.ollama_top_p = QDoubleSpinBox()
        self.ollama_top_p.setRange(0.0, 1.0)
        self.ollama_top_p.setSingleStep(0.05)
        self.ollama_top_p.setDecimals(2)
        ollama_layout.addRow("Top P:", self.ollama_top_p)
        
        self.ollama_timeout = QSpinBox()
        self.ollama_timeout.setRange(5, 300)
        self.ollama_timeout.setSuffix(" seconds")
        ollama_layout.addRow("Timeout:", self.ollama_timeout)
        
        layout.addWidget(ollama_group)
        
        # Cloud LLM group
        cloud_group = QGroupBox("Cloud LLM (Optional)")
        cloud_layout = QFormLayout(cloud_group)
        
        self.cloud_enabled = QCheckBox("Enable cloud LLM fallback")
        cloud_layout.addRow(self.cloud_enabled)
        
        self.cloud_provider = QComboBox()
        self.cloud_provider.addItems(["None", "OpenAI", "Anthropic", "Google"])
        cloud_layout.addRow("Provider:", self.cloud_provider)
        
        self.cloud_api_key = QLineEdit()
        self.cloud_api_key.setEchoMode(QLineEdit.Password)
        self.cloud_api_key.setPlaceholderText("API Key (stored securely)")
        cloud_layout.addRow("API Key:", self.cloud_api_key)
        
        layout.addWidget(cloud_group)
        layout.addStretch()
        
        return widget
    
    def _create_ui_tab(self) -> QWidget:
        """Create UI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.ui_theme = QComboBox()
        self.ui_theme.addItems(["dark", "light"])
        appearance_layout.addRow("Theme:", self.ui_theme)
        
        self.ui_font_scale = QDoubleSpinBox()
        self.ui_font_scale.setRange(0.5, 2.0)
        self.ui_font_scale.setSingleStep(0.1)
        self.ui_font_scale.setDecimals(1)
        appearance_layout.addRow("Font Scale:", self.ui_font_scale)
        
        self.ui_show_previews = QCheckBox("Show image thumbnails")
        appearance_layout.addRow(self.ui_show_previews)
        
        self.ui_preview_size = QSpinBox()
        self.ui_preview_size.setRange(64, 512)
        self.ui_preview_size.setSingleStep(32)
        self.ui_preview_size.setSuffix(" px")
        appearance_layout.addRow("Preview Size:", self.ui_preview_size)
        
        layout.addWidget(appearance_group)
        
        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.ui_confirm_delete = QCheckBox("Confirm before deleting")
        behavior_layout.addWidget(self.ui_confirm_delete)
        
        self.ui_auto_save = QCheckBox("Auto-save changes")
        behavior_layout.addWidget(self.ui_auto_save)
        
        self.ui_restore_session = QCheckBox("Restore last session on startup")
        behavior_layout.addWidget(self.ui_restore_session)
        
        layout.addWidget(behavior_group)
        layout.addStretch()
        
        return widget
    
    def _create_batch_tab(self) -> QWidget:
        """Create batch processing settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        batch_group = QGroupBox("Batch Processing")
        batch_layout = QFormLayout(batch_group)
        
        self.batch_concurrency = QSpinBox()
        self.batch_concurrency.setRange(1, 16)
        batch_layout.addRow("Concurrency:", self.batch_concurrency)
        
        self.batch_max_retry = QSpinBox()
        self.batch_max_retry.setRange(0, 10)
        batch_layout.addRow("Max Retries:", self.batch_max_retry)
        
        self.batch_stop_on_error = QCheckBox("Stop on first error")
        batch_layout.addRow(self.batch_stop_on_error)
        
        layout.addWidget(batch_group)
        layout.addStretch()
        
        return widget
    
    def _create_search_tab(self) -> QWidget:
        """Create search settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        search_group = QGroupBox("Full-Text Search")
        search_layout = QFormLayout(search_group)
        
        self.search_fts_desc = QCheckBox("Search in descriptions")
        search_layout.addRow(self.search_fts_desc)
        
        self.search_fts_text = QCheckBox("Search in OCR text")
        search_layout.addRow(self.search_fts_text)
        
        self.search_tokenizer = QComboBox()
        self.search_tokenizer.addItems(["unicode61", "porter", "simple"])
        search_layout.addRow("Tokenizer:", self.search_tokenizer)
        
        self.search_max_time = QSpinBox()
        self.search_max_time.setRange(500, 10000)
        self.search_max_time.setSingleStep(500)
        self.search_max_time.setSuffix(" ms")
        search_layout.addRow("Max Query Time:", self.search_max_time)
        
        layout.addWidget(search_group)
        layout.addStretch()
        
        return widget
    
    def _create_paths_tab(self) -> QWidget:
        """Create paths settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        paths_group = QGroupBox("Directory Paths")
        paths_layout = QFormLayout(paths_group)
        
        # Data directory
        data_layout = QHBoxLayout()
        self.path_data = QLineEdit()
        data_layout.addWidget(self.path_data)
        data_browse = QPushButton("Browse...")
        data_browse.clicked.connect(lambda: self._browse_directory(self.path_data))
        data_layout.addWidget(data_browse)
        paths_layout.addRow("Data Directory:", data_layout)
        
        # Logs directory
        logs_layout = QHBoxLayout()
        self.path_logs = QLineEdit()
        logs_layout.addWidget(self.path_logs)
        logs_browse = QPushButton("Browse...")
        logs_browse.clicked.connect(lambda: self._browse_directory(self.path_logs))
        logs_layout.addWidget(logs_browse)
        paths_layout.addRow("Logs Directory:", logs_layout)
        
        # Models directory
        models_layout = QHBoxLayout()
        self.path_models = QLineEdit()
        models_layout.addWidget(self.path_models)
        models_browse = QPushButton("Browse...")
        models_browse.clicked.connect(lambda: self._browse_directory(self.path_models))
        models_layout.addWidget(models_browse)
        paths_layout.addRow("Models Directory:", models_layout)
        
        # Exports directory
        exports_layout = QHBoxLayout()
        self.path_exports = QLineEdit()
        exports_layout.addWidget(self.path_exports)
        exports_browse = QPushButton("Browse...")
        exports_browse.clicked.connect(lambda: self._browse_directory(self.path_exports))
        exports_layout.addWidget(exports_browse)
        paths_layout.addRow("Exports Directory:", exports_layout)
        
        layout.addWidget(paths_group)
        
        # Note about paths
        note = QLabel("Note: Paths are relative to the portable root directory")
        note.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(note)
        
        layout.addStretch()
        
        return widget
    
    def _browse_directory(self, line_edit: QLineEdit):
        """
        Browse for directory and update line edit.
        
        Args:
            line_edit: Line edit to update with selected path
        """
        current_path = line_edit.text() or "."
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            current_path,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            line_edit.setText(directory)
    
    def _load_settings(self):
        """Load current settings from config manager into UI."""
        # OCR settings
        self.tesseract_path.setText(self.config.get("paths.tesseract_cmd", "") or "")
        self.ocr_mode.setCurrentText(self.config.get("ocr.default_mode", "fast"))
        languages = self.config.get("ocr.languages", ["eng"])
        self.ocr_languages.setText(", ".join(languages) if isinstance(languages, list) else str(languages))
        self.ocr_psm.setCurrentText(self.config.get("ocr.psm", "auto"))
        self.ocr_oem.setCurrentText(self.config.get("ocr.oem", "auto"))
        self.ocr_retries.setValue(self.config.get("ocr.retries", 1))
        self.ocr_preproc.setCurrentText(self.config.get("ocr.preproc_profile", "light"))
        
        # LLM settings
        self.ollama_host.setText(self.config.get("ollama.host", "http://localhost:11434"))
        model_name = self.config.get("ollama.default_model", "llama3.2") or "llama3.2"
        self.ollama_model.setCurrentText(model_name)
        self.ollama_temperature.setValue(self.config.get("ollama.temperature", 0.2))
        self.ollama_max_tokens.setValue(self.config.get("ollama.max_tokens", 220))
        self.ollama_top_p.setValue(self.config.get("ollama.top_p", 0.9))
        self.ollama_timeout.setValue(self.config.get("ollama.timeout_s", 30))
        
        self.cloud_enabled.setChecked(self.config.get("cloud.enabled_globally", False))
        self.cloud_provider.setCurrentText(self.config.get("cloud.provider", "None") or "None")
        self.cloud_api_key.setText(self.config.get("cloud.api_key", "") or "")
        
        # UI settings
        self.ui_theme.setCurrentText(self.config.get("ui.theme", "dark"))
        self.ui_font_scale.setValue(self.config.get("ui.font_scale", 1.0))
        self.ui_show_previews.setChecked(self.config.get("ui.show_previews", True))
        self.ui_preview_size.setValue(self.config.get("ui.preview_size", 128))
        self.ui_confirm_delete.setChecked(self.config.get("ui.confirm_delete", True))
        self.ui_auto_save.setChecked(self.config.get("ui.auto_save", True))
        self.ui_restore_session.setChecked(self.config.get("ui.restore_last_session", False))
        
        # Batch settings
        self.batch_concurrency.setValue(self.config.get("batch.concurrency", 1))
        self.batch_max_retry.setValue(self.config.get("batch.max_retry_count", 1))
        self.batch_stop_on_error.setChecked(self.config.get("batch.stop_on_error", False))
        
        # Search settings
        self.search_fts_desc.setChecked(self.config.get("search.fts_descriptions_enabled", True))
        self.search_fts_text.setChecked(self.config.get("search.fts_text_enabled", False))
        self.search_tokenizer.setCurrentText(self.config.get("search.fts_tokenizer", "unicode61"))
        self.search_max_time.setValue(self.config.get("search.max_query_time_ms", 3000))
        
        # Paths
        self.path_data.setText(self.config.get("paths.data_dir", "data"))
        self.path_logs.setText(self.config.get("paths.logs_dir", "logs"))
        self.path_models.setText(self.config.get("paths.models_dir", "models"))
        self.path_exports.setText(self.config.get("paths.exports_dir", "exports"))
    
    def _gather_settings(self) -> Dict[str, Any]:
        """
        Gather settings from UI into dictionary.
        
        Returns:
            Dictionary with all current settings
        """
        settings = {}
        
        # OCR settings
        settings["paths.tesseract_cmd"] = self.tesseract_path.text() or None
        settings["ocr.default_mode"] = self.ocr_mode.currentText()
        settings["ocr.languages"] = [lang.strip() for lang in self.ocr_languages.text().split(",")]
        settings["ocr.psm"] = self.ocr_psm.currentText()
        settings["ocr.oem"] = self.ocr_oem.currentText()
        settings["ocr.retries"] = self.ocr_retries.value()
        settings["ocr.preproc_profile"] = self.ocr_preproc.currentText()
        
        # LLM settings
        settings["ollama.host"] = self.ollama_host.text()
        settings["ollama.default_model"] = self.ollama_model.currentText() or None
        settings["ollama.temperature"] = self.ollama_temperature.value()
        settings["ollama.max_tokens"] = self.ollama_max_tokens.value()
        settings["ollama.top_p"] = self.ollama_top_p.value()
        settings["ollama.timeout_s"] = self.ollama_timeout.value()
        
        settings["cloud.enabled_globally"] = self.cloud_enabled.isChecked()
        provider = self.cloud_provider.currentText()
        settings["cloud.provider"] = provider if provider != "None" else None
        settings["cloud.api_key"] = self.cloud_api_key.text() or None
        
        # UI settings
        settings["ui.theme"] = self.ui_theme.currentText()
        settings["ui.font_scale"] = self.ui_font_scale.value()
        settings["ui.show_previews"] = self.ui_show_previews.isChecked()
        settings["ui.preview_size"] = self.ui_preview_size.value()
        settings["ui.confirm_delete"] = self.ui_confirm_delete.isChecked()
        settings["ui.auto_save"] = self.ui_auto_save.isChecked()
        settings["ui.restore_last_session"] = self.ui_restore_session.isChecked()
        
        # Batch settings
        settings["batch.concurrency"] = self.batch_concurrency.value()
        settings["batch.max_retry_count"] = self.batch_max_retry.value()
        settings["batch.stop_on_error"] = self.batch_stop_on_error.isChecked()
        
        # Search settings
        settings["search.fts_descriptions_enabled"] = self.search_fts_desc.isChecked()
        settings["search.fts_text_enabled"] = self.search_fts_text.isChecked()
        settings["search.fts_tokenizer"] = self.search_tokenizer.currentText()
        settings["search.max_query_time_ms"] = self.search_max_time.value()
        
        # Paths
        settings["paths.data_dir"] = self.path_data.text()
        settings["paths.logs_dir"] = self.path_logs.text()
        settings["paths.models_dir"] = self.path_models.text()
        settings["paths.exports_dir"] = self.path_exports.text()
        
        return settings
    
    def _apply_settings(self):
        """Apply settings without closing dialog."""
        settings = self._gather_settings()
        
        # Update configuration
        for key, value in settings.items():
            self.config.set(key, value)
        
        # Save to disk
        self.config.save()
        
        logger.info("Settings applied")
        self.settings_changed.emit()
        
        # Show success message with green styling
        self.status_label.setText("✓ Settings saved successfully")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.status_label.show()
        
        # Auto-hide after 4 seconds
        QTimer.singleShot(4000, self.status_label.hide)
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        self._apply_settings()
        self.accept()

