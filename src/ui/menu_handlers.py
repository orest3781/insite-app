"""
Missing handler methods for menu actions.
"""
from PySide6.QtCore import Qt
from src.utils.logging_utils import get_logger

logger = get_logger("ui.menu_handlers")

def _refresh_all_views(self):
    """Refresh all views in the application."""
    logger.info("Refreshing all views")
    self._refresh_inventory()
    self._refresh_queue_table()
    self._refresh_results()
    self._show_notification("All views refreshed", "info")

def _toggle_always_on_top(self):
    """Toggle the always-on-top window state."""
    flags = self.windowFlags()
    if flags & Qt.WindowStaysOnTopHint:
        # Turn off always-on-top
        flags &= ~Qt.WindowStaysOnTopHint
        self._show_notification("Always on top disabled", "info")
    else:
        # Turn on always-on-top
        flags |= Qt.WindowStaysOnTopHint
        self._show_notification("Always on top enabled", "info")
    
    self.setWindowFlags(flags)
    self.show()  # Need to show window again after changing flags

def _manage_watch_folders(self):
    """Show dialog to manage watched folders."""
    logger.info("Opening watch folders management")
    # Load current watched folders
    folders = self.file_watcher.get_watch_folders()
    
    # Use a custom dialog to manage folders
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel
    
    dialog = QDialog(self)
    dialog.setWindowTitle("Manage Watch Folders")
    dialog.setMinimumSize(600, 400)
    
    layout = QVBoxLayout(dialog)
    
    # Instructions
    instructions = QLabel("Manage folders being monitored for new documents.")
    layout.addWidget(instructions)
    
    # Folder list
    folder_list = QListWidget()
    for folder in folders:
        folder_list.addItem(str(folder))
    layout.addWidget(folder_list)
    
    # Buttons
    btn_layout = QHBoxLayout()
    
    add_btn = QPushButton("Add Folder")
    add_btn.clicked.connect(lambda: self._add_watch_folder_from_dialog(folder_list))
    btn_layout.addWidget(add_btn)
    
    remove_btn = QPushButton("Remove Folder")
    remove_btn.clicked.connect(lambda: self._remove_watch_folder_from_dialog(folder_list))
    btn_layout.addWidget(remove_btn)
    
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(close_btn)
    
    layout.addLayout(btn_layout)
    
    # Show dialog
    dialog.exec()
    
    # Refresh inventory after dialog closes
    self._refresh_inventory()

def _add_watch_folder_from_dialog(self, folder_list):
    """Add a watch folder from within the manage dialog."""
    from PySide6.QtWidgets import QFileDialog
    
    folder_path = QFileDialog.getExistingDirectory(
        self,
        "Select Folder to Watch",
        str(self.portable_root)
    )
    
    if folder_path:
        self.file_watcher.add_folder(folder_path)
        folder_list.addItem(folder_path)
        self._show_notification(f"Added watch folder: {folder_path}", "info")

def _remove_watch_folder_from_dialog(self, folder_list):
    """Remove a watch folder from within the manage dialog."""
    selected_items = folder_list.selectedItems()
    if not selected_items:
        self._show_notification("No folder selected", "warning")
        return
        
    folder_path = selected_items[0].text()
    self.file_watcher.remove_folder(folder_path)
    
    # Remove from list widget
    for item in selected_items:
        folder_list.takeItem(folder_list.row(item))
        
    self._show_notification(f"Removed watch folder: {folder_path}", "info")

