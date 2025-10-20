import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.queue_manager import QueueManager
from src.services.file_watcher import FileWatcherService


class TestFileTypeFiltering(unittest.TestCase):
    """Test file type filtering functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock dependencies
        self.mock_db = MagicMock()
        self.mock_config = MagicMock()
        
        # Create instances with mocked dependencies
        self.queue_manager = QueueManager(self.mock_db)
    
    def test_supported_file_types(self):
        """Test that supported file types are correctly defined."""
        file_types = self.queue_manager.get_supported_file_types()
        
        # Check that we have the expected categories
        self.assertIn('pdf', file_types)
        self.assertIn('image', file_types)
        self.assertIn('text', file_types)
        self.assertIn('office', file_types)
        
        # Check that each category has extensions
        for category, extensions in file_types.items():
            self.assertTrue(len(extensions) > 0, f"Category {category} has no extensions")
            
            # Check that each extension starts with a dot
            for ext in extensions:
                self.assertTrue(ext.startswith('.'), f"Extension {ext} doesn't start with a dot")
    
    def test_supported_extensions_flat_list(self):
        """Test that get_supported_extensions returns a flat list of all extensions."""
        extensions = self.queue_manager.get_supported_extensions()
        
        # Check that we have extensions
        self.assertTrue(len(extensions) > 0)
        
        # Check common extensions are included
        self.assertIn('.pdf', extensions)
        self.assertIn('.jpg', extensions)
        self.assertIn('.png', extensions)
        self.assertIn('.txt', extensions)
    
    def test_is_supported_file(self):
        """Test is_supported_file method with various file types."""
        # Test supported files
        self.assertTrue(self.queue_manager.is_supported_file('document.pdf'))
        self.assertTrue(self.queue_manager.is_supported_file('image.jpg'))
        self.assertTrue(self.queue_manager.is_supported_file('data.txt'))
        self.assertTrue(self.queue_manager.is_supported_file('spreadsheet.xlsx'))
        
        # Test unsupported files
        self.assertFalse(self.queue_manager.is_supported_file('archive.zip'))
        self.assertFalse(self.queue_manager.is_supported_file('video.mp4'))
        self.assertFalse(self.queue_manager.is_supported_file('audio.mp3'))
        self.assertFalse(self.queue_manager.is_supported_file('executable.exe'))
        self.assertFalse(self.queue_manager.is_supported_file('noextension'))
    
    def test_detect_file_type(self):
        """Test _detect_file_type method."""
        # Test detection for various file types
        self.assertEqual(self.queue_manager._detect_file_type('document.pdf'), 'pdf')
        self.assertEqual(self.queue_manager._detect_file_type('image.jpg'), 'image')
        self.assertEqual(self.queue_manager._detect_file_type('image.png'), 'image')
        self.assertEqual(self.queue_manager._detect_file_type('data.txt'), 'text')
        self.assertEqual(self.queue_manager._detect_file_type('document.docx'), 'office')
        
        # Test unsupported file types
        self.assertIsNone(self.queue_manager._detect_file_type('archive.zip'))
        self.assertIsNone(self.queue_manager._detect_file_type('video.mp4'))
        self.assertIsNone(self.queue_manager._detect_file_type('noextension'))
    
    def test_add_item_filters_unsupported_files(self):
        """Test that add_item filters out unsupported files."""
        # Test with supported file
        with patch('pathlib.Path.resolve', return_value=Path('/test/document.pdf')):
            result = self.queue_manager.add_item('/test/document.pdf')
            self.assertTrue(result)
        
        # Test with unsupported file
        with patch('pathlib.Path.resolve', return_value=Path('/test/video.mp4')):
            result = self.queue_manager.add_item('/test/video.mp4')
            self.assertFalse(result)
    
    def test_file_watcher_uses_queue_manager_supported_types(self):
        """Test that FileWatcherService uses QueueManager's supported file types."""
        # Create a FileWatcherService instance
        with patch('src.services.file_watcher.QFileSystemWatcher'):
            file_watcher = FileWatcherService(self.mock_config, self.mock_db)
            
            # Test supported files
            self.assertTrue(file_watcher.is_supported_file('document.pdf'))
            self.assertTrue(file_watcher.is_supported_file('image.jpg'))
            
            # Test hidden files are not supported regardless of extension
            self.assertFalse(file_watcher.is_supported_file('.hidden.pdf'))
            self.assertFalse(file_watcher.is_supported_file('~temp.jpg'))
            
            # Test analysis JSON files are not supported
            self.assertFalse(file_watcher.is_supported_file('document.analysis.json'))


if __name__ == '__main__':
    unittest.main()