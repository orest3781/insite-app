"""
Review and classification dialog for human verification of processing results.

Allows users to review OCR text, edit tags, and modify descriptions before saving.
"""

import logging
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QGroupBox, QScrollArea, QWidget,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class ReviewDialog(QDialog):
    """
    Dialog for reviewing and editing processing results.
    
    Features:
    - Display OCR extracted text
    - Edit classification tags
    - Edit two-sentence description
    - Show confidence scores
    - Approve or reject results
    """
    
    # Signals
    approved = Signal(dict)  # Emit approved results with edits
    rejected = Signal(str)   # Emit rejection reason
    
    def __init__(self, parent=None):
        """Initialize review dialog."""
        super().__init__(parent)
        
        self.result = None
        self._setup_ui()
        
        logger.info("ReviewDialog initialized")
    
    def _setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("Review Processing Results")
        self.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # File info header
        self.file_label = QLabel()
        self.file_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(self.file_label)
        
        # Confidence indicator
        self.confidence_label = QLabel()
        layout.addWidget(self.confidence_label)
        
        # Splitter for OCR text and classification
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: OCR Text
        ocr_panel = self._create_ocr_panel()
        splitter.addWidget(ocr_panel)
        
        # Right panel: Classification
        classification_panel = self._create_classification_panel()
        splitter.addWidget(classification_panel)
        
        # Set initial sizes (40% OCR, 60% classification)
        splitter.setSizes([360, 540])
        
        layout.addWidget(splitter, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reject_btn = QPushButton("Reject")
        self.reject_btn.clicked.connect(self._on_reject)
        button_layout.addWidget(self.reject_btn)
        
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.skip_btn)
        
        self.approve_btn = QPushButton("Approve && Save")
        self.approve_btn.setDefault(True)
        self.approve_btn.clicked.connect(self._on_approve)
        button_layout.addWidget(self.approve_btn)
        
        layout.addLayout(button_layout)
    
    def _create_ocr_panel(self) -> QWidget:
        """Create OCR text display panel."""
        panel = QGroupBox("Extracted Text (OCR)")
        layout = QVBoxLayout(panel)
        
        # OCR confidence
        self.ocr_confidence_label = QLabel()
        layout.addWidget(self.ocr_confidence_label)
        
        # OCR text display (read-only)
        self.ocr_text_edit = QTextEdit()
        self.ocr_text_edit.setReadOnly(True)
        self.ocr_text_edit.setFont(QFont("Consolas", 9))
        layout.addWidget(self.ocr_text_edit)
        
        # Page navigation (for multi-page PDFs)
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self.prev_page_btn = QPushButton("← Previous Page")
        self.prev_page_btn.clicked.connect(self._previous_page)
        self.prev_page_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_page_btn)
        
        self.page_label = QLabel("Page 1 of 1")
        nav_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton("Next Page →")
        self.next_page_btn.clicked.connect(self._next_page)
        self.next_page_btn.setEnabled(False)
        nav_layout.addWidget(self.next_page_btn)
        
        layout.addLayout(nav_layout)
        
        return panel
    
    def _create_classification_panel(self) -> QWidget:
        """Create classification editing panel."""
        panel = QGroupBox("Classification && Description")
        layout = QVBoxLayout(panel)
        
        # Tags section
        tags_label = QLabel("Tags (6 required):")
        tags_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(tags_label)
        
        # Tags input (one per line)
        self.tags_edit = QTextEdit()
        self.tags_edit.setMaximumHeight(150)
        self.tags_edit.setPlaceholderText(
            "Enter one tag per line:\n"
            "type:invoice\n"
            "domain:finance\n"
            "status:unpaid\n"
            "priority:high\n"
            "currency:usd\n"
            "vendor:acme_corp"
        )
        layout.addWidget(self.tags_edit)
        
        # Tag hints
        hints_label = QLabel(
            "💡 Required: type:*, domain:*, status:*\n"
            "Format: category:value (snake_case, singular)"
        )
        hints_label.setStyleSheet("color: #888; font-size: 8pt;")
        layout.addWidget(hints_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Description section
        desc_label = QLabel("Description (exactly 2 sentences):")
        desc_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(desc_label)
        
        # Description input
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(120)
        self.description_edit.setPlaceholderText(
            "Write exactly two sentences describing the document.\n"
            "Be concise, factual, and avoid speculation."
        )
        self.description_edit.textChanged.connect(self._validate_description)
        layout.addWidget(self.description_edit)
        
        # Description validation
        self.desc_validation_label = QLabel()
        self.desc_validation_label.setStyleSheet("font-size: 8pt;")
        layout.addWidget(self.desc_validation_label)
        
        # LLM info
        self.llm_info_label = QLabel()
        self.llm_info_label.setStyleSheet("color: #888; font-size: 8pt;")
        layout.addWidget(self.llm_info_label)
        
        layout.addStretch()
        
        return panel
    
    def load_result(self, result):
        """
        Load processing result into dialog.
        
        Args:
            result: ProcessingResult object
        """
        self.result = result
        self.current_page = 0
        
        # Update file info
        file_name = Path(result.file_path).name
        self.file_label.setText(f"File: {file_name}")
        
        # Update overall confidence
        if result.ocr_results:
            avg_conf = sum(r.confidence for r in result.ocr_results) / len(result.ocr_results)
            conf_color = self._get_confidence_color(avg_conf)
            self.confidence_label.setText(
                f"Overall Confidence: <span style='color:{conf_color};font-weight:bold;'>"
                f"{avg_conf:.1f}%</span>"
            )
        
        # Load OCR text (first page)
        self._update_ocr_display()
        
        # Load tags
        if result.tags:
            self.tags_edit.setPlainText('\n'.join(result.tags))
        
        # Load description
        if result.description:
            self.description_edit.setPlainText(result.description.response_text)
        
        # Update LLM info
        if result.classification:
            model = result.classification.model_name
            tokens = result.classification.tokens_used
            self.llm_info_label.setText(f"Generated by: {model} ({tokens} tokens)")
        
        # Validate
        self._validate_description()
    
    def _update_ocr_display(self):
        """Update OCR text display for current page."""
        if not self.result or not self.result.ocr_results:
            return
        
        total_pages = len(self.result.ocr_results)
        current_result = self.result.ocr_results[self.current_page]
        
        # Update page label
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        
        # Update navigation buttons
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled(self.current_page < total_pages - 1)
        
        # Update OCR text
        self.ocr_text_edit.setPlainText(current_result.text)
        
        # Update page confidence
        conf_color = self._get_confidence_color(current_result.confidence)
        self.ocr_confidence_label.setText(
            f"Page {self.current_page + 1} Confidence: "
            f"<span style='color:{conf_color};font-weight:bold;'>"
            f"{current_result.confidence:.1f}%</span> | "
            f"Mode: {current_result.mode.value} | "
            f"Language: {current_result.language}"
        )
    
    def _previous_page(self):
        """Navigate to previous OCR page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_ocr_display()
    
    def _next_page(self):
        """Navigate to next OCR page."""
        if self.current_page < len(self.result.ocr_results) - 1:
            self.current_page += 1
            self._update_ocr_display()
    
    def _validate_description(self):
        """Validate description sentence count."""
        text = self.description_edit.toPlainText().strip()
        
        if not text:
            self.desc_validation_label.setText("")
            return
        
        # Count sentences (simple approach: count periods)
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        sentence_count = len(sentences)
        
        if sentence_count == 2:
            self.desc_validation_label.setText(
                "✓ <span style='color:#4CAF50;'>Valid (2 sentences)</span>"
            )
        elif sentence_count < 2:
            self.desc_validation_label.setText(
                f"⚠ <span style='color:#FF9800;'>Need {2 - sentence_count} more sentence(s)</span>"
            )
        else:
            self.desc_validation_label.setText(
                f"⚠ <span style='color:#FF9800;'>Too many sentences ({sentence_count}), need exactly 2</span>"
            )
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence score."""
        if confidence >= 80:
            return "#4CAF50"  # Green
        elif confidence >= 50:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red
    
    def _on_approve(self):
        """Handle approve button click."""
        # Gather edited data
        tags = [tag.strip() for tag in self.tags_edit.toPlainText().split('\n') if tag.strip()]
        description = self.description_edit.toPlainText().strip()
        
        # Validate
        if len(tags) < 6:
            self.desc_validation_label.setText(
                f"⚠ <span style='color:#F44336;'>Need at least 6 tags (have {len(tags)})</span>"
            )
            return
        
        # Count sentences
        sentences = [s.strip() for s in description.split('.') if s.strip()]
        if len(sentences) != 2:
            self.desc_validation_label.setText(
                "⚠ <span style='color:#F44336;'>Description must be exactly 2 sentences</span>"
            )
            return
        
        # Emit approved data
        approved_data = {
            'file_path': self.result.file_path,
            'file_hash': self.result.file_hash,
            'tags': tags,
            'description': description,
            'ocr_results': self.result.ocr_results
        }
        
        logger.info(f"Results approved for: {self.result.file_path}")
        self.approved.emit(approved_data)
        self.accept()
    
    def _on_reject(self):
        """Handle reject button click."""
        logger.info(f"Results rejected for: {self.result.file_path}")
        self.rejected.emit(self.result.file_path)
        self.reject()