def _manage_tags(self):
    """Show dialog to manage document tags."""
    logger.info("Opening tag management")
    
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                  QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
                                  QHeaderView, QMessageBox, QColorDialog, QWidget)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
    
    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Tag Management")
    dialog.setMinimumSize(700, 500)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(15)  # Increase spacing between layout elements
    
    # Instructions
    instructions = QLabel("Create, edit, and delete tags for document organization.")
    instructions.setStyleSheet("font-size: 11pt; margin-bottom: 10px;")
    layout.addWidget(instructions)
    layout.addSpacing(5)  # Add space after instructions
    
    # Create input area
    input_layout = QHBoxLayout()
    input_layout.setSpacing(10)  # Increase spacing between elements
    
    tag_name_label = QLabel("Tag Name:")
    tag_name_label.setStyleSheet("font-weight: bold;")
    input_layout.addWidget(tag_name_label)
    
    tag_name_input = QLineEdit()
    tag_name_input.setMinimumWidth(200)  # Make text field wider
    tag_name_input.setPlaceholderText("Enter tag name")
    input_layout.addWidget(tag_name_input)
    
    color_label = QLabel("Color:")
    color_label.setStyleSheet("font-weight: bold; margin-left: 10px;")
    input_layout.addWidget(color_label)
    
    # Color button with preview
    selected_color = QColor("#3498db")  # Default blue
    color_preview = QPushButton()
    color_preview.setFixedSize(24, 24)
    color_preview.setStyleSheet(f"background-color: {selected_color.name()}; border: 1px solid #cccccc;")
    
    def pick_color():
        nonlocal selected_color
        color = QColorDialog.getColor(selected_color, dialog, "Select Tag Color")
        if color.isValid():
            selected_color = color
            color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #cccccc;")
    
    color_preview.clicked.connect(pick_color)
    input_layout.addWidget(color_preview)
    
    # Add tag button
    add_btn = QPushButton("Add Tag")
    add_btn.setStyleSheet("padding: 5px 15px;")
    input_layout.addWidget(add_btn)
    
    layout.addLayout(input_layout)
    layout.addSpacing(10)  # Add space before table
    
    # Create table for displaying tags
    table = QTableWidget(0, 3)  # 3 columns: Name, Color, Actions
    table.setHorizontalHeaderLabels(["Tag Name", "Color", "Actions"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    table.setStyleSheet("QHeaderView::section { padding: 6px; }")
    table.verticalHeader().setDefaultSectionSize(40)  # Increase row height
    layout.addWidget(table)
    
        # Load existing tags from database
    try:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, color FROM tags ORDER BY name")
            tags = cursor.fetchall()
            table.setRowCount(len(tags))
            
            for i, (tag_id, name, color) in enumerate(tags):
                # Name
                name_item = QTableWidgetItem(name)
                table.setItem(i, 0, name_item)
                
                # Color preview
                color_item = QTableWidgetItem("")
                color_item.setBackground(QColor(color))
                table.setItem(i, 1, color_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(8, 4, 8, 4)
                actions_layout.setSpacing(10)  # Increased spacing between buttons
                
                edit_btn = QPushButton("Edit")
                edit_btn.setProperty("tag_id", tag_id)
                edit_btn.setStyleSheet("padding: 4px 10px;")
                edit_btn.setMinimumWidth(60)  # Set minimum width for button
                edit_btn.clicked.connect(lambda checked, row=i: edit_tag(row))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setProperty("tag_id", tag_id)
                delete_btn.setStyleSheet("padding: 4px 10px;")
                delete_btn.setMinimumWidth(60)  # Set minimum width for button
                delete_btn.clicked.connect(lambda checked, row=i, tid=tag_id: delete_tag(row, tid))
                actions_layout.addWidget(delete_btn)
                
                table.setCellWidget(i, 2, actions_widget)
    except Exception as e:
        logger.error(f"Failed to load tags: {e}")
        self._show_notification(f"Error loading tags: {str(e)}", "error")
    
    # Add new tag function
    def add_tag():
        name = tag_name_input.text().strip()
        if not name:
            QMessageBox.warning(dialog, "Input Error", "Tag name cannot be empty!")
            return
            
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tags (name, color, created_at) VALUES (?, ?, ?)",
                    (name, selected_color.name(), current_time)
                )
                tag_id = cursor.lastrowid
                
                # Add to table
                row_position = table.rowCount()
                table.insertRow(row_position)
                
                # Name
                name_item = QTableWidgetItem(name)
                table.setItem(row_position, 0, name_item)
                
                # Color preview
                color_item = QTableWidgetItem("")
                color_item.setBackground(selected_color)
                table.setItem(row_position, 1, color_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(8, 4, 8, 4)
                actions_layout.setSpacing(10)  # Increased spacing between buttons
                
                edit_btn = QPushButton("Edit")
                edit_btn.setProperty("tag_id", tag_id)
                edit_btn.setStyleSheet("padding: 4px 10px;")
                edit_btn.setMinimumWidth(60)  # Set minimum width for button
                edit_btn.clicked.connect(lambda checked, row=row_position: edit_tag(row))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setProperty("tag_id", tag_id)
                delete_btn.setStyleSheet("padding: 4px 10px;")
                delete_btn.setMinimumWidth(60)  # Set minimum width for button
                delete_btn.clicked.connect(lambda checked, row=row_position, tid=tag_id: delete_tag(row, tid))
                actions_layout.addWidget(delete_btn)
                
                table.setCellWidget(row_position, 2, actions_widget)
                
                # Clear input
                tag_name_input.clear()
                self._show_notification(f"Tag '{name}' created", "success")
        except Exception as e:
            logger.error(f"Failed to create tag: {e}")
            self._show_notification(f"Error creating tag: {str(e)}", "error")
    
    # Connect add button
    add_btn.clicked.connect(add_tag)
    
    # Edit tag function
    def edit_tag(row):
        current_name = table.item(row, 0).text()
        current_color = table.item(row, 1).background().color()
        # Get the first button (Edit button) from the actions cell widget
        actions_widget = table.cellWidget(row, 2)
        buttons = actions_widget.findChildren(QPushButton)
        tag_id = buttons[0].property("tag_id")
        
        # Create edit dialog
        edit_dialog = QDialog(dialog)
        edit_dialog.setWindowTitle(f"Edit Tag: {current_name}")
        edit_dialog.setFixedSize(400, 180)  # Increased height for better spacing
        
        edit_layout = QVBoxLayout(edit_dialog)
        edit_layout.setSpacing(15)  # Increase spacing between elements
        
        # Name field
        name_layout = QHBoxLayout()
        name_layout.setSpacing(10)  # Add spacing between elements
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold;")
        name_layout.addWidget(name_label)
        
        name_input = QLineEdit(current_name)
        name_layout.addWidget(name_input)
        
        edit_layout.addLayout(name_layout)
        
        # Color field
        color_layout = QHBoxLayout()
        color_layout.setSpacing(10)  # Add spacing between elements
        color_label = QLabel("Color:")
        color_label.setStyleSheet("font-weight: bold;")
        color_layout.addWidget(color_label)
        
        edit_color = current_color
        edit_color_preview = QPushButton()
        edit_color_preview.setFixedSize(30, 30)  # Larger color preview
        edit_color_preview.setCursor(Qt.PointingHandCursor)  # Change cursor to pointing hand
        edit_color_preview.setStyleSheet(f"background-color: {edit_color.name()}; border: 1px solid #cccccc;")
        
        def pick_edit_color():
            nonlocal edit_color
            color = QColorDialog.getColor(edit_color, edit_dialog, "Select Tag Color")
            if color.isValid():
                edit_color = color
                edit_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #cccccc;")
        
        edit_color_preview.clicked.connect(pick_edit_color)
        color_layout.addWidget(edit_color_preview)
        
        edit_layout.addLayout(color_layout)
        
        # Buttons
        edit_layout.addSpacing(5)  # Add space before buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("padding: 6px 12px;")
        save_btn.setMinimumWidth(80)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 6px 12px;")
        cancel_btn.setMinimumWidth(80)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        edit_layout.addLayout(button_layout)
        
        # Connect buttons
        cancel_btn.clicked.connect(edit_dialog.reject)
        
        def save_edit():
            new_name = name_input.text().strip()
            if not new_name:
                QMessageBox.warning(edit_dialog, "Input Error", "Tag name cannot be empty!")
                return
                
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE tags SET name = ?, color = ? WHERE id = ?",
                        (new_name, edit_color.name(), tag_id)
                    )
                    
                    # Update table
                    table.item(row, 0).setText(new_name)
                    table.item(row, 1).setBackground(edit_color)
                    
                    self._show_notification(f"Tag '{new_name}' updated", "success")
                    edit_dialog.accept()
            except Exception as e:
                logger.error(f"Failed to update tag: {e}")
                self._show_notification(f"Error updating tag: {str(e)}", "error")
        
        save_btn.clicked.connect(save_edit)
        
        edit_dialog.exec()
    
    # Delete tag function
    def delete_tag(row, tag_id):
        name = table.item(row, 0).text()
        
        # Confirm deletion
        confirm = QMessageBox.question(
            dialog,
            "Confirm Deletion",
            f"Are you sure you want to delete the tag '{name}'?\n\n"
            "This will remove the tag from all documents.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    # First delete tag assignments
                    cursor.execute("DELETE FROM document_tags WHERE tag_id = ?", (tag_id,))
                    # Then delete tag
                    cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
                    
                    # Remove from table
                    table.removeRow(row)
                    
                    self._show_notification(f"Tag '{name}' deleted", "success")
            except Exception as e:
                logger.error(f"Failed to delete tag: {e}")
                self._show_notification(f"Error deleting tag: {str(e)}", "error")
    
    # Bottom buttons
    layout.addSpacing(15)  # Add space before button section
    btn_layout = QHBoxLayout()
    close_btn = QPushButton("Close")
    close_btn.setStyleSheet("padding: 8px 16px;")
    close_btn.setMinimumWidth(100)
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addStretch()
    btn_layout.addWidget(close_btn)
    
    layout.addLayout(btn_layout)
    
    # Show dialog
    dialog.exec()
    
def _add_files_to_queue(self):
    """Add files directly to the processing queue."""
    logger.info("Adding files to queue")
    
    from PySide6.QtWidgets import QFileDialog
    
    file_paths, _ = QFileDialog.getOpenFileNames(
        self,
        "Select Files to Process",
        str(self.portable_root),
        "All Files (*.*)"
    )
    
    if not file_paths:
        return  # User cancelled
        
    # Add files to queue
    for file_path in file_paths:
        self.queue_manager.add_file(file_path)
        
    self._show_notification(f"Added {len(file_paths)} file(s) to queue", "info")
    
def _show_processing_options(self):
    """Show dialog to configure processing options."""
    logger.info("Opening processing options")
    
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                  QLabel, QCheckBox, QSpinBox, QComboBox, QTabWidget,
                                  QWidget, QFormLayout, QGroupBox, QSlider)
    from PySide6.QtCore import Qt
    
    # Load current settings
    config = self.config.get_all()
    
    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Processing Options")
    dialog.setMinimumSize(700, 500)
    
    layout = QVBoxLayout(dialog)
    
    # Create tabs
    tab_widget = QTabWidget()
    layout.addWidget(tab_widget)
    
    # General Tab
    general_tab = QWidget()
    general_layout = QVBoxLayout(general_tab)
    
    # Auto-processing options
    auto_group = QGroupBox("Automatic Processing")
    auto_layout = QFormLayout(auto_group)
    
    auto_watch = QCheckBox("Monitor watch folders")
    auto_watch.setChecked(config.get("watch_enabled", True))
    auto_layout.addRow("Watch Folders:", auto_watch)
    
    auto_process = QCheckBox("Auto-process new files")
    auto_process.setChecked(config.get("auto_process", True))
    auto_layout.addRow("Processing:", auto_process)
    
    auto_enqueue = QCheckBox("Auto-enqueue unanalyzed files on startup")
    auto_enqueue.setChecked(config.get("auto_enqueue_unanalyzed", True))
    auto_layout.addRow("Startup:", auto_enqueue)
    
    general_layout.addWidget(auto_group)
    
    # Queue options
    queue_group = QGroupBox("Queue Management")
    queue_layout = QFormLayout(queue_group)
    
    max_threads = QSpinBox()
    max_threads.setMinimum(1)
    max_threads.setMaximum(16)
    max_threads.setValue(config.get("max_threads", 2))
    queue_layout.addRow("Maximum Processing Threads:", max_threads)
    
    retry_count = QSpinBox()
    retry_count.setMinimum(0)
    retry_count.setMaximum(10)
    retry_count.setValue(config.get("max_retries", 3))
    queue_layout.addRow("Max Retry Attempts:", retry_count)
    
    general_layout.addWidget(queue_group)
    
    # Interface options
    interface_group = QGroupBox("Interface")
    interface_layout = QFormLayout(interface_group)
    
    theme_selector = QComboBox()
    theme_selector.addItems(["light", "dark", "system"])
    theme_selector.setCurrentText(config.get("theme", "dark"))
    interface_layout.addRow("Theme:", theme_selector)
    
    refresh_interval = QSpinBox()
    refresh_interval.setMinimum(100)
    refresh_interval.setMaximum(5000)
    refresh_interval.setSingleStep(100)
    refresh_interval.setValue(config.get("ui_refresh_interval", 1000))
    refresh_interval.setSuffix(" ms")
    interface_layout.addRow("UI Refresh Interval:", refresh_interval)
    
    general_layout.addWidget(interface_group)
    
    # Add general tab
    tab_widget.addTab(general_tab, "General")
    
    # AI Models Tab
    models_tab = QWidget()
    models_layout = QVBoxLayout(models_tab)
    
    models_group = QGroupBox("AI Models")
    models_form = QFormLayout(models_group)
    
    auto_pull = QCheckBox("Automatically download missing models")
    auto_pull.setChecked(config.get("auto_pull_models", True))
    models_form.addRow("Auto-Download:", auto_pull)
    
    check_updates = QCheckBox("Check for model updates on startup")
    check_updates.setChecked(config.get("check_model_updates", True))
    models_form.addRow("Update Check:", check_updates)
    
    model_quality = QComboBox()
    model_quality.addItems(["Fast", "Balanced", "High Quality"])
    current_quality = config.get("model_quality", "Balanced")
    model_quality.setCurrentText(current_quality)
    models_form.addRow("Default Quality:", model_quality)
    
    models_layout.addWidget(models_group)
    
    # Performance settings
    perf_group = QGroupBox("Performance")
    perf_layout = QFormLayout(perf_group)
    
    memory_limit = QSlider(Qt.Horizontal)
    memory_limit.setMinimum(512)
    memory_limit.setMaximum(8192)
    memory_limit.setValue(config.get("memory_limit_mb", 2048))
    memory_limit.setTickInterval(512)
    memory_limit.setTickPosition(QSlider.TicksBelow)
    
    memory_label = QLabel(f"{memory_limit.value()} MB")
    memory_limit.valueChanged.connect(lambda v: memory_label.setText(f"{v} MB"))
    
    mem_layout = QHBoxLayout()
    mem_layout.addWidget(memory_limit)
    mem_layout.addWidget(memory_label)
    
    perf_layout.addRow("Memory Limit:", mem_layout)
    
    models_layout.addWidget(perf_group)
    
    # Storage group
    storage_group = QGroupBox("Storage")
    storage_layout = QFormLayout(storage_group)
    
    model_path = QLabel(str(self.portable_root / "models"))
    storage_layout.addRow("Models Directory:", model_path)
    
    models_layout.addWidget(storage_group)
    
    models_layout.addStretch()
    
    # Add AI tab
    tab_widget.addTab(models_tab, "AI Models")
    
    # Advanced Tab
    advanced_tab = QWidget()
    advanced_layout = QVBoxLayout(advanced_tab)
    
    debug_group = QGroupBox("Debugging")
    debug_layout = QFormLayout(debug_group)
    
    debug_mode = QCheckBox("Enable debug logging")
    debug_mode.setChecked(config.get("debug_mode", False))
    debug_layout.addRow("Debug Mode:", debug_mode)
    
    log_retention = QSpinBox()
    log_retention.setMinimum(1)
    log_retention.setMaximum(90)
    log_retention.setValue(config.get("log_retention_days", 7))
    log_retention.setSuffix(" days")
    debug_layout.addRow("Log Retention:", log_retention)
    
    advanced_layout.addWidget(debug_group)
    
    # Add advanced tab
    tab_widget.addTab(advanced_tab, "Advanced")
    
    # Buttons
    btn_layout = QHBoxLayout()
    save_btn = QPushButton("Save")
    cancel_btn = QPushButton("Cancel")
    defaults_btn = QPushButton("Restore Defaults")
    
    btn_layout.addWidget(defaults_btn)
    btn_layout.addStretch()
    btn_layout.addWidget(save_btn)
    btn_layout.addWidget(cancel_btn)
    
    layout.addLayout(btn_layout)
    
    # Connect buttons
    cancel_btn.clicked.connect(dialog.reject)
    
    def save_settings():
        # Build updated config
        updated_config = {
            # General
            "watch_enabled": auto_watch.isChecked(),
            "auto_process": auto_process.isChecked(),
            "auto_enqueue_unanalyzed": auto_enqueue.isChecked(),
            "max_threads": max_threads.value(),
            "max_retries": retry_count.value(),
            "theme": theme_selector.currentText(),
            "ui_refresh_interval": refresh_interval.value(),
            
            # AI Models
            "auto_pull_models": auto_pull.isChecked(),
            "check_model_updates": check_updates.isChecked(),
            "model_quality": model_quality.currentText(),
            "memory_limit_mb": memory_limit.value(),
            
            # Advanced
            "debug_mode": debug_mode.isChecked(),
            "log_retention_days": log_retention.value()
        }
        
        # Save to config
        self.config.update(updated_config)
        
        # Apply theme change if needed
        if updated_config["theme"] != config.get("theme"):
            self._apply_theme(updated_config["theme"])
        
        self._show_notification("Settings saved successfully", "success")
        dialog.accept()
    
    save_btn.clicked.connect(save_settings)
    
    def restore_defaults():
        # Set all fields to defaults
        auto_watch.setChecked(True)
        auto_process.setChecked(True)
        auto_enqueue.setChecked(True)
        max_threads.setValue(2)
        retry_count.setValue(3)
        theme_selector.setCurrentText("dark")
        refresh_interval.setValue(1000)
        auto_pull.setChecked(True)
        check_updates.setChecked(True)
        model_quality.setCurrentText("Balanced")
        memory_limit.setValue(2048)
        memory_label.setText("2048 MB")
        debug_mode.setChecked(False)
        log_retention.setValue(7)
    
    defaults_btn.clicked.connect(restore_defaults)
    
    # Show dialog
    dialog.exec()
    
def _show_db_maintenance(self):
    """Show database maintenance dialog."""
    logger.info("Opening database maintenance")
    
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                  QLabel, QTabWidget, QWidget, QProgressBar, 
                                  QTextEdit, QMessageBox, QFileDialog)
    from PySide6.QtCore import QTimer
    import sqlite3
    import time
    import os
    from datetime import datetime
    from pathlib import Path
    
    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Database Maintenance")
    dialog.setMinimumSize(700, 500)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(15)
    
    # Header section with database info
    header_widget = QWidget()
    header_widget.setStyleSheet("background-color: #2c3e50; padding: 10px; border-radius: 5px;")
    header_layout = QVBoxLayout(header_widget)
    
    # Database path
    db_path = self.db.db_path
    path_label = QLabel(f"📁 Database: {db_path}")
    path_label.setStyleSheet("color: white; font-weight: bold;")
    header_layout.addWidget(path_label)
    
    # Database info row
    info_row = QHBoxLayout()
    
    # Get database size
    try:
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        size_label = QLabel(f"💾 Size: {size_mb:.2f} MB")
        size_label.setStyleSheet("color: white;")
        info_row.addWidget(size_label)
    except Exception as e:
        logger.error(f"Error getting database size: {e}")
    
    # Schema version
    try:
        version = self.db.get_schema_version()
        version_label = QLabel(f"📋 Schema Version: {version}")
        version_label.setStyleSheet("color: white;")
        info_row.addWidget(version_label)
    except Exception as e:
        logger.error(f"Error getting schema version: {e}")
    
    info_row.addStretch()
    header_layout.addLayout(info_row)
    
    layout.addWidget(header_widget)
    
    # Tabs for different maintenance operations
    tabs = QTabWidget()
    tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #cccccc; }")
    layout.addWidget(tabs)
    
    # Status/Info Tab
    info_tab = QWidget()
    info_tab_layout = QVBoxLayout(info_tab)
    
    # Database stats
    stats_text = QTextEdit()
    stats_text.setReadOnly(True)
    info_tab_layout.addWidget(stats_text)
    
    # Function to load database statistics
    def load_db_stats():
        try:
            stats_text.clear()
            stats = []
            
            # Get schema version
            version = self.db.get_schema_version()
            stats.append(f"Schema Version: {version}")
            
            # Get table stats
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    # Skip SQLite internal tables
                    if table.startswith('sqlite_'):
                        continue
                        
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats.append(f"Table '{table}': {count} records")
                
                # Get database status
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                stats.append(f"\nIntegrity Check: {integrity}")
                
                cursor.execute("PRAGMA foreign_key_check")
                fk_errors = cursor.fetchall()
                if fk_errors:
                    stats.append(f"Foreign Key Errors: {len(fk_errors)}")
                else:
                    stats.append("Foreign Key Check: OK")
            
            # Add modified timestamp
            mod_time = datetime.fromtimestamp(os.path.getmtime(db_path))
            stats.append(f"\nLast Modified: {mod_time}")
            
            stats_text.setPlainText("\n".join(stats))
        except Exception as e:
            logger.error(f"Error loading database stats: {e}")
            stats_text.setPlainText(f"Error loading statistics: {str(e)}")
    
    # Load stats button
    refresh_stats_btn = QPushButton("Refresh Statistics")
    refresh_stats_btn.clicked.connect(load_db_stats)
    info_tab_layout.addWidget(refresh_stats_btn)
    
    # Load initial stats
    load_db_stats()
    
    # Add info tab
    tabs.addTab(info_tab, "Database Info")
    
    # Maintenance Tab
    maintenance_tab = QWidget()
    maintenance_layout = QVBoxLayout(maintenance_tab)
    
    maintenance_layout.addWidget(QLabel("Perform database maintenance operations:"))
    
    # Progress bar and status
    progress_bar = QProgressBar()
    progress_bar.setRange(0, 100)
    progress_bar.setValue(0)
    progress_bar.setVisible(False)
    maintenance_layout.addWidget(progress_bar)
    
    status_label = QLabel("")
    maintenance_layout.addWidget(status_label)
    
    # Operations buttons
    vacuum_btn = QPushButton("Vacuum Database")
    vacuum_btn.setToolTip("Rebuild the database to reclaim unused space")
    
    reindex_btn = QPushButton("Reindex Database")
    reindex_btn.setToolTip("Rebuild all indices for improved performance")
    
    check_btn = QPushButton("Check Integrity")
    check_btn.setToolTip("Verify database integrity")
    
    cleanup_btn = QPushButton("Clean Orphaned Records")
    cleanup_btn.setToolTip("Remove records with broken references")
    
    # Add buttons to layout
    ops_layout = QHBoxLayout()
    ops_layout.addWidget(vacuum_btn)
    ops_layout.addWidget(reindex_btn)
    ops_layout.addWidget(check_btn)
    ops_layout.addWidget(cleanup_btn)
    maintenance_layout.addLayout(ops_layout)
    
    # Progress reporting function
    def update_progress(value, message):
        progress_bar.setValue(value)
        status_label.setText(message)
        
    # Connect operations
    def run_vacuum():
        progress_bar.setVisible(True)
        update_progress(0, "Starting vacuum operation...")
        
        # Enable UI updating during operation
        QTimer.singleShot(100, lambda: perform_vacuum(10))
    
    def perform_vacuum(progress):
        try:
            if progress == 10:
                update_progress(10, "Starting vacuum...")
                
                # Disable buttons during operation
                vacuum_btn.setEnabled(False)
                reindex_btn.setEnabled(False)
                check_btn.setEnabled(False)
                cleanup_btn.setEnabled(False)
                
                QTimer.singleShot(100, lambda: perform_vacuum(20))
                return
                
            if progress == 20:
                update_progress(20, "Analyzing database structure...")
                QTimer.singleShot(500, lambda: perform_vacuum(40))
                return
                
            if progress == 40:
                update_progress(40, "Performing vacuum operation...")
                
                # Actually perform the vacuum
                with self.db.get_connection() as conn:
                    conn.execute("VACUUM")
                
                QTimer.singleShot(500, lambda: perform_vacuum(90))
                return
                
            if progress == 90:
                # Get new size
                size_bytes = os.path.getsize(db_path)
                size_mb = size_bytes / (1024 * 1024)
                
                update_progress(100, f"Vacuum complete. New size: {size_mb:.2f} MB")
                
                # Re-enable buttons
                vacuum_btn.setEnabled(True)
                reindex_btn.setEnabled(True)
                check_btn.setEnabled(True)
                cleanup_btn.setEnabled(True)
                
                # Update size label
                size_label.setText(f"Size: {size_mb:.2f} MB")
                
                # Refresh stats
                load_db_stats()
                
        except Exception as e:
            logger.error(f"Vacuum error: {e}")
            update_progress(0, f"Error: {str(e)}")
            
            # Re-enable buttons
            vacuum_btn.setEnabled(True)
            reindex_btn.setEnabled(True)
            check_btn.setEnabled(True)
            cleanup_btn.setEnabled(True)
    
    vacuum_btn.clicked.connect(run_vacuum)
    
    # Reindex operation
    def run_reindex():
        progress_bar.setVisible(True)
        update_progress(0, "Starting reindex operation...")
        
        # Disable buttons during operation
        vacuum_btn.setEnabled(False)
        reindex_btn.setEnabled(False)
        check_btn.setEnabled(False)
        cleanup_btn.setEnabled(False)
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get list of indices
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
                )
                indices = cursor.fetchall()
                
                total_indices = len(indices)
                if total_indices == 0:
                    update_progress(100, "No user indices found")
                    vacuum_btn.setEnabled(True)
                    reindex_btn.setEnabled(True)
                    check_btn.setEnabled(True)
                    cleanup_btn.setEnabled(True)
                    return
                
                # Reindex each one
                for i, (index_name,) in enumerate(indices):
                    progress = int((i / total_indices) * 90)
                    update_progress(progress, f"Reindexing {index_name}...")
                    cursor.execute(f"REINDEX {index_name}")
                
                update_progress(100, f"Reindex complete. Rebuilt {total_indices} indices.")
        
        except Exception as e:
            logger.error(f"Reindex error: {e}")
            update_progress(0, f"Error: {str(e)}")
        finally:
            # Re-enable buttons
            vacuum_btn.setEnabled(True)
            reindex_btn.setEnabled(True)
            check_btn.setEnabled(True)
            cleanup_btn.setEnabled(True)
    
    reindex_btn.clicked.connect(run_reindex)
    
    # Check integrity operation
    def run_integrity_check():
        progress_bar.setVisible(True)
        update_progress(0, "Starting integrity check...")
        
        # Disable buttons during operation
        vacuum_btn.setEnabled(False)
        reindex_btn.setEnabled(False)
        check_btn.setEnabled(False)
        cleanup_btn.setEnabled(False)
        
        try:
            update_progress(10, "Checking database integrity...")
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Run integrity check
                update_progress(30, "Running PRAGMA integrity_check...")
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchall()
                
                # Run foreign key check
                update_progress(60, "Running PRAGMA foreign_key_check...")
                cursor.execute("PRAGMA foreign_key_check")
                fk_result = cursor.fetchall()
                
                # Check for errors
                has_integrity_errors = len(integrity_result) > 1 or integrity_result[0][0] != "ok"
                has_fk_errors = len(fk_result) > 0
                
                if has_integrity_errors or has_fk_errors:
                    error_msg = "Database integrity issues found:\n\n"
                    
                    if has_integrity_errors:
                        error_msg += f"Integrity errors: {len(integrity_result)}\n"
                        for i, (msg,) in enumerate(integrity_result):
                            if i < 10:  # Show first 10 errors
                                error_msg += f"- {msg}\n"
                            else:
                                error_msg += f"... and {len(integrity_result) - 10} more errors\n"
                                break
                    
                    if has_fk_errors:
                        error_msg += f"\nForeign key errors: {len(fk_result)}\n"
                        for i, error_details in enumerate(fk_result):
                            if i < 10:  # Show first 10 errors
                                error_msg += f"- {error_details}\n"
                            else:
                                error_msg += f"... and {len(fk_result) - 10} more errors\n"
                                break
                    
                    update_progress(100, "Integrity check complete - ERRORS FOUND")
                    
                    # Show detailed error dialog
                    QMessageBox.critical(dialog, "Integrity Check Failed", error_msg)
                else:
                    update_progress(100, "Integrity check passed - No issues found")
            
        except Exception as e:
            logger.error(f"Integrity check error: {e}")
            update_progress(0, f"Error: {str(e)}")
        finally:
            # Re-enable buttons
            vacuum_btn.setEnabled(True)
            reindex_btn.setEnabled(True)
            check_btn.setEnabled(True)
            cleanup_btn.setEnabled(True)
            
            # Refresh stats
            load_db_stats()
    
    check_btn.clicked.connect(run_integrity_check)
    
    # Cleanup operation
    def run_cleanup():
        progress_bar.setVisible(True)
        update_progress(0, "Starting orphaned record cleanup...")
        
        # Disable buttons during operation
        vacuum_btn.setEnabled(False)
        reindex_btn.setEnabled(False)
        check_btn.setEnabled(False)
        cleanup_btn.setEnabled(False)
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # List of cleanup operations to perform
                cleanup_operations = [
                    {
                        "name": "document_tags without documents",
                        "sql": """DELETE FROM document_tags 
                                 WHERE document_id NOT IN (SELECT id FROM documents)"""
                    },
                    {
                        "name": "document_tags without tags",
                        "sql": """DELETE FROM document_tags 
                                 WHERE tag_id NOT IN (SELECT id FROM tags)"""
                    },
                    {
                        "name": "processing_results without documents",
                        "sql": """DELETE FROM processing_results 
                                 WHERE document_id NOT IN (SELECT id FROM documents)"""
                    },
                    {
                        "name": "queue_items with invalid status",
                        "sql": """DELETE FROM queue_items 
                                 WHERE status NOT IN ('pending', 'processing', 'completed', 'failed')"""
                    },
                    {
                        "name": "orphaned documents",
                        "sql": """DELETE FROM documents 
                                 WHERE file_path NOT IN (SELECT file_path FROM file_inventory) 
                                 AND file_path NOT LIKE 'import:%'"""
                    }
                ]
                
                total_operations = len(cleanup_operations)
                total_deleted = 0
                
                # Run each cleanup operation
                for i, operation in enumerate(cleanup_operations):
                    progress = int((i / total_operations) * 80)
                    update_progress(progress, f"Cleaning {operation['name']}...")
                    
                    # Execute and get count
                    cursor.execute(f"SELECT COUNT(*) FROM ({operation['sql'].replace('DELETE FROM', 'SELECT * FROM')})")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        cursor.execute(operation['sql'])
                        total_deleted += count
                
                # Final vacuum if we deleted anything
                if total_deleted > 0:
                    update_progress(90, "Vacuuming database after cleanup...")
                    conn.execute("VACUUM")
                
                update_progress(100, f"Cleanup complete. Removed {total_deleted} orphaned records.")
                
                # Update size label
                size_bytes = os.path.getsize(db_path)
                size_mb = size_bytes / (1024 * 1024)
                size_label.setText(f"Size: {size_mb:.2f} MB")
                
                # Refresh stats
                load_db_stats()
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            update_progress(0, f"Error: {str(e)}")
        finally:
            # Re-enable buttons
            vacuum_btn.setEnabled(True)
            reindex_btn.setEnabled(True)
            check_btn.setEnabled(True)
            cleanup_btn.setEnabled(True)
    
    cleanup_btn.clicked.connect(run_cleanup)
    
    # Add maintenance tab
    tabs.addTab(maintenance_tab, "Maintenance")
    
    # Backup/Restore Tab
    backup_tab = QWidget()
    backup_layout = QVBoxLayout(backup_tab)
    
    backup_layout.addWidget(QLabel("Create database backups or restore from a previous backup:"))
    
    # Backup section
    backup_btn = QPushButton("Create Backup")
    backup_layout.addWidget(backup_btn)
    
    # Restore section
    restore_btn = QPushButton("Restore from Backup")
    backup_layout.addWidget(restore_btn)
    
    # Backup/restore status
    backup_status = QLabel("")
    backup_layout.addWidget(backup_status)
    
    # Backup function
    def create_backup():
        try:
            # Suggest filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"previewless_backup_{timestamp}.db"
            backup_dir = Path(self.portable_root) / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            backup_path, _ = QFileDialog.getSaveFileName(
                dialog,
                "Save Database Backup",
                str(backup_dir / default_name),
                "SQLite Database (*.db);;All Files (*)"
            )
            
            if not backup_path:
                return  # User cancelled
                
            # Create backup
            backup_status.setText("Creating backup...")
            
            # Make sure database is not in use
            self.db.close()  # Close any open connections
            
            # Use SQLite's backup API via a direct connection
            source_conn = sqlite3.connect(db_path)
            dest_conn = sqlite3.connect(backup_path)
            
            source_conn.backup(dest_conn)
            
            # Clean up
            source_conn.close()
            dest_conn.close()
            
            # Reopen database
            self.db.ensure_connection()
            
            backup_status.setText(f"Backup created successfully at: {backup_path}")
            
        except Exception as e:
            logger.error(f"Backup error: {e}")
            backup_status.setText(f"Error creating backup: {str(e)}")
            
            # Make sure database is reopened
            self.db.ensure_connection()
    
    backup_btn.clicked.connect(create_backup)
    
    # Restore function
    def restore_backup():
        try:
            # Warning dialog
            confirm = QMessageBox.warning(
                dialog,
                "Confirm Restore",
                "Restoring from a backup will REPLACE your current database.\n\n"
                "All changes since the backup was made will be lost!\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
                
            # Get backup file
            backup_dir = Path(self.portable_root) / "backups"
            backup_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Select Backup to Restore",
                str(backup_dir) if backup_dir.exists() else str(self.portable_root),
                "SQLite Database (*.db);;All Files (*)"
            )
            
            if not backup_path:
                return  # User cancelled
                
            # Close application database
            backup_status.setText("Preparing to restore...")
            self.db.close()  # Close any open connections
            
            # Create a backup of current database just in case
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_backup_dir = Path(self.portable_root) / "backups"
            auto_backup_dir.mkdir(exist_ok=True)
            auto_backup_path = auto_backup_dir / f"autosave_before_restore_{timestamp}.db"
            
            # Copy current database to auto-backup
            import shutil
            shutil.copy2(db_path, auto_backup_path)
            
            backup_status.setText(f"Restoring from backup: {backup_path}")
            
            # Replace database with backup
            shutil.copy2(backup_path, db_path)
            
            # Reopen database
            self.db.ensure_connection()
            
            # Refresh UI
            backup_status.setText(f"Database restored successfully from: {backup_path}")
            
            # Update info
            load_db_stats()
            
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            size_label.setText(f"Size: {size_mb:.2f} MB")
            
            # Show success message
            QMessageBox.information(
                dialog,
                "Restore Complete",
                f"Database restored successfully from backup.\n\n"
                f"A copy of your previous database was saved to:\n{auto_backup_path}\n\n"
                f"You may need to restart the application for all changes to take effect."
            )
            
        except Exception as e:
            logger.error(f"Restore error: {e}")
            backup_status.setText(f"Error restoring database: {str(e)}")
            
            # Make sure database is reopened
            self.db.ensure_connection()
    
    restore_btn.clicked.connect(restore_backup)
    
    # Add backup tab
    tabs.addTab(backup_tab, "Backup & Restore")
    
    # Bottom button bar
    btn_layout = QHBoxLayout()
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    
    btn_layout.addStretch()
    btn_layout.addWidget(close_btn)
    layout.addLayout(btn_layout)
    
    # Show dialog
    dialog.exec()
    
