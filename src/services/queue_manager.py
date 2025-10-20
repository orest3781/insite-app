"""
Queue management service for processing files.

Manages the queue of files to be processed, supports reordering, and tracks queue state.
"""

import logging
import hashlib
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class QueueItemStatus(Enum):
    """Status of items in the queue."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class QueueItem:
    """Item in the processing queue."""
    file_path: str
    file_hash: Optional[str] = None
    file_type: Optional[str] = None
    status: QueueItemStatus = QueueItemStatus.PENDING
    priority: int = 0
    added_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    def __hash__(self):
        """Make QueueItem hashable based on file_path."""
        return hash(self.file_path)
    
    def __eq__(self, other):
        """Compare QueueItems by file_path."""
        if isinstance(other, QueueItem):
            return self.file_path == other.file_path
        return False


class QueueManager(QObject):
    """
    Service for managing the processing queue.
    
    Features:
    - Add/remove items from queue
    - Reorder queue items (drag-drop support)
    - Track queue status and progress
    - Batch operations
    """
    
    # Signals
    item_added = Signal(QueueItem)
    item_removed = Signal(str)  # file_path
    item_updated = Signal(QueueItem)
    queue_reordered = Signal(list)  # List of file_paths in new order
    queue_cleared = Signal()
    progress_changed = Signal(int, int)  # completed, total
    
    def __init__(self, database):
        """
        Initialize queue manager.
        
        Args:
            database: Database instance for persisting queue state
        """
        super().__init__()
        self.db = database
        
        # Queue storage (ordered list)
        self.queue: List[QueueItem] = []
        self._queue_map: Dict[str, QueueItem] = {}  # Fast lookup by path
        
        logger.info("QueueManager initialized")
    
    def add_item(self, file_path: str, priority: int = 0) -> bool:
        """
        Add a file to the queue.
        
        Args:
            file_path: Path to the file
            priority: Priority level (higher = processed first)
        
        Returns:
            True if added successfully, False if already in queue or unsupported file type
        """
        abs_path = str(Path(file_path).resolve())
        
        if abs_path in self._queue_map:
            logger.debug(f"File already in queue: {abs_path}")
            return False
            
        # Check if file type is supported
        if not self.is_supported_file(abs_path):
            logger.warning(f"Unsupported file type: {abs_path}")
            return False
            
        # Get file type
        file_type = self._detect_file_type(abs_path)
        if not file_type:
            logger.warning(f"Could not determine file type: {abs_path}")
            return False
        
        # Create queue item
        item = QueueItem(
            file_path=abs_path,
            priority=priority,
            file_type=file_type
        )
        
        # Insert based on priority
        insert_pos = len(self.queue)
        for i, existing_item in enumerate(self.queue):
            if existing_item.priority < priority:
                insert_pos = i
                break
        
        self.queue.insert(insert_pos, item)
        self._queue_map[abs_path] = item
        
        logger.info(f"Added to queue (pos {insert_pos}): {abs_path}")
        self.item_added.emit(item)
        self._update_progress()
        
        return True
    
    def add_batch(self, file_paths: List[str], priority: int = 0) -> int:
        """
        Add multiple files to the queue.
        
        Args:
            file_paths: List of file paths
            priority: Priority level for all items
        
        Returns:
            Number of items successfully added
        """
        added_count = 0
        for file_path in file_paths:
            if self.add_item(file_path, priority):
                added_count += 1
        
        logger.info(f"Batch add: {added_count}/{len(file_paths)} items added")
        return added_count
    
    def remove_item(self, file_path: str) -> bool:
        """
        Remove a file from the queue.
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if removed successfully, False if not in queue
        """
        abs_path = str(Path(file_path).resolve())
        
        if abs_path not in self._queue_map:
            logger.debug(f"File not in queue: {abs_path}")
            return False
        
        item = self._queue_map[abs_path]
        self.queue.remove(item)
        del self._queue_map[abs_path]
        
        logger.info(f"Removed from queue: {abs_path}")
        self.item_removed.emit(abs_path)
        self._update_progress()
        
        return True
    
    def remove_batch(self, file_paths: List[str]) -> int:
        """
        Remove multiple files from the queue.
        
        Args:
            file_paths: List of file paths
        
        Returns:
            Number of items successfully removed
        """
        removed_count = 0
        for file_path in file_paths:
            if self.remove_item(file_path):
                removed_count += 1
        
        logger.info(f"Batch remove: {removed_count}/{len(file_paths)} items removed")
        return removed_count
    
    def clear_queue(self, status_filter: Optional[QueueItemStatus] = None):
        """
        Clear the queue.
        
        Args:
            status_filter: If provided, only clear items with this status
        """
        if status_filter is None:
            self.queue.clear()
            self._queue_map.clear()
            logger.info("Queue cleared")
        else:
            items_to_remove = [item for item in self.queue if item.status == status_filter]
            for item in items_to_remove:
                self.queue.remove(item)
                del self._queue_map[item.file_path]
            logger.info(f"Cleared {len(items_to_remove)} items with status {status_filter.value}")
        
        self.queue_cleared.emit()
        self._update_progress()
    
    def reorder_item(self, file_path: str, new_position: int) -> bool:
        """
        Move an item to a new position in the queue.
        
        Args:
            file_path: Path to the file
            new_position: New index in the queue (0-based)
        
        Returns:
            True if reordered successfully
        """
        abs_path = str(Path(file_path).resolve())
        
        if abs_path not in self._queue_map:
            return False
        
        item = self._queue_map[abs_path]
        self.queue.remove(item)
        
        # Clamp position to valid range
        new_position = max(0, min(new_position, len(self.queue)))
        self.queue.insert(new_position, item)
        
        logger.debug(f"Reordered {abs_path} to position {new_position}")
        self.queue_reordered.emit([item.file_path for item in self.queue])
        
        return True
    
    def move_up(self, file_path: str) -> bool:
        """Move an item up one position in the queue."""
        abs_path = str(Path(file_path).resolve())
        if abs_path not in self._queue_map:
            return False
        
        current_pos = self.queue.index(self._queue_map[abs_path])
        if current_pos > 0:
            return self.reorder_item(abs_path, current_pos - 1)
        return False
    
    def move_down(self, file_path: str) -> bool:
        """Move an item down one position in the queue."""
        abs_path = str(Path(file_path).resolve())
        if abs_path not in self._queue_map:
            return False
        
        current_pos = self.queue.index(self._queue_map[abs_path])
        if current_pos < len(self.queue) - 1:
            return self.reorder_item(abs_path, current_pos + 1)
        return False
    
    def get_next_item(self) -> Optional[QueueItem]:
        """
        Get the next pending item from the queue.
        
        Returns:
            Next QueueItem to process, or None if queue is empty/all completed
        """
        for item in self.queue:
            if item.status == QueueItemStatus.PENDING:
                return item
        return None
    
    def update_item_status(self, file_path: str, status: QueueItemStatus, 
                          error_code: Optional[str] = None,
                          error_message: Optional[str] = None):
        """
        Update the status of a queue item.
        
        Args:
            file_path: Path to the file
            status: New status
            error_code: Error code if status is FAILED
            error_message: Error message if status is FAILED
        """
        abs_path = str(Path(file_path).resolve())
        
        if abs_path not in self._queue_map:
            logger.warning(f"Cannot update status for unknown item: {abs_path}")
            return
        
        item = self._queue_map[abs_path]
        item.status = status
        
        if status == QueueItemStatus.PROCESSING:
            item.started_at = datetime.now()
        elif status in (QueueItemStatus.COMPLETED, QueueItemStatus.FAILED, QueueItemStatus.SKIPPED):
            item.completed_at = datetime.now()
        
        if error_code:
            item.error_code = error_code
            item.error_message = error_message
        
        logger.debug(f"Updated item status: {abs_path} -> {status.value}")
        self.item_updated.emit(item)
        self._update_progress()
    
    def get_queue_items(self, status_filter: Optional[QueueItemStatus] = None) -> List[QueueItem]:
        """
        Get all queue items, optionally filtered by status.
        
        Args:
            status_filter: If provided, only return items with this status
        
        Returns:
            List of QueueItems
        """
        if status_filter is None:
            return self.queue.copy()
        return [item for item in self.queue if item.status == status_filter]
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with counts by status
        """
        stats = {
            'total': len(self.queue),
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for item in self.queue:
            stats[item.status.value] += 1
        
        return stats
    
    def _detect_file_type(self, file_path: str) -> Optional[str]:
        """
        Detect file type from extension.
        
        Returns:
            Type of the file (pdf, image, text, office) or None if unsupported
        """
        ext = Path(file_path).suffix.lower()
        
        type_map = {
            '.pdf': 'pdf',
            '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
            '.tif': 'image', '.tiff': 'image', '.bmp': 'image',
            '.gif': 'image', '.webp': 'image', '.heic': 'image',
            '.txt': 'text', '.md': 'text', '.csv': 'text',
            '.json': 'text', '.xml': 'text', '.yaml': 'text',
            '.doc': 'office', '.docx': 'office',
            '.xls': 'office', '.xlsx': 'office',
            '.ppt': 'office', '.pptx': 'office'
        }
        
        return type_map.get(ext)
    
    @classmethod
    def get_supported_file_types(cls) -> Dict[str, list]:
        """
        Get all supported file types grouped by category.
        
        Returns:
            Dictionary with categories as keys and lists of extensions as values
        """
        return {
            'pdf': ['.pdf'],
            'image': ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif', '.webp', '.heic'],
            'text': ['.txt', '.md', '.csv', '.json', '.xml', '.yaml'],
            'office': ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        }
    
    @classmethod
    def get_supported_extensions(cls) -> list:
        """
        Get flat list of all supported file extensions.
        
        Returns:
            List of all supported extensions including the dot (e.g., '.pdf')
        """
        extensions = []
        for ext_list in cls.get_supported_file_types().values():
            extensions.extend(ext_list)
        return extensions
    
    @classmethod
    def is_supported_file(cls, file_path: str) -> bool:
        """
        Check if a file is supported by extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file extension is supported, False otherwise
        """
        ext = Path(file_path).suffix.lower()
        return ext in cls.get_supported_extensions()
    
    def _update_progress(self):
        """Emit progress signal with current completion stats."""
        stats = self.get_statistics()
        completed = stats['completed'] + stats['failed'] + stats['skipped']
        total = stats['total']
        self.progress_changed.emit(completed, total)
    
    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hex string of the file hash
        """
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""
