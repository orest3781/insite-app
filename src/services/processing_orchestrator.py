"""
Processing orchestrator for coordinating the full processing pipeline.

Manages the workflow: Queue → OCR → LLM → Review → Database
"""

import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, Signal, QThread, Slot

from src.services.queue_manager import QueueManager, QueueItem, QueueItemStatus
from src.services.ocr_adapter import OCRAdapter, OCRMode, OCRResult
from src.services.llm_adapter import OllamaAdapter, LLMResult, PromptType

logger = logging.getLogger(__name__)


class ProcessingState(Enum):
    """Overall processing state."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSING = "pausing"  # Added transition state
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"


class ProcessingError(Exception):
    """Exception raised during processing operations."""
    
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"{error_code}: {message}")


@dataclass
class ProcessingResult:
    """Result from processing a single file."""
    file_path: str
    file_hash: str
    file_type: str
    page_count: int
    file_size: int
    created_at: str
    modified_at: str
    ocr_results: list  # List of OCRResult objects
    classification: Optional[LLMResult] = None
    description: Optional[LLMResult] = None
    tags: list = field(default_factory=list)
    status: str = "pending"
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    needs_review: bool = True


class ProcessingOrchestrator(QObject):
    """
    Orchestrates the full processing pipeline.
    
    Workflow:
    1. Get next item from queue
    2. Calculate file hash (deduplication check)
    3. Run OCR (fast or high-accuracy mode)
    4. Generate classification tags (LLM)
    5. Generate description (LLM)
    6. Emit for human review
    7. Store results in database (after review approval)
    
    Features:
    - Pause/resume support
    - Retry logic for failed items
    - Progress tracking
    - Error recovery
    """
    
    # Signals
    processing_started = Signal()
    processing_paused = Signal()
    processing_stopped = Signal()
    processing_completed = Signal()
    
    item_processing_started = Signal(str)  # file_path
    item_processing_completed = Signal(ProcessingResult)
    item_processing_failed = Signal(str, str, str)  # file_path, error_code, message
    item_progress_updated = Signal(str, int, str)  # file_path, percentage, stage_description
    
    review_required = Signal(ProcessingResult)  # Emit when human review needed
    
    progress_updated = Signal(int, int, str)  # current, total, current_file
    state_changed = Signal(ProcessingState)
    
    def __init__(self, config_manager, database, queue_manager: QueueManager,
                 ocr_adapter: OCRAdapter, llm_adapter: OllamaAdapter):
        """
        Initialize processing orchestrator.
        
        Args:
            config_manager: ConfigManager instance
            database: Database instance
            queue_manager: QueueManager instance
            ocr_adapter: OCRAdapter instance
            llm_adapter: OllamaAdapter instance
        """
        super().__init__()
        
        self.config = config_manager
        self.db = database
        self.queue = queue_manager
        self.ocr = ocr_adapter
        self.llm = llm_adapter
        
        # Processing state
        self.state = ProcessingState.IDLE
        self.current_item: Optional[QueueItem] = None
        self.should_stop = False
        self.should_pause = False
        
        # Statistics
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        logger.info("ProcessingOrchestrator initialized")
    
    @Slot()
    def start_processing(self):
        """Start processing the queue."""
        logger.info(f"start_processing called, current state: {self.state}")
        
        if self.state == ProcessingState.RUNNING:
            logger.warning("Processing already running")
            return
        
        self.state = ProcessingState.RUNNING
        self.should_stop = False
        self.should_pause = False
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        logger.info("Processing started, emitting signals...")
        self.processing_started.emit()
        self.state_changed.emit(self.state)
        
        # Emit initial progress (0/total) so UI can initialize
        stats = self.queue.get_statistics()
        logger.debug(f"Emitting initial progress: 0/{stats['total']}")
        self.progress_updated.emit(0, stats['total'], "")
        
        logger.info("Starting processing loop...")
        # Start processing loop
        self._process_next_item()
    
    @Slot()
    def pause_processing(self):
        """Immediately pause processing and reset current item to pending for later resume."""
        logger.info(f"pause_processing called, current state: {self.state}, should_pause: {self.should_pause}")

        if self.state != ProcessingState.RUNNING:
            logger.warning(f"Processing not running (state={self.state}), cannot pause")
            return

        # Immediately pause and reset current item to pending
        self.should_pause = True
        self.state = ProcessingState.PAUSED

        # If there's a current item being processed, reset it to pending so it can be restarted
        if self.current_item:
            logger.info(f"Resetting current item {self.current_item.file_path} to pending for later resume")
            self.queue.update_item_status(self.current_item.file_path, QueueItemStatus.PENDING)
            self.current_item = None

        logger.info("Processing immediately paused, current item reset to pending")
        self.processing_paused.emit()
        self.state_changed.emit(self.state)
    
    @Slot()
    def resume_processing(self):
        """Resume processing from paused state, restarting from the beginning of the queue."""
        if self.state != ProcessingState.PAUSED:
            logger.warning("Processing not paused, cannot resume")
            return

        self.state = ProcessingState.RUNNING
        self.should_pause = False

        logger.info("Processing resumed from paused state")
        self.state_changed.emit(self.state)

        # Start processing from the beginning of the queue (including any previously paused items)
        self._process_next_item()
    
    @Slot()
    def stop_processing(self):
        """Stop processing immediately."""
        if self.state == ProcessingState.IDLE:
            logger.warning("Processing not running, cannot stop")
            return
        
        self.should_stop = True
        self.state = ProcessingState.STOPPING
        
        logger.info("Processing stop requested")
        self.state_changed.emit(self.state)
    
    def _handle_stop(self):
        """Handle the stop operation - reset to IDLE state."""
        logger.info("Handling stop - resetting to IDLE state")
        
        # Reset state to STOPPED first, then to IDLE
        self.state = ProcessingState.STOPPED
        self.state_changed.emit(self.state)
        
        # Reset all counters
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        # Clear current item
        self.current_item = None
        
        # Reset flags
        self.should_stop = False
        self.should_pause = False
        
        # Emit stopped signal
        self.processing_stopped.emit()
        
        # Finally set to IDLE state
        self.state = ProcessingState.IDLE
        self.state_changed.emit(self.state)
        
        logger.info("Stop handling complete - back to IDLE state")
    
    def _handle_pause(self):
        """Handle the pause operation."""
        logger.info("Handling pause - setting state to PAUSED")
        
        self.state = ProcessingState.PAUSED
        self.state_changed.emit(self.state)
        
        logger.info("Pause handling complete")
    
    def _handle_completion(self):
        """Handle completion of all items in the queue."""
        logger.info("Handling completion - all items processed")
        
        # Reset counters but keep the processed/failed counts for display
        self.current_item = None
        
        # Reset flags
        self.should_stop = False
        self.should_pause = False
        
        # Set state to IDLE
        self.state = ProcessingState.IDLE
        self.state_changed.emit(self.state)
        
        logger.info("Completion handling complete - back to IDLE state")
    
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file content for deduplication."""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            # Return a hash based on file path and size as fallback
            file_size = Path(file_path).stat().st_size
            fallback_hash = hashlib.sha256()
            fallback_hash.update(str(file_path).encode())
            fallback_hash.update(str(file_size).encode())
            return fallback_hash.hexdigest()
    
    def _is_already_processed(self, file_hash: str) -> bool:
        """Check if a file with the given hash has already been processed."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 1 FROM files f
                    WHERE f.file_hash = ?
                    AND (
                        EXISTS (SELECT 1 FROM descriptions d WHERE d.file_id = f.file_id)
                        OR EXISTS (SELECT 1 FROM classifications c WHERE c.file_id = f.file_id)
                    )
                    LIMIT 1
                """, (file_hash,))
                
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking if file is already processed: {e}")
            return False
    
    def _save_results(self, result: ProcessingResult):
        """
        Save processing results to database.
        
        Args:
            result: ProcessingResult object containing all analysis data
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert file record
                cursor.execute("""
                    INSERT INTO files (
                        file_path, file_hash, file_type, page_count,
                        file_size, created_at, modified_at, analyzed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    result.file_path,
                    result.file_hash,
                    result.file_type,
                    result.page_count,
                    result.file_size,
                    result.created_at,
                    result.modified_at
                ))
                
                file_id = cursor.lastrowid
                logger.info(f"Inserted file record with file_id={file_id}")
                
                # **CRITICAL FIX**: Delete any existing results for this file
                # This prevents tag accumulation from retries/multiple attempts
                cursor.execute("DELETE FROM classifications WHERE file_id = ?", (file_id,))
                deleted_tags = cursor.rowcount
                if deleted_tags > 0:
                    logger.warning(f"Deleted {deleted_tags} existing tags for file_id={file_id} (retry/reprocess)")
                
                cursor.execute("DELETE FROM descriptions WHERE file_id = ?", (file_id,))
                deleted_descs = cursor.rowcount
                if deleted_descs > 0:
                    logger.warning(f"Deleted {deleted_descs} existing descriptions for file_id={file_id} (retry/reprocess)")
                
                cursor.execute("DELETE FROM pages WHERE file_id = ?", (file_id,))
                deleted_pages = cursor.rowcount
                if deleted_pages > 0:
                    logger.warning(f"Deleted {deleted_pages} existing pages for file_id={file_id} (retry/reprocess)")
                
                # Insert OCR results (pages)
                if result.ocr_results:
                    for ocr_result in result.ocr_results:
                        cursor.execute("""
                            INSERT INTO pages (
                                file_id, page_number, ocr_text,
                                ocr_confidence, ocr_engine, ocr_language
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            file_id,
                            ocr_result.page_number,
                            ocr_result.text or '',
                            ocr_result.confidence,
                            'tesseract',
                            ocr_result.language or 'eng'
                        ))
                
                # Insert classification tags
                if result.tags:
                    # Deduplicate tags before saving to database
                    seen_tags = set()
                    unique_tag_objects = []
                    
                    for tag in result.tags:
                        tag_text = tag if isinstance(tag, str) else tag.response_text
                        tag_lower = tag_text.lower()
                        
                        if tag_lower not in seen_tags:
                            unique_tag_objects.append((tag_text, tag))
                            seen_tags.add(tag_lower)
                        else:
                            logger.debug(f"Skipping duplicate tag at save: {tag_text}")
                    
                    logger.info(f"Saving {len(unique_tag_objects)} unique tags (removed {len(result.tags) - len(unique_tag_objects)} duplicates)")
                    
                    # Save unique tags
                    for idx, (tag_text, tag) in enumerate(unique_tag_objects):
                        cursor.execute("""
                            INSERT INTO classifications (
                                file_id, tag_number, tag_text,
                                confidence, model_used
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            file_id,
                            idx + 1,  # tag_number starts at 1
                            tag_text,
                            tag.confidence if hasattr(tag, 'confidence') else 0.0,
                            result.classification.model_name if result.classification else 'unknown'
                        ))
                    
                    # Verify what was saved
                    cursor.execute("SELECT COUNT(*) FROM classifications WHERE file_id = ?", (file_id,))
                    saved_count = cursor.fetchone()[0]
                    logger.info(f"Verified: {saved_count} tags saved to database for file_id={file_id}")
                
                # Insert description
                if result.description:
                    cursor.execute("""
                        INSERT INTO descriptions (
                            file_id, description_text,
                            confidence, model_used
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        file_id,
                        result.description.response_text,
                        result.description.confidence if hasattr(result.description, 'confidence') else 0.0,
                        result.description.model_name
                    ))
                
                logger.info(f"Saved results for: {result.file_path} (file_id={file_id})")
                
        except Exception as e:
            logger.exception(f"Error saving results to database: {e}")
            raise ProcessingError("DATABASE_ERROR", f"Failed to save results: {str(e)}")
    
    def _parse_tags(self, classification_text: str) -> list:
        """
        Parse classification tags from LLM response.
        
        Args:
            classification_text: Raw text response from LLM (comma-separated tags)
            
        Returns:
            List of tag strings
        """
        if not classification_text:
            return []
        
        # Split by comma and clean up whitespace
        tags = [tag.strip() for tag in classification_text.split(',')]
        
        # Remove empty tags and duplicates while preserving order
        seen = set()
        clean_tags = []
        for tag in tags:
            if tag and tag.lower() not in seen:
                clean_tags.append(tag)
                seen.add(tag.lower())
        
        logger.debug(f"Parsed {len(clean_tags)} tags from classification")
        return clean_tags
    
    def _should_require_review(self, ocr_results: list, classification_result) -> bool:
        """
        Determine if processing result should require human review.
        
        Args:
            ocr_results: List of OCR results
            classification_result: LLM classification result
            
        Returns:
            True if review is needed, False otherwise
        """
        # Require review if OCR confidence is low
        if ocr_results:
            avg_confidence = sum(r.confidence for r in ocr_results) / len(ocr_results)
            if avg_confidence < 0.7:
                logger.debug(f"Review required: Low OCR confidence ({avg_confidence:.2f})")
                return True
        
        # Require review if LLM confidence is low
        if classification_result and hasattr(classification_result, 'confidence'):
            if classification_result.confidence < 0.7:
                logger.debug(f"Review required: Low classification confidence ({classification_result.confidence:.2f})")
                return True
        
        # Require review if no meaningful text was extracted
        if ocr_results:
            total_text = ' '.join(r.text for r in ocr_results if r.text)
            if len(total_text.strip()) < 10:
                logger.debug("Review required: Minimal text extracted")
                return True
        
        # Auto-approve if all confidence checks pass
        logger.debug("No review required: All confidence checks passed")
        return False
    
    @Slot()
    def retry_failed_items(self):
        """Retry all failed items in the queue and start processing if idle."""
        failed_items = self.queue.get_queue_items(QueueItemStatus.FAILED)

        for item in failed_items:
            self.queue.update_item_status(item.file_path, QueueItemStatus.PENDING)

        logger.info(f"Reset {len(failed_items)} failed items to pending")

        # If we're idle, automatically start processing the retried items
        if self.state == ProcessingState.IDLE and failed_items:
            logger.info("Automatically starting processing of retried items")
            self.start_processing()
    
    def _process_next_item(self):
        """Process the next item in the queue."""
        logger.info("_process_next_item called")
        
        # Check for stop/pause requests
        if self.should_stop:
            logger.info("Stop requested, handling stop...")
            self._handle_stop()
            return
        
        if self.should_pause:
            logger.info("Pause requested, handling pause...")
            self._handle_pause()
            return
        
        # Get next item
        logger.info("Getting next item from queue...")
        next_item = self.queue.get_next_item()
        
        if next_item is None:
            # No more items to process
            logger.info("No more items to process, completing...")
            self._handle_completion()
            return
        
        logger.info(f"Got item: {next_item.file_path}")
        # Process the item
        self.current_item = next_item
        self._process_item(next_item)
    
    def _run_ocr(self, file_path: str, mode: OCRMode) -> list:
        """
        Run OCR on a document file (PDF or text file).
        
        Args:
            file_path: Path to the document file
            mode: OCRMode (FAST or ACCURATE)
            
        Returns:
            List of OCRResult objects
            
        Raises:
            ProcessingError: If OCR processing fails
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # Handle PDF files
            if file_ext == '.pdf':
                logger.info(f"Running OCR on PDF: {file_path} (mode={mode.value})")
                ocr_results = self.ocr.process_pdf(file_path, mode=mode)
                
                if not ocr_results:
                    raise ProcessingError("OCR_EMPTY_RESULT", "No OCR results returned from PDF")
                
                logger.info(f"OCR completed: {len(ocr_results)} pages processed")
                return ocr_results
            
            # Handle text files (.txt, .md, .rst, etc)
            elif file_ext in {'.txt', '.md', '.rst', '.log', '.csv', '.json'}:
                logger.info(f"Processing text file: {file_path}")
                
                # Read text file directly
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read()
                    
                    # Create a single OCRResult for the text file
                    ocr_result = OCRResult(
                        text=text_content,
                        confidence=1.0,
                        page_number=0,
                        error_code=None,
                        error_message=None
                    )
                    logger.info(f"Text file read successfully: {len(text_content)} characters")
                    return [ocr_result]
                
                except Exception as e:
                    raise ProcessingError(
                        "TEXT_READ_ERROR",
                        f"Failed to read text file: {str(e)}"
                    )
            
            else:
                # Unsupported file type for document processing
                raise ProcessingError(
                    "UNSUPPORTED_DOCUMENT_TYPE",
                    f"Unsupported document type: {file_ext}"
                )
        
        except ProcessingError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during OCR: {e}")
            raise ProcessingError(
                "OCR_PROCESSING_ERROR",
                f"Unexpected error during OCR: {str(e)}"
            )
    
    def _process_item(self, item: QueueItem):
        """
        Process a single queue item through the full pipeline.
        
        Args:
            item: QueueItem to process
        """
        file_path = item.file_path
        file_path_obj = Path(file_path)  # Convert to Path for .name attribute
        start_time = datetime.now()
        
        logger.info(f"Processing: {file_path}")
        self.item_processing_started.emit(file_path)
        
        # Update queue status
        self.queue.update_item_status(file_path, QueueItemStatus.PROCESSING)
        
        try:
            # Step 1: Calculate file hash
            file_hash = self._calculate_hash(file_path)
            
            # Step 2: Check if already processed (deduplication)
            if self._is_already_processed(file_hash):
                logger.info(f"File already processed (hash={file_hash[:8]}...), skipping")
                self.queue.update_item_status(file_path, QueueItemStatus.SKIPPED)
                self.skipped_count += 1
                
                # Update progress for skipped item
                stats = self.queue.get_statistics()
                self.progress_updated.emit(
                    self.processed_count + self.failed_count + self.skipped_count,
                    stats['total'],
                    file_path
                )
                
                # Continue to next item
                self._process_next_item()
                return
            
            # Get file metadata for database
            file_stats = file_path_obj.stat()
            file_type = file_path_obj.suffix.lower()
            file_size = file_stats.st_size
            created_at = datetime.fromtimestamp(file_stats.st_ctime).isoformat()
            modified_at = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            
            # Step 3: Determine if this is an image file (should use vision) or document (should use OCR)
            file_ext = file_path_obj.suffix.lower()
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
            is_image_file = file_ext in image_extensions
            
            # For image files: Skip OCR, use vision directly
            if is_image_file:
                logger.info(f"Image file detected: {file_path_obj.name}, using vision analysis")
                
                # Emit progress: Starting vision analysis
                self.item_progress_updated.emit(file_path, 20, "Starting vision analysis...")
                
                # Check for pause/stop BEFORE starting vision processing
                if self.should_stop:
                    logger.info("Stop requested before vision processing, handling stop...")
                    self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                    self._handle_stop()
                    return
                
                if self.should_pause:
                    logger.info("Pause requested before vision processing, handling pause...")
                    self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                    self._handle_pause()
                    return
                
                logger.info(f"Starting vision analysis, should_pause={self.should_pause}, should_stop={self.should_stop}")
                
                # Create empty OCR results (vision will analyze the image directly)
                ocr_results = []
                combined_text = ""
                
                # Use vision to analyze the image file directly
                try:
                    vision_results = self.llm.analyze_image_vision(file_path)
                    
                    # Emit progress: Vision analysis complete
                    self.item_progress_updated.emit(file_path, 75, "Processing results...")
                    
                    logger.info(f"Vision complete, checking flags: should_pause={self.should_pause}, should_stop={self.should_stop}")
                    
                    # Check for pause/stop AFTER vision completes (can take 1-3 minutes)
                    if self.should_stop:
                        logger.info("Stop requested during vision processing, handling stop...")
                        self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                        self._handle_stop()
                        return
                    
                    if self.should_pause:
                        logger.info("Pause requested during vision processing, handling pause...")
                        self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                        self._handle_pause()
                        return
                    
                    # Extract tags from vision analysis
                    tags_response = vision_results['tags'].response_text
                    tag_list = [tag.strip() for tag in tags_response.split(',') if tag.strip()]
                    
                    # Log raw vision response for debugging
                    logger.info(f"Raw vision tags response: {tags_response}")
                    logger.info(f"Parsed {len(tag_list)} tags from vision model")
                    
                    # ENFORCE 6-TAG LIMIT - Take only first 6 tags
                    tag_list = tag_list[:6]
                    logger.info(f"Enforcing 6-tag limit, keeping: {tag_list}")
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_tags = []
                    for tag in tag_list:
                        tag_lower = tag.lower()
                        if tag_lower not in seen:
                            unique_tags.append(tag)
                            seen.add(tag_lower)
                        else:
                            logger.debug(f"Removing duplicate tag: {tag}")
                    
                    logger.info(f"After deduplication: {len(unique_tags)} unique tags: {unique_tags}")
                    
                    # Create LLMResult objects for each unique tag
                    tags = [
                        LLMResult(
                            response_text=tag,
                            model_name=vision_results['tags'].model_name,
                            prompt_type="classification",
                            tokens_used=0,
                            confidence=vision_results['tags'].confidence
                        )
                        for tag in unique_tags
                    ]
                    
                    # Get description from vision analysis
                    description_result = vision_results['description']
                    logger.info(f"Description preview: {description_result.response_text[:100]}...")
                    
                    # Create classification result with deduplicated tags
                    deduplicated_tags_str = ', '.join(unique_tags)
                    classification_result = LLMResult(
                        response_text=deduplicated_tags_str,
                        model_name=vision_results['tags'].model_name,
                        prompt_type="classification",
                        tokens_used=vision_results['tags'].tokens_used,
                        confidence=vision_results['tags'].confidence
                    )
                    
                    logger.info(f"Vision analysis complete: {len(tags)} unique tags (from {len(tag_list)} total), {vision_results['description'].tokens_used} tokens")
                    
                except Exception as e:
                    logger.error(f"Vision analysis failed: {e}, using fallback")
                    
                    # Fallback to basic classification
                    classification_result = LLMResult(
                        response_text="visual-content, image-file, unclassified",
                        model_name=self.llm.model_name,
                        prompt_type="classification",
                        tokens_used=0,
                        confidence=0.1
                    )
                    
                    tags = [
                        LLMResult(
                            response_text=tag,
                            model_name=self.llm.model_name,
                            prompt_type="classification",
                            tokens_used=0,
                            confidence=0.1
                        )
                        for tag in ["visual-content", "image-file", "unclassified"]
                    ]
                    
                    description_result = LLMResult(
                        response_text=f"Image file: {file_path_obj.name}. Vision analysis failed: {str(e)}",
                        model_name=self.llm.model_name,
                        prompt_type="description",
                        tokens_used=0,
                        confidence=0.1
                    )
                
                # Step 6: Create processing result for vision-analyzed image
                self.item_progress_updated.emit(file_path, 90, "Saving results...")
                
                result = ProcessingResult(
                    file_path=file_path,
                    file_hash=file_hash,
                    file_type=file_type,
                    page_count=1,  # Images are single-page
                    file_size=file_size,
                    created_at=created_at,
                    modified_at=modified_at,
                    ocr_results=ocr_results,
                    classification=classification_result,
                    description=description_result,
                    tags=tags,
                    status="completed",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    needs_review=False
                )
                
                # Save to database
                self._save_results(result)
                
                # Update queue status
                self.queue.update_item_status(file_path, QueueItemStatus.COMPLETED)
                self.processed_count += 1
                
                # Emit completion
                self.item_processing_completed.emit(result)
                
                # Check for pause/stop BEFORE continuing to next item (after vision processing)
                # Note: Item is already COMPLETED and saved, so we don't reset it to PENDING
                if self.should_stop:
                    logger.info("Stop requested after completing vision item, handling stop...")
                    self._handle_stop()
                    return
                
                if self.should_pause:
                    logger.info("Pause requested after completing vision item, handling pause...")
                    self._handle_pause()
                    return
                
                # Don't call _process_next_item() here - let finally block handle it
                return
            
            # Step 4: For documents (PDFs, text files): Run OCR
            logger.info(f"Document file detected: {file_path_obj.name}, using OCR")
            
            # Emit progress: Starting OCR
            self.item_progress_updated.emit(file_path, 20, "Running OCR...")
            
            ocr_mode = OCRMode(self.config.get('ocr_default_mode', 'fast'))
            ocr_results = self._run_ocr(file_path, ocr_mode)
            
            # Emit progress: OCR complete
            self.item_progress_updated.emit(file_path, 40, "OCR complete, analyzing...")
            
            # Check for pause/stop AFTER OCR completes
            if self.should_stop:
                logger.info("Stop requested after OCR, handling stop...")
                self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                self._handle_stop()
                return
            
            if self.should_pause:
                logger.info("Pause requested after OCR, handling pause...")
                self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                self._handle_pause()
                return
            
            # Check for OCR errors
            if all(r.error_code for r in ocr_results):
                error_code = ocr_results[0].error_code
                error_message = ocr_results[0].error_message
                raise ProcessingError(error_code, error_message)
            
            # Combine OCR text from all pages
            combined_text = "\n\n".join(r.text for r in ocr_results if r.text)
            
            # For documents with no text, handle gracefully
            if not combined_text.strip():
                logger.info(f"No text found in {file_path_obj.name}, treating as empty document")
                
                # Use minimal classification for images
                tags = ["image", "no-text", "visual-content"]
                
                # Create simple description
                description_text = f"Image file: {file_path_obj.name}\nNo text content detected. This appears to be a purely visual image (e.g., photograph, artwork, wallpaper)."
                
                # Step 6: Create processing result for image without text
                result = ProcessingResult(
                    file_path=file_path,
                    file_hash=file_hash,
                    ocr_results=ocr_results,
                    classification=LLMResult(
                        response_text="image, no-text, visual-content",
                        model_name=self.llm.model_name,
                        prompt_type="classification",
                        tokens_used=0
                    ),
                    description=LLMResult(
                        response_text=description_text,
                        model_name=self.llm.model_name,
                        prompt_type="description",
                        tokens_used=0
                    ),
                    tags=tags,
                    status="completed",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    needs_review=False  # Visual-only images don't need review
                )
                
                # Save to database
                self._save_results(result)
                
                # Update queue status
                self.queue.update_item_status(file_path, QueueItemStatus.COMPLETED)
                self.processed_count += 1
                
                # Emit completion
                self.item_processing_completed.emit(result)
                
                # Check for pause/stop BEFORE continuing to next item (image without text)
                if self.should_stop:
                    logger.info("Stop requested after completing empty image item, handling stop...")
                    self._handle_stop()
                    return
                
                if self.should_pause:
                    logger.info("Pause requested after completing empty image item, handling pause...")
                    self._handle_pause()
                    return
                
                # Don't call _process_next_item() here - let finally block handle it
                return
            
            # For documents with no text, handle gracefully
            if not combined_text.strip():
                logger.info(f"No text found in {file_path_obj.name}, treating as empty document")
                
                # Use minimal classification for empty documents
                tags = ["document", "no-text", "empty"]
                
                # Create simple description
                description_text = f"Document file: {file_path_obj.name}\nNo text content detected. This document appears to be empty."
                
                # Create processing result for empty document
                result = ProcessingResult(
                    file_path=file_path,
                    file_hash=file_hash,
                    file_type=file_type,
                    page_count=len(ocr_results) if ocr_results else 1,
                    file_size=file_size,
                    created_at=created_at,
                    modified_at=modified_at,
                    ocr_results=ocr_results,
                    classification=LLMResult(
                        response_text="document, no-text, empty",
                        model_name=self.llm.model_name,
                        prompt_type="classification",
                        tokens_used=0
                    ),
                    description=LLMResult(
                        response_text=description_text,
                        model_name=self.llm.model_name,
                        prompt_type="description",
                        tokens_used=0
                    ),
                    tags=tags,
                    status="completed",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    needs_review=False
                )
                
                # Save to database
                self._save_results(result)
                
                # Update queue status
                self.queue.update_item_status(file_path, QueueItemStatus.COMPLETED)
                self.processed_count += 1
                
                # Emit completion
                self.item_processing_completed.emit(result)
                
                # Check for pause/stop BEFORE continuing to next item (empty document)
                if self.should_stop:
                    logger.info("Stop requested after completing empty document item, handling stop...")
                    self._handle_stop()
                    return
                
                if self.should_pause:
                    logger.info("Pause requested after completing empty document item, handling pause...")
                    self._handle_pause()
                    return
                
                # Don't call _process_next_item() here - let finally block handle it
                return
            
            # Check for pause/stop BEFORE LLM analysis
            if self.should_stop:
                logger.info("Stop requested before LLM analysis, handling stop...")
                self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                self._handle_stop()
                return
            
            if self.should_pause:
                logger.info("Pause requested before LLM analysis, handling pause...")
                self.queue.update_item_status(file_path, QueueItemStatus.PENDING)
                self._handle_pause()
                return
            
            # Step 5: Generate classification tags (for documents with text)
            self.item_progress_updated.emit(file_path, 50, "Generating tags...")
            classification_result = self.llm.generate_classification(combined_text)
            
            if classification_result.error_code:
                raise ProcessingError(
                    classification_result.error_code,
                    classification_result.error_message
                )
            
            # Parse tags from LLM response (as strings for description generation)
            tags_str = self._parse_tags(classification_result.response_text)
            
            # Step 5: Generate description
            self.item_progress_updated.emit(file_path, 70, "Generating description...")
            description_result = self.llm.generate_description(combined_text, tags_str)
            
            if description_result.error_code:
                raise ProcessingError(
                    description_result.error_code,
                    description_result.error_message
                )
            
            # Emit progress: Analysis complete, saving
            self.item_progress_updated.emit(file_path, 90, "Saving results...")
            
            # Convert string tags to LLMResult objects for database storage
            tags = [
                LLMResult(
                    response_text=tag,
                    model_name=classification_result.model_name,
                    prompt_type="classification",
                    confidence=classification_result.confidence,
                    tokens_used=0
                )
                for tag in tags_str
            ]
            
            # Step 6: Create processing result
            result = ProcessingResult(
                file_path=file_path,
                file_hash=file_hash,
                file_type=file_type,
                page_count=len(ocr_results) if ocr_results else 1,
                file_size=file_size,
                created_at=created_at,
                modified_at=modified_at,
                ocr_results=ocr_results,
                classification=classification_result,
                description=description_result,
                tags=tags,
                status="completed",
                processing_time=(datetime.now() - start_time).total_seconds(),
                needs_review=self._should_require_review(ocr_results, classification_result)
            )
            
            # Step 7: Emit for review (if needed) or auto-save
            if result.needs_review:
                logger.info(f"Review required for: {file_path}")
                self.review_required.emit(result)
            else:
                logger.info(f"Auto-saving results for: {file_path}")
                self._save_results(result)
            
            # Update queue status
            self.queue.update_item_status(file_path, QueueItemStatus.COMPLETED)
            self.processed_count += 1
            
            # Emit completion
            self.item_processing_completed.emit(result)
            
            # Update progress
            stats = self.queue.get_statistics()
            current_progress = self.processed_count + self.failed_count + self.skipped_count
            logger.debug(f"Emitting progress: {current_progress}/{stats['total']} (processed={self.processed_count}, failed={self.failed_count}, skipped={self.skipped_count})")
            self.progress_updated.emit(
                current_progress,
                stats['total'],
                file_path
            )
        
        except ProcessingError as e:
            logger.error(f"Processing failed for {file_path}: {e.error_code} - {e.message}")
            
            # Update queue status with error
            self.queue.update_item_status(
                file_path,
                QueueItemStatus.FAILED,
                error_code=e.error_code,
                error_message=e.message
            )
            
            self.failed_count += 1
            self.item_processing_failed.emit(file_path, e.error_code, e.message)
            
            # Update progress even on failure
            stats = self.queue.get_statistics()
            self.progress_updated.emit(
                self.processed_count + self.failed_count + self.skipped_count,
                stats['total'],
                file_path
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error processing {file_path}: {e}")
            
            # Update queue status with error
            self.queue.update_item_status(
                file_path,
                QueueItemStatus.FAILED,
                error_code="PROCESSING_ERROR",
                error_message=str(e)
            )
            
            self.failed_count += 1
            self.item_processing_failed.emit(file_path, "PROCESSING_ERROR", str(e))
            
            # Update progress even on exception
            stats = self.queue.get_statistics()
            self.progress_updated.emit(
                self.processed_count + self.failed_count + self.skipped_count,
                stats['total'],
                file_path
            )
        
        finally:
            # Always process the next item unless stopped
            if not self.should_stop:
                logger.info("Processing next item")
                self._process_next_item()
            else:
                logger.info("Processing stopped, not processing next item")