def _show_help_center(self):
    """Show the application help center."""
    logger.info("Opening help center")
    
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                   QLabel, QTextBrowser, QSplitter, QTreeWidget, 
                                   QTreeWidgetItem, QWidget, QStackedWidget)
    from PySide6.QtCore import Qt, QSize
    import os
    from pathlib import Path
    
    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Help Center")
    dialog.setMinimumSize(900, 600)
    
    layout = QVBoxLayout(dialog)
    
    # Header
    header_layout = QHBoxLayout()
    
    title_label = QLabel("Previewless Insight Viewer Help")
    title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    header_layout.addWidget(title_label)
    
    header_layout.addStretch()
    
    layout.addLayout(header_layout)
    
    # Main content splitter
    splitter = QSplitter(Qt.Horizontal)
    layout.addWidget(splitter)
    
    # Navigation tree
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setMinimumWidth(250)
    splitter.addWidget(tree)
    
    # Content area - using stacked widget to switch between content pages
    content_stack = QStackedWidget()
    splitter.addWidget(content_stack)
    
    # Set splitter sizes (30% navigation, 70% content)
    splitter.setSizes([300, 700])
    
    # Define help topics and content
    help_topics = {
        "getting_started": {
            "title": "Getting Started",
            "content": """
                <h1>Getting Started with Previewless Insight Viewer</h1>
                
                <p>Welcome to Previewless Insight Viewer, a powerful tool for processing and analyzing documents using AI models.</p>
                
                <h2>Quick Overview</h2>
                <p>The application is organized into three main tabs:</p>
                <ul>
                    <li><strong>Watch</strong> - Manage folders being monitored for new documents</li>
                    <li><strong>Queue</strong> - View and control document processing tasks</li>
                    <li><strong>Results</strong> - View and analyze processed documents</li>
                </ul>
                
                <h2>Setup Steps</h2>
                <ol>
                    <li>Add watch folders to monitor for new documents</li>
                    <li>Ensure AI models are downloaded (they'll be downloaded automatically if needed)</li>
                    <li>Check the queue tab to monitor processing progress</li>
                    <li>View results in the Results tab once processing is complete</li>
                </ol>
                
                <p>For more detailed information, see the sections below.</p>
            """
        },
        "watch_folders": {
            "title": "Watch Folders",
            "content": """
                <h1>Managing Watch Folders</h1>
                
                <p>Watch folders are directories that the application automatically monitors for new files.</p>
                
                <h2>Adding Watch Folders</h2>
                <ol>
                    <li>Navigate to the <strong>Watch</strong> tab</li>
                    <li>Click the <strong>Add Folder</strong> button</li>
                    <li>Select the directory you want to monitor</li>
                </ol>
                
                <h2>Removing Watch Folders</h2>
                <ol>
                    <li>Select the folder in the list</li>
                    <li>Click the <strong>Remove Folder</strong> button</li>
                </ol>
                
                <h2>Watch Folder Settings</h2>
                <p>You can configure watch folder behavior in the Processing Options dialog:</p>
                <ul>
                    <li>Auto-processing of new files</li>
                    <li>File types to monitor</li>
                    <li>Recursive folder watching</li>
                </ul>
                
                <p>Watch folders are checked every few seconds for new files matching the configured criteria.</p>
            """
        },
        "processing_queue": {
            "title": "Processing Queue",
            "content": """
                <h1>Using the Processing Queue</h1>
                
                <p>The queue manages the processing of documents through the AI models.</p>
                
                <h2>Queue Management</h2>
                <ul>
                    <li><strong>Add Files</strong> - Add files directly to the queue</li>
                    <li><strong>Start Processing</strong> - Begin processing files in the queue</li>
                    <li><strong>Pause Processing</strong> - Temporarily halt processing</li>
                    <li><strong>Stop Processing</strong> - Cancel all pending tasks</li>
                </ul>
                
                <h2>Queue Status</h2>
                <p>Files in the queue can have several statuses:</p>
                <ul>
                    <li><strong>Pending</strong> - Waiting to be processed</li>
                    <li><strong>Processing</strong> - Currently being analyzed</li>
                    <li><strong>Completed</strong> - Successfully processed</li>
                    <li><strong>Failed</strong> - Error during processing</li>
                </ul>
                
                <h2>Performance</h2>
                <p>Processing speed depends on:</p>
                <ul>
                    <li>File size and complexity</li>
                    <li>Selected AI models</li>
                    <li>System resources (CPU, RAM, GPU)</li>
                    <li>Number of processing threads (configurable in Settings)</li>
                </ul>
            """
        },
        "viewing_results": {
            "title": "Viewing Results",
            "content": """
                <h1>Working with Results</h1>
                
                <p>The Results tab shows all processed documents and their analysis outputs.</p>
                
                <h2>Results Table</h2>
                <p>The results table displays:</p>
                <ul>
                    <li>File name and location</li>
                    <li>Processing date and time</li>
                    <li>Processing status and quality</li>
                    <li>Tags and categories</li>
                </ul>
                
                <h2>Document Viewer</h2>
                <p>Click on any result to open the document viewer, which shows:</p>
                <ul>
                    <li>File metadata</li>
                    <li>Extracted content</li>
                    <li>AI analysis results</li>
                    <li>Tags and categories</li>
                </ul>
                
                <h2>Search and Filter</h2>
                <p>Use the search box to find specific documents or content. The advanced search options allow filtering by:</p>
                <ul>
                    <li>Date range</li>
                    <li>File type</li>
                    <li>Processing status</li>
                    <li>Tags and categories</li>
                    <li>Content keywords</li>
                </ul>
                
                <h2>Exporting</h2>
                <p>Results can be exported to various formats:</p>
                <ul>
                    <li>CSV for spreadsheet analysis</li>
                    <li>JSON for data processing</li>
                    <li>PDF reports</li>
                    <li>Text summaries</li>
                </ul>
            """
        },
        "ai_models": {
            "title": "AI Models",
            "content": """
                <h1>Understanding AI Models</h1>
                
                <p>Previewless Insight Viewer uses specialized AI models for document analysis.</p>
                
                <h2>Model Types</h2>
                <ul>
                    <li><strong>Text Extraction</strong> - Converts document images to text</li>
                    <li><strong>Analysis</strong> - Identifies key information and themes</li>
                    <li><strong>Classification</strong> - Categorizes documents by content</li>
                    <li><strong>Entity Recognition</strong> - Identifies people, organizations, dates, etc.</li>
                </ul>
                
                <h2>Model Management</h2>
                <p>Models are downloaded automatically when needed, but you can also:</p>
                <ul>
                    <li>Check model status in the status bar</li>
                    <li>Update models via the AI Models button</li>
                    <li>Configure model settings in Processing Options</li>
                </ul>
                
                <h2>Quality Settings</h2>
                <p>You can choose between three quality levels:</p>
                <ul>
                    <li><strong>Fast</strong> - Quicker processing, lower accuracy</li>
                    <li><strong>Balanced</strong> - Good balance of speed and accuracy</li>
                    <li><strong>High Quality</strong> - Maximum accuracy, slower processing</li>
                </ul>
                
                <p>Higher quality settings require more system resources.</p>
            """
        },
        "keyboard_shortcuts": {
            "title": "Keyboard Shortcuts",
            "content": """
                <h1>Keyboard Shortcuts</h1>
                
                <p>Previewless Insight Viewer supports the following keyboard shortcuts:</p>
                
                <h2>Application</h2>
                <table border="1" cellpadding="5">
                    <tr>
                        <th>Shortcut</th>
                        <th>Action</th>
                    </tr>
                    <tr>
                        <td>Ctrl+Q</td>
                        <td>Quit application</td>
                    </tr>
                    <tr>
                        <td>F1</td>
                        <td>Open Help Center</td>
                    </tr>
                    <tr>
                        <td>F5</td>
                        <td>Refresh current view</td>
                    </tr>
                    <tr>
                        <td>Ctrl+,</td>
                        <td>Open Settings</td>
                    </tr>
                </table>
                
                <h2>Navigation</h2>
                <table border="1" cellpadding="5">
                    <tr>
                        <th>Shortcut</th>
                        <th>Action</th>
                    </tr>
                    <tr>
                        <td>Ctrl+1</td>
                        <td>Go to Watch tab</td>
                    </tr>
                    <tr>
                        <td>Ctrl+2</td>
                        <td>Go to Queue tab</td>
                    </tr>
                    <tr>
                        <td>Ctrl+3</td>
                        <td>Go to Results tab</td>
                    </tr>
                </table>
                
                <h2>Queue Management</h2>
                <table border="1" cellpadding="5">
                    <tr>
                        <th>Shortcut</th>
                        <th>Action</th>
                    </tr>
                    <tr>
                        <td>Ctrl+A</td>
                        <td>Add files to queue</td>
                    </tr>
                    <tr>
                        <td>Ctrl+P</td>
                        <td>Start/Pause processing</td>
                    </tr>
                    <tr>
                        <td>Ctrl+S</td>
                        <td>Stop processing</td>
                    </tr>
                </table>
                
                <h2>Results</h2>
                <table border="1" cellpadding="5">
                    <tr>
                        <th>Shortcut</th>
                        <th>Action</th>
                    </tr>
                    <tr>
                        <td>Ctrl+F</td>
                        <td>Search results</td>
                    </tr>
                    <tr>
                        <td>Ctrl+E</td>
                        <td>Export selected results</td>
                    </tr>
                    <tr>
                        <td>Delete</td>
                        <td>Remove selected result</td>
                    </tr>
                </table>
            """
        },
        "troubleshooting": {
            "title": "Troubleshooting",
            "content": """
                <h1>Troubleshooting Common Issues</h1>
                
                <h2>Application Won't Start</h2>
                <ul>
                    <li>Check if another instance is already running</li>
                    <li>Verify the database file isn't locked or corrupted</li>
                    <li>Make sure you have sufficient permissions</li>
                    <li>Try running as administrator (Windows) or with sudo (Linux)</li>
                </ul>
                
                <h2>Processing Issues</h2>
                <ul>
                    <li><strong>Files not being detected</strong> - Check watch folder settings and permissions</li>
                    <li><strong>Queue stuck</strong> - Try stopping and restarting processing</li>
                    <li><strong>Processing errors</strong> - Check logs for details on specific errors</li>
                </ul>
                
                <h2>AI Model Problems</h2>
                <ul>
                    <li><strong>Models not downloading</strong> - Check internet connection and firewall settings</li>
                    <li><strong>Out of memory errors</strong> - Reduce memory limit in settings or close other applications</li>
                    <li><strong>Model loading errors</strong> - Try reinstalling models via the AI Models dialog</li>
                </ul>
                
                <h2>Database Issues</h2>
                <ul>
                    <li><strong>Database errors</strong> - Run database maintenance from the Tools menu</li>
                    <li><strong>Missing results</strong> - Check if filters are applied in the Results tab</li>
                    <li><strong>Corruption</strong> - Restore from a backup if available</li>
                </ul>
                
                <h2>General Fixes</h2>
                <ul>
                    <li>Restart the application</li>
                    <li>Check the logs for specific error messages</li>
                    <li>Update to the latest version</li>
                    <li>Clear temporary files</li>
                </ul>
            """
        },
    }
    
    # Create tree items for each topic
    topics_dict = {}
    for topic_id, topic_data in help_topics.items():
        item = QTreeWidgetItem([topic_data["title"]])
        item.setData(0, Qt.UserRole, topic_id)
        tree.addTopLevelItem(item)
        topics_dict[topic_id] = item
    
    # Create content widgets for each topic
    for topic_id, topic_data in help_topics.items():
        content_browser = QTextBrowser()
        content_browser.setHtml(topic_data["content"])
        content_browser.setOpenExternalLinks(True)
        content_stack.addWidget(content_browser)
    
    # Handle tree item selection
    def on_topic_selected():
        selected = tree.selectedItems()
        if selected:
            topic_id = selected[0].data(0, Qt.UserRole)
            index = list(help_topics.keys()).index(topic_id)
            content_stack.setCurrentIndex(index)
    
    tree.itemClicked.connect(on_topic_selected)
    
    # Select first topic by default
    tree.setCurrentItem(tree.topLevelItem(0))
    on_topic_selected()
    
    # Bottom button bar
    btn_layout = QHBoxLayout()
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addStretch()
    btn_layout.addWidget(close_btn)
    
    layout.addLayout(btn_layout)
    
    # Show dialog
    dialog.exec()
    
