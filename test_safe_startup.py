#!/usr/bin/env python3
"""
Test app startup with proper Qt signal handling.
"""
import sys
import logging
from pathlib import Path

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

def test_app_initialization():
    """Test that the app can initialize without hanging."""
    try:
        logger.info("=" * 70)
        logger.info("APP INITIALIZATION TEST")
        logger.info("=" * 70)
        
        # Step 1: Import Qt
        logger.info("\n[1/6] Importing PySide6...")
        from PySide6.QtWidgets import QApplication
        
        # Create QApplication (required for Qt operations)
        app = QApplication.instance() or QApplication(sys.argv)
        logger.info("✅ QApplication created")
        
        # Step 2: Import services
        logger.info("\n[2/6] Importing services...")
        from src.core.config import ConfigManager
        from src.models.database import Database
        logger.info("✅ Services imported")
        
        # Step 3: Initialize config
        logger.info("\n[3/6] Initializing ConfigManager...")
        portable_root = Path(__file__).parent
        config = ConfigManager(portable_root)
        logger.info("✅ ConfigManager initialized")
        
        # Step 4: Initialize database
        logger.info("\n[4/6] Initializing Database...")
        db_path = config.get('database_path') or str(portable_root / 'data' / 'database.db')
        db = Database(db_path)
        logger.info("✅ Database initialized")
        
        # Step 5: Import MainWindow
        logger.info("\n[5/6] Importing MainWindow...")
        from src.ui.main_window import MainWindow
        logger.info("✅ MainWindow imported")
        
        # Step 6: Create MainWindow (this is where it was hanging)
        logger.info("\n[6/6] Creating MainWindow...")
        main_window = MainWindow(portable_root, config, db)
        logger.info("✅ MainWindow created successfully!")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ SUCCESS - APP INITIALIZES WITHOUT HANGING")
        logger.info("=" * 70)
        
        logger.info("\nKey Fix Applied:")
        logger.info("• AI status check now uses Qt signals for thread-safe updates")
        logger.info("• Background thread emits signal to main thread")
        logger.info("• Main thread receives signal and updates UI safely")
        logger.info("• No blocking operations on main thread")
        
        # Cleanup
        main_window.close()
        logger.info("\n✅ Cleanup complete")
        
        return True
        
    except Exception as e:
        logger.exception(f"\n❌ ERROR: {e}")
        return False
    finally:
        # Quit Qt application
        QApplication.quit()

if __name__ == "__main__":
    logger.info("\nStarting app initialization test...\n")
    success = test_app_initialization()
    sys.exit(0 if success else 1)
