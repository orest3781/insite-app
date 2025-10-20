"""
File watching service for monitoring configured directories.

Tracks inventory by file type and provides real-time updates when files are added/removed.
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QFileSystemWatcher, QTimer

from src.services.queue_manager import QueueManager

logger = logging.getLogger(__name__)


@dataclass
class FileInventory:
    """Inventory statistics for watched directories."""
    total_files: int = 0
    unanalyzed_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class FileWatcherService(QObject):
    """
    Service for watching configured directories and tracking file inventory.
    
    Emits signals when:
    - New files are detected
    - Files are removed
    - Inventory statistics change
    """
    
    # Signals
    file_added = Signal(str)  # file_path
    file_removed = Signal(str)  # file_path
    inventory_updated = Signal(FileInventory)  # updated inventory stats
    error_occurred = Signal(str, str)  # error_code, message
    
    # We use the same supported file extensions as QueueManager for consistency
    
    def __init__(self, config_manager, database):
        """
        Initialize file watcher service.
        
        Args:
            config_manager: ConfigManager instance for settings
            database: Database instance for tracking analyzed files
        """
        super().__init__()
        self.config = config_manager
        self.db = database
        
        # File system watcher
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._on_directory_changed)
        
        # Tracked state
        self.watched_paths: Set[str] = set()
        self.known_files: Set[str] = set()
        self.inventory = FileInventory()
        
        # Debounce timer for batch updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_inventory)
        self.update_timer.setInterval(500)  # 500ms debounce
        
        logger.info("FileWatcherService initialized")
    
    def start_watching(self, paths: Optional[List[str]] = None):
        """
        Start watching directories.
        
        Args:
            paths: List of directory paths to watch. If None, loads from config.
        """
        if paths is None:
            paths = self.config.get('watched_folders', [])
        
        if not paths:
            logger.warning("No paths configured for watching")
            return
        
        for path_str in paths:
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Watch path does not exist: {path}")
                self.error_occurred.emit('WATCH_PATH_MISSING', f"Path not found: {path}")
                continue
            
            if not path.is_dir():
                logger.warning(f"Watch path is not a directory: {path}")
                continue
            
            abs_path = str(path.resolve())
            if abs_path in self.watched_paths:
                logger.debug(f"Already watching: {abs_path}")
                continue
            
            self.watcher.addPath(abs_path)
            self.watched_paths.add(abs_path)
            logger.info(f"Now watching: {abs_path}")
        
        # Initial inventory scan
        self._scan_all_directories()
    
    def stop_watching(self):
        """Stop watching all directories."""
        if self.watched_paths:
            for path in self.watched_paths:
                self.watcher.removePath(path)
            self.watched_paths.clear()
            logger.info("Stopped watching all directories")
    
    def add_watch_path(self, path: str):
        """Add a new directory to watch."""
        path_obj = Path(path)
        if not path_obj.exists() or not path_obj.is_dir():
            logger.error(f"Invalid watch path: {path}")
            self.error_occurred.emit('WATCH_PATH_INVALID', f"Invalid path: {path}")
            return
        
        abs_path = str(path_obj.resolve())
        if abs_path not in self.watched_paths:
            self.watcher.addPath(abs_path)
            self.watched_paths.add(abs_path)
            logger.info(f"Added watch path: {abs_path}")
            
            # Update config
            current_paths = self.config.get('watched_folders', [])
            if abs_path not in current_paths:
                current_paths.append(abs_path)
                self.config.set('watched_folders', current_paths)
                self.config.save()
            
            # Scan new directory
            self._scan_directory(path_obj)
    
    def remove_watch_path(self, path: str):
        """Remove a directory from watching."""
        abs_path = str(Path(path).resolve())
        if abs_path in self.watched_paths:
            self.watcher.removePath(abs_path)
            self.watched_paths.remove(abs_path)
            logger.info(f"Removed watch path: {abs_path}")
            
            # Update config
            current_paths = self.config.get('watched_folders', [])
            if abs_path in current_paths:
                current_paths.remove(abs_path)
                self.config.set('watched_folders', current_paths)
                self.config.save()
            
            # Update inventory
            self._update_inventory()
    
    def get_inventory(self) -> FileInventory:
        """Get current inventory statistics."""
        return self.inventory
    
    def is_supported_file(self, file_path: str) -> bool:
        """
        Check if file extension is supported.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is supported, False otherwise
        """
        path = Path(file_path)
        
        # Exclude analysis JSON files
        if path.suffix.lower() == '.json' and path.stem.endswith('.analysis'):
            return False
        
        # Exclude hidden files and system files
        if path.name.startswith('.') or path.name.startswith('~'):
            return False
        
        # Use QueueManager's supported file check
        return QueueManager.is_supported_file(file_path)
    
    def get_file_category(self, file_path: str) -> Optional[str]:
        """
        Get category for a file based on extension.
        
        Args:
            file_path: Path to the file to categorize
            
        Returns:
            Category name or None if not supported
        """
        ext = Path(file_path).suffix.lower()
        
        # Use QueueManager's supported file types
        for category, extensions in QueueManager.get_supported_file_types().items():
            if ext in extensions:
                return category
        return None
    
    def _on_directory_changed(self, path: str):
        """Handle directory change events (debounced)."""
        logger.debug(f"Directory changed: {path}")
        # Debounce rapid changes
        self.update_timer.start()
    
    def _scan_all_directories(self):
        """Scan all watched directories for initial inventory."""
        logger.info("Scanning all watched directories...")
        self.known_files.clear()
        
        for path_str in self.watched_paths:
            self._scan_directory(Path(path_str))
        
        self._update_inventory()
        logger.info(f"Initial scan complete: {self.inventory.total_files} files found")
    
    def _scan_directory(self, directory: Path):
        """Scan a single directory and update known files."""
        if not directory.exists():
            return
        
        try:
            # Get all files (non-recursive by default, can be configured)
            recursive = self.config.get('watch_recursive', False)
            
            if recursive:
                pattern = '**/*'
            else:
                pattern = '*'
            
            for file_path in directory.glob(pattern):
                if file_path.is_file() and self.is_supported_file(str(file_path)):
                    abs_path = str(file_path.resolve())
                    if abs_path not in self.known_files:
                        self.known_files.add(abs_path)
                        self.file_added.emit(abs_path)
        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            self.error_occurred.emit('SCAN_ERROR', str(e))
    
    def _update_inventory(self):
        """Update inventory statistics and emit signal."""
        try:
            # Count files by type
            by_type: Dict[str, int] = {}
            total = 0
            
            for file_path in self.known_files:
                category = self.get_file_category(file_path)
                if category:
                    by_type[category] = by_type.get(category, 0) + 1
                    total += 1
            
            # Get analyzed file hashes from database
            # In P1 schema, a file is analyzed if it has descriptions or classifications
            analyzed_hashes = set()
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT f.file_hash 
                    FROM files f
                    WHERE EXISTS (
                        SELECT 1 FROM descriptions d WHERE d.file_id = f.file_id
                    ) OR EXISTS (
                        SELECT 1 FROM classifications c WHERE c.file_id = f.file_id
                    )
                """)
                analyzed_hashes = {row[0] for row in cursor.fetchall()}
            
            # Count unanalyzed (files in directory but not fully analyzed in DB)
            unanalyzed = total - len(analyzed_hashes)
            
            # Update inventory
            self.inventory = FileInventory(
                total_files=total,
                unanalyzed_count=unanalyzed,
                by_type=by_type,
                by_status={'pending': unanalyzed, 'analyzed': total - unanalyzed},
                last_updated=datetime.now()
            )
            
            self.inventory_updated.emit(self.inventory)
            logger.debug(f"Inventory updated: {total} total, {unanalyzed} unanalyzed")
        
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            self.error_occurred.emit('INVENTORY_ERROR', str(e))
