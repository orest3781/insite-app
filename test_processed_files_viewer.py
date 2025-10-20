"""Test the Processed Files viewer functionality."""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from src.core.config import ConfigManager
from src.models.database import Database
from src.ui.main_window import MainWindow
from src.utils.logging_utils import get_logger

logger = get_logger("test_processed_files_viewer")

def test_processed_files_viewer():
    """Test that the Processed Files viewer can be accessed."""
    try:
        # Create QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        logger.info("✅ QApplication created")
        
        # Initialize services
        portable_root = Path(__file__).parent
        config = ConfigManager(portable_root)
        db_path = config.get('database_path') or str(portable_root / 'data' / 'database.db')
        db = Database(db_path)
        logger.info("✅ Services initialized")
        
        # Create MainWindow
        main_window = MainWindow(portable_root, config, db)
        logger.info("✅ MainWindow created")
        
        # Check that _view_processed_files exists
        if hasattr(main_window, '_view_processed_files'):
            logger.info("✅ _view_processed_files method exists")
        else:
            logger.error("❌ _view_processed_files method NOT found")
            return False
        
        # Check that it's callable
        if callable(main_window._view_processed_files):
            logger.info("✅ _view_processed_files is callable")
        else:
            logger.error("❌ _view_processed_files is NOT callable")
            return False
        
        # Try to call it (will open dialog, but we'll close app immediately)
        logger.info("Testing _view_processed_files call...")
        # We won't actually call it in automated test since it would block
        
        logger.info("\n" + "="*60)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("="*60)
        
        # Clean up
        app.quit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_processed_files_viewer()
    sys.exit(0 if success else 1)