def _show_quickstart(self):
    """Show the quick start guide."""
    logger.info("Opening quick start guide")
    
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                  QLabel, QWizard, QWizardPage, QCheckBox,
                                  QRadioButton, QButtonGroup, QFileDialog)
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QPixmap, QFont, QIcon
    import os
    from pathlib import Path
    
    # Create wizard
    wizard = QWizard(self)
    wizard.setWindowTitle("Quick Start Guide")
    wizard.setMinimumSize(800, 600)
    wizard.setWizardStyle(QWizard.ModernStyle)
    
    # Welcome page
    welcome_page = QWizardPage()
    welcome_page.setTitle("Welcome to Previewless Insight Viewer")
    welcome_page.setSubTitle("This guide will help you get started with the application")
    
    welcome_layout = QVBoxLayout(welcome_page)
    
    welcome_text = QLabel(
        "<p>Previewless Insight Viewer helps you process and analyze documents "
        "using advanced AI models.</p>"
        "<p>This wizard will guide you through the essential steps to set up "
        "the application for first use.</p>"
        "<p>You'll learn how to:</p>"
        "<ul>"
        "<li>Configure watch folders for automatic document monitoring</li>"
        "<li>Process documents through the AI pipeline</li>"
        "<li>View and work with analysis results</li>"
        "</ul>"
        "<p>Click <b>Next</b> to begin.</p>"
    )
    welcome_text.setWordWrap(True)
    welcome_layout.addWidget(welcome_text)
    
    # Use a spacer to push content to the top
    welcome_layout.addStretch()
    
    wizard.addPage(welcome_page)
    
    # Watch folders page
    watch_page = QWizardPage()
    watch_page.setTitle("Setting Up Watch Folders")
    watch_page.setSubTitle("Configure folders for automatic document monitoring")
    
    watch_layout = QVBoxLayout(watch_page)
    
    watch_text = QLabel(
        "<p>Watch folders are directories that the application monitors for new documents.</p>"
        "<p>When new files are detected, they can be automatically added to the processing queue.</p>"
        "<p>To set up watch folders:</p>"
        "<ol>"
        "<li>Go to the <b>Watch</b> tab</li>"
        "<li>Click <b>Add Folder</b> to select directories to monitor</li>"
        "<li>Use <b>Remove Folder</b> to stop monitoring a directory</li>"
        "</ol>"
        "<p>You can also add folders now using the button below:</p>"
    )
    watch_text.setWordWrap(True)
    watch_layout.addWidget(watch_text)
    
    # Add folder button
    add_folder_btn = QPushButton("Add Watch Folder")
    
    def add_watch_folder_from_wizard():
        folder_path = QFileDialog.getExistingDirectory(
            wizard,
            "Select Folder to Watch",
            str(self.portable_root)
        )
        
        if folder_path:
            self.file_watcher.add_folder(folder_path)
            self._show_notification(f"Added watch folder: {folder_path}", "success")
    
    add_folder_btn.clicked.connect(add_watch_folder_from_wizard)
    watch_layout.addWidget(add_folder_btn)
    
    # Use a spacer to push content to the top
    watch_layout.addStretch()
    
    wizard.addPage(watch_page)
    
    # Queue page
    queue_page = QWizardPage()
    queue_page.setTitle("Processing Documents")
    queue_page.setSubTitle("Understanding the document processing queue")
    
    queue_layout = QVBoxLayout(queue_page)
    
    queue_text = QLabel(
        "<p>The <b>Queue</b> tab manages document processing.</p>"
        "<p>Key features:</p>"
        "<ul>"
        "<li><b>Add Files</b> - Manually add files to the processing queue</li>"
        "<li><b>Start Processing</b> - Begin processing documents</li>"
        "<li><b>Pause</b> - Temporarily halt processing</li>"
        "<li><b>Stop</b> - Cancel all remaining tasks</li>"
        "</ul>"
        "<p>Documents move through these states:</p>"
        "<ol>"
        "<li><b>Pending</b> - Waiting to be processed</li>"
        "<li><b>Processing</b> - Currently being analyzed</li>"
        "<li><b>Completed</b> - Analysis finished successfully</li>"
        "<li><b>Failed</b> - Error occurred during processing</li>"
        "</ol>"
    )
    queue_text.setWordWrap(True)
    queue_layout.addWidget(queue_text)
    
    queue_layout.addStretch()
    
    wizard.addPage(queue_page)
    
    # Results page
    results_page = QWizardPage()
    results_page.setTitle("Working with Results")
    results_page.setSubTitle("Viewing and analyzing processed documents")
    
    results_layout = QVBoxLayout(results_page)
    
    results_text = QLabel(
        "<p>The <b>Results</b> tab displays all processed documents.</p>"
        "<p>Key features:</p>"
        "<ul>"
        "<li><b>Search</b> - Find documents by content or metadata</li>"
        "<li><b>Filter</b> - Narrow down results by various criteria</li>"
        "<li><b>Sort</b> - Organize documents by different properties</li>"
        "<li><b>Export</b> - Save analysis results in various formats</li>"
        "</ul>"
        "<p>Click on any document to view detailed analysis results.</p>"
        "<p>You can tag documents to organize them into categories.</p>"
    )
    results_text.setWordWrap(True)
    results_layout.addWidget(results_text)
    
    results_layout.addStretch()
    
    wizard.addPage(results_page)
    
    # AI Models page
    models_page = QWizardPage()
    models_page.setTitle("AI Models")
    models_page.setSubTitle("Understanding the analysis models")
    
    models_layout = QVBoxLayout(models_page)
    
    models_text = QLabel(
        "<p>Previewless Insight Viewer uses specialized AI models for document analysis.</p>"
        "<p>These models are downloaded automatically when needed.</p>"
        "<p>You can check the status of AI models by looking at the status bar at the bottom of the window.</p>"
        "<p>The <b>AI Models</b> button shows:</p>"
        "<ul>"
        "<li><b>Green</b> - All models are available and ready</li>"
        "<li><b>Yellow</b> - Models are downloading or updating</li>"
        "<li><b>Red</b> - Issues with models</li>"
        "</ul>"
        "<p>Click on the AI Models button to manage models and see detailed status information.</p>"
    )
    models_text.setWordWrap(True)
    models_layout.addWidget(models_text)
    
    check_models_btn = QPushButton("Check AI Models Status")
    check_models_btn.clicked.connect(lambda: self._update_ai_status(True))
    models_layout.addWidget(check_models_btn)
    
    models_layout.addStretch()
    
    wizard.addPage(models_page)
    
    # Finishing page
    finish_page = QWizardPage()
    finish_page.setTitle("Ready to Go!")
    finish_page.setSubTitle("You're all set to start using Previewless Insight Viewer")
    
    finish_layout = QVBoxLayout(finish_page)
    
    finish_text = QLabel(
        "<p>Congratulations! You've completed the quick start guide.</p>"
        "<p>Here are some suggestions to get you started:</p>"
        "<ul>"
        "<li>Add some watch folders if you haven't already</li>"
        "<li>Add a few files to the processing queue</li>"
        "<li>Start processing to see the application in action</li>"
        "<li>Explore the results tab once documents are processed</li>"
        "</ul>"
        "<p>Remember, you can access help at any time by pressing F1 or using the Help menu.</p>"
        "<p>Click <b>Finish</b> to close this guide and start using the application.</p>"
    )
    finish_text.setWordWrap(True)
    finish_layout.addWidget(finish_text)
    
    # Option to show the guide at startup
    show_at_startup = QCheckBox("Show this guide when the application starts")
    show_at_startup.setChecked(self.config.get("show_quickstart_at_startup", True))
    
    def update_startup_setting(state):
        self.config.update({"show_quickstart_at_startup": state == Qt.Checked})
    
    show_at_startup.stateChanged.connect(update_startup_setting)
    finish_layout.addWidget(show_at_startup)
    
    finish_layout.addStretch()
    
    wizard.addPage(finish_page)
    
    # Show the wizard
    wizard.exec()

def _view_processed_files(self):
    """Show all processed files from the database with links to open them."""
    logger.info("Opening processed files viewer")
    
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                   QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                                   QLineEdit, QMessageBox, QWidget)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QDesktopServices, QColor
    from pathlib import Path
    import os
    
    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Processed Files")
    dialog.setMinimumSize(1000, 600)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(15)
    
    # Header
    header_widget = QWidget()
    header_widget.setStyleSheet("background-color: #2c3e50; padding: 10px; border-radius: 5px;")
    header_layout = QVBoxLayout(header_widget)
    
    title_label = QLabel("📁 Processed Files Database")
    title_label.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")
    header_layout.addWidget(title_label)
    
    subtitle_label = QLabel("View all processed files and open them directly")
    subtitle_label.setStyleSheet("color: #ecf0f1; font-size: 10pt;")
    header_layout.addWidget(subtitle_label)
    
    layout.addWidget(header_widget)
    
    # Search bar
    search_layout = QHBoxLayout()
    search_label = QLabel("🔍 Search:")
    search_label.setStyleSheet("font-weight: bold;")
    search_layout.addWidget(search_label)
    
    search_input = QLineEdit()
    search_input.setPlaceholderText("Search by filename, path, or tags...")
    search_input.setStyleSheet("padding: 8px; font-size: 10pt;")
    search_layout.addWidget(search_input)
    
    layout.addLayout(search_layout)
    
    # Files table
    table = QTableWidget(0, 6)  # 6 columns
    table.setHorizontalHeaderLabels([
        "Filename", "Path", "Pages", "Tags", "Processed Date", "Actions"
    ])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
    table.setStyleSheet("QHeaderView::section { padding: 8px; }")
    table.verticalHeader().setDefaultSectionSize(40)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    layout.addWidget(table)
    
    # Status bar
    status_label = QLabel("Loading processed files...")
    status_label.setStyleSheet("padding: 8px; background-color: #ecf0f1; border-radius: 3px;")
    layout.addWidget(status_label)
    
    # Function to load files from database
    def load_files(search_text=""):
        try:
            table.setRowCount(0)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Query to get files with their classifications
                if search_text:
                    # Search in file path and tags
                    cursor.execute("""
                        SELECT DISTINCT 
                            f.file_id,
                            f.file_path,
                            f.page_count,
                            f.analyzed_at,
                            GROUP_CONCAT(DISTINCT c.tag_text, ', ') as tags
                        FROM files f
                        LEFT JOIN classifications c ON f.file_id = c.file_id
                        WHERE f.file_path LIKE ? OR c.tag_text LIKE ?
                        GROUP BY f.file_id
                        ORDER BY f.analyzed_at DESC
                    """, (f'%{search_text}%', f'%{search_text}%'))
                else:
                    cursor.execute("""
                        SELECT 
                            f.file_id,
                            f.file_path,
                            f.page_count,
                            f.analyzed_at,
                            GROUP_CONCAT(DISTINCT c.tag_text, ', ') as tags
                        FROM files f
                        LEFT JOIN classifications c ON f.file_id = c.file_id
                        GROUP BY f.file_id
                        ORDER BY f.analyzed_at DESC
                    """)
                
                files = cursor.fetchall()
                
                if not files:
                    status_label.setText("No processed files found in database")
                    return
                
                table.setRowCount(len(files))
                
                for i, (file_id, file_path, page_count, analyzed_at, tags) in enumerate(files):
                    # Filename
                    filename = os.path.basename(file_path)
                    filename_item = QTableWidgetItem(filename)
                    filename_item.setToolTip(file_path)
                    table.setItem(i, 0, filename_item)
                    
                    # Path
                    path_item = QTableWidgetItem(file_path)
                    path_item.setToolTip(file_path)
                    table.setItem(i, 1, path_item)
                    
                    # Pages
                    pages_item = QTableWidgetItem(str(page_count) if page_count else "N/A")
                    pages_item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(i, 2, pages_item)
                    
                    # Tags
                    tags_text = tags if tags else "No tags"
                    tags_item = QTableWidgetItem(tags_text)
                    tags_item.setToolTip(tags_text)
                    table.setItem(i, 3, tags_item)
                    
                    # Processed date
                    date_item = QTableWidgetItem(analyzed_at if analyzed_at else "Unknown")
                    table.setItem(i, 4, date_item)
                    
                    # Actions buttons
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(8, 4, 8, 4)
                    actions_layout.setSpacing(8)
                    
                    # Open file button
                    open_btn = QPushButton("📂 Open")
                    open_btn.setStyleSheet("padding: 4px 10px;")
                    open_btn.setMinimumWidth(70)
                    open_btn.setToolTip("Open this file in default application")
                    open_btn.clicked.connect(lambda checked, path=file_path: open_file(path))
                    actions_layout.addWidget(open_btn)
                    
                    # Show in folder button
                    folder_btn = QPushButton("📁 Folder")
                    folder_btn.setStyleSheet("padding: 4px 10px;")
                    folder_btn.setMinimumWidth(70)
                    folder_btn.setToolTip("Show file in folder")
                    folder_btn.clicked.connect(lambda checked, path=file_path: show_in_folder(path))
                    actions_layout.addWidget(folder_btn)
                    
                    # Details button
                    details_btn = QPushButton("ℹ️ Details")
                    details_btn.setStyleSheet("padding: 4px 10px;")
                    details_btn.setMinimumWidth(70)
                    details_btn.setToolTip("View detailed information")
                    details_btn.clicked.connect(lambda checked, fid=file_id: show_details(fid))
                    actions_layout.addWidget(details_btn)
                    
                    # Check if file exists
                    if not os.path.exists(file_path):
                        # Highlight missing files
                        for col in range(6):
                            if col < 5:
                                item = table.item(i, col)
                                if item:
                                    item.setBackground(QColor("#ffebee"))
                                    item.setToolTip(f"⚠️ File not found: {file_path}")
                        open_btn.setEnabled(False)
                        folder_btn.setEnabled(False)
                        open_btn.setToolTip("⚠️ File not found")
                        folder_btn.setToolTip("⚠️ File not found")
                    
                    table.setCellWidget(i, 5, actions_widget)
                
                status_label.setText(f"✅ Showing {len(files)} processed file(s)")
                
        except Exception as e:
            logger.error(f"Error loading processed files: {e}")
            status_label.setText(f"❌ Error loading files: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Function to open a file
    def open_file(file_path):
        try:
            if not os.path.exists(file_path):
                QMessageBox.warning(
                    dialog,
                    "File Not Found",
                    f"The file no longer exists:\n{file_path}"
                )
                return
            
            # Open file with default application
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            logger.info(f"Opened file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error opening file: {e}")
            QMessageBox.critical(
                dialog,
                "Error",
                f"Failed to open file:\n{str(e)}"
            )
    
    # Function to show file in folder
    def show_in_folder(file_path):
        try:
            if not os.path.exists(file_path):
                QMessageBox.warning(
                    dialog,
                    "File Not Found",
                    f"The file no longer exists:\n{file_path}"
                )
                return
            
            # Show file in folder
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', '-R', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', os.path.dirname(file_path)])
            
            logger.info(f"Showed file in folder: {file_path}")
            
        except Exception as e:
            logger.error(f"Error showing file in folder: {e}")
            QMessageBox.critical(
                dialog,
                "Error",
                f"Failed to show file in folder:\n{str(e)}"
            )
    
    # Function to show file details
    def show_details(file_id):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get file details
                cursor.execute("""
                    SELECT 
                        f.file_path,
                        f.file_hash,
                        f.file_type,
                        f.page_count,
                        f.file_size,
                        f.analyzed_at,
                        GROUP_CONCAT(DISTINCT c.tag_text, '\n  • ') as tags,
                        d.description_text
                    FROM files f
                    LEFT JOIN classifications c ON f.file_id = c.file_id
                    LEFT JOIN descriptions d ON f.file_id = d.file_id
                    WHERE f.file_id = ?
                    GROUP BY f.file_id
                """, (file_id,))
                
                result = cursor.fetchone()
                if not result:
                    QMessageBox.warning(dialog, "Not Found", "File details not found")
                    return
                
                file_path, file_hash, file_type, page_count, file_size, analyzed_at, tags, description = result
                
                # Format file size
                if file_size:
                    if file_size < 1024:
                        size_str = f"{file_size} bytes"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.2f} KB"
                    else:
                        size_str = f"{file_size / (1024 * 1024):.2f} MB"
                else:
                    size_str = "Unknown"
                
                # Build details message
                details_text = f"""
<h2>📄 File Details</h2>

<p><b>Filename:</b> {os.path.basename(file_path)}</p>
<p><b>Path:</b> {file_path}</p>
<p><b>Type:</b> {file_type or 'Unknown'}</p>
<p><b>Size:</b> {size_str}</p>
<p><b>Pages:</b> {page_count or 'N/A'}</p>
<p><b>Processed:</b> {analyzed_at or 'Unknown'}</p>
<p><b>Hash:</b> <code>{file_hash or 'N/A'}</code></p>

<h3>🏷️ Tags:</h3>
<p style="margin-left: 20px;">
  • {tags if tags else 'No tags'}
</p>

<h3>📝 Description:</h3>
<p style="margin-left: 20px; font-style: italic;">
{description or 'No description available'}
</p>
"""
                
                # Show details dialog
                details_dialog = QDialog(dialog)
                details_dialog.setWindowTitle(f"Details: {os.path.basename(file_path)}")
                details_dialog.setMinimumSize(600, 500)
                
                details_layout = QVBoxLayout(details_dialog)
                
                from PySide6.QtWidgets import QTextBrowser
                text_browser = QTextBrowser()
                text_browser.setHtml(details_text)
                text_browser.setOpenExternalLinks(True)
                details_layout.addWidget(text_browser)
                
                close_btn = QPushButton("Close")
                close_btn.setStyleSheet("padding: 8px 16px;")
                close_btn.setMinimumWidth(100)
                close_btn.clicked.connect(details_dialog.accept)
                details_layout.addWidget(close_btn, alignment=Qt.AlignRight)
                
                details_dialog.exec()
                
        except Exception as e:
            logger.error(f"Error showing file details: {e}")
            QMessageBox.critical(
                dialog,
                "Error",
                f"Failed to load file details:\n{str(e)}"
            )
    
    # Connect search to filter
    search_input.textChanged.connect(lambda text: load_files(text))
    
    # Bottom buttons
    layout.addSpacing(10)
    btn_layout = QHBoxLayout()
    
    refresh_btn = QPushButton("🔄 Refresh")
    refresh_btn.setStyleSheet("padding: 8px 16px;")
    refresh_btn.setMinimumWidth(100)
    refresh_btn.clicked.connect(lambda: load_files(search_input.text()))
    btn_layout.addWidget(refresh_btn)
    
    btn_layout.addStretch()
    
    close_btn = QPushButton("Close")
    close_btn.setStyleSheet("padding: 8px 16px;")
    close_btn.setMinimumWidth(100)
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(close_btn)
    
    layout.addLayout(btn_layout)
    
    # Load files initially
    load_files()
    
    # Show dialog
    dialog.exec()
    
def _check_for_updates(self):
    """Check for application updates."""
    logger.info("Checking for updates")
    
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                   QLabel, QProgressBar, QTextBrowser, QMessageBox)
    from PySide6.QtCore import QTimer, QThread, Signal
    import json
    import urllib.request
    import threading
    
    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Check for Updates")
    dialog.setMinimumSize(500, 300)
    
    layout = QVBoxLayout(dialog)
    
    # Current version info
    current_version = "1.0.0"  # Placeholder - should come from app config
    version_label = QLabel(f"Current Version: {current_version}")
    version_label.setStyleSheet("font-weight: bold;")
    layout.addWidget(version_label)
    
    # Status message
    status_label = QLabel("Checking for updates...")
    layout.addWidget(status_label)
    
    # Progress indicator
    progress = QProgressBar()
    progress.setRange(0, 0)  # Indeterminate progress
    layout.addWidget(progress)
    
    # Details area
    details = QTextBrowser()
    details.setVisible(False)
    layout.addWidget(details)
    
    # Buttons
    btn_layout = QHBoxLayout()
    
    download_btn = QPushButton("Download Update")
    download_btn.setVisible(False)
    btn_layout.addWidget(download_btn)
    
    btn_layout.addStretch()
    
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(close_btn)
    
    layout.addLayout(btn_layout)
    
    # Create a thread for checking updates
    class UpdateChecker(QThread):
        update_available = Signal(dict)
        update_not_available = Signal()
        check_failed = Signal(str)
        
        def run(self):
            try:
                # This is a placeholder URL and should be replaced with your actual update API
                update_url = "https://api.example.com/previewless/updates/check"
                
                # In a real implementation, you would make an API call here
                # For this example, we'll simulate the response
                
                # Simulate network delay
                QThread.sleep(2)
                
                # Simulate an update check response
                mock_response = {
                    "latest_version": "1.1.0",
                    "current_version_supported": True,
                    "update_required": False,
                    "download_url": "https://example.com/previewless/download/v1.1.0",
                    "release_date": "2025-10-15",
                    "release_notes": [
                        "New features:",
                        "- Improved document processing speed",
                        "- Enhanced tag management system",
                        "- Added support for additional file formats",
                        "",
                        "Bug fixes:",
                        "- Fixed memory leak in processing large files",
                        "- Corrected issue with tag search",
                        "- Resolved database connection issues"
                    ]
                }
                
                # Check if update is available
                if mock_response["latest_version"] > current_version:
                    self.update_available.emit(mock_response)
                else:
                    self.update_not_available.emit()
                    
            except Exception as e:
                self.check_failed.emit(str(e))
    
    # Create the thread
    update_thread = UpdateChecker()
    
    # Handle thread signals
    def on_update_available(update_info):
        status_label.setText(f"Update available: version {update_info['latest_version']}")
        status_label.setStyleSheet("color: green; font-weight: bold;")
        progress.setVisible(False)
        
        # Show release notes
        details.setVisible(True)
        
        notes = "\n".join(update_info["release_notes"])
        details.setPlainText(
            f"Version: {update_info['latest_version']}\n"
            f"Release Date: {update_info['release_date']}\n\n"
            f"Release Notes:\n{notes}"
        )
        
        # Show download button
        download_btn.setVisible(True)
        
        # Connect download button
        download_url = update_info["download_url"]
        download_btn.clicked.connect(lambda: self._open_download_page(download_url))
    
    def on_update_not_available():
        status_label.setText("You have the latest version!")
        status_label.setStyleSheet("color: blue; font-weight: bold;")
        progress.setVisible(False)
    
    def on_check_failed(error_msg):
        status_label.setText(f"Update check failed")
        status_label.setStyleSheet("color: red; font-weight: bold;")
        progress.setVisible(False)
        
        details.setVisible(True)
        details.setPlainText(f"Error: {error_msg}\n\nPlease check your internet connection and try again later.")
    
    # Connect signals
    update_thread.update_available.connect(on_update_available)
    update_thread.update_not_available.connect(on_update_not_available)
    update_thread.check_failed.connect(on_check_failed)
    
    # Start the update check
    update_thread.start()
    
    # Show dialog
    dialog.exec()
    
    # Clean up thread if needed
    if update_thread.isRunning():
        update_thread.terminate()
        update_thread.wait()

def _open_download_page(self, url):
    """Open the download page in the default browser."""
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtCore import QUrl
    
    try:
        QDesktopServices.openUrl(QUrl(url))
    except Exception as e:
        logger.error(f"Failed to open download URL: {e}")
        self._show_notification(f"Could not open download page: {str(e)}", "error")
    
def _show_about(self):
    """Show application about dialog."""
    logger.info("Showing about dialog")
    
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
    
    dialog = QDialog(self)
    dialog.setWindowTitle("About Previewless Insight Viewer")
    dialog.setFixedSize(400, 300)
    
    layout = QVBoxLayout(dialog)
    
    # App title
    title = QLabel("Previewless Insight Viewer")
    title.setStyleSheet("font-size: 18px; font-weight: bold;")
    layout.addWidget(title)
    
    # Version info
    version = QLabel("Version 1.0.0")
    layout.addWidget(version)
    
    # Description
    desc = QLabel("Document processing and analysis application")
    layout.addWidget(desc)
    
    layout.addSpacing(20)
    
    # Copyright
    copyright = QLabel("© 2025 Previewless Technologies")
    layout.addWidget(copyright)
    
    # Close button
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(close_btn)
    
    layout.addStretch()
    layout.addLayout(btn_layout)
    
    dialog.exec()