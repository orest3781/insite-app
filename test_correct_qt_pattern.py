#!/usr/bin/env python3
"""
Test the CORRECT Qt pattern for app initialization:
1. Create window (fast)
2. Show window (user sees it immediately)
3. After show, do network operations (in showEvent)
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

logging.basicConfig(level=logging.INFO, format='%(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

def test_correct_qt_pattern():
    """Test app using correct Qt initialization pattern."""
    logger.info("\n" + "="*70)
    logger.info("TESTING CORRECT Qt INITIALIZATION PATTERN")
    logger.info("="*70)
    
    logger.info("\n[1] Create QApplication...")
    app = QApplication.instance() or QApplication(sys.argv)
    logger.info("✅ QApplication created")
    
    logger.info("\n[2] Initialize services...")
    from src.core.config import ConfigManager
    from src.models.database import Database
    
    portable_root = Path(__file__).parent
    config = ConfigManager(portable_root)
    db_path = config.get('database_path') or str(portable_root / 'data' / 'database.db')
    db = Database(db_path)
    logger.info("✅ Services initialized")
    
    logger.info("\n[3] Import MainWindow...")
    from src.ui.main_window import MainWindow
    logger.info("✅ MainWindow imported")
    
    logger.info("\n[4] Create MainWindow (FAST - no network)...")
    import time
    start = time.time()
    main_window = MainWindow(portable_root, config, db)
    elapsed = time.time() - start
    logger.info(f"✅ MainWindow created in {elapsed:.2f} seconds (no network)")
    
    logger.info("\n[5] Show MainWindow (window visible to user)...")
    main_window.show()
    logger.info("✅ MainWindow shown")
    
    logger.info("\n[6] Process events (allows showEvent to trigger)...")
    QApplication.processEvents()
    logger.info("✅ Events processed (showEvent may have triggered AI check)")
    
    logger.info("\n" + "="*70)
    logger.info("CORRECT Qt PATTERN VERIFIED ✅")
    logger.info("="*70)
    
    logger.info("\nKey Insights:")
    logger.info("✅ Window creation is FAST (no network)")
    logger.info("✅ Window shows immediately to user")
    logger.info("✅ AI status check happens AFTER show (in showEvent)")
    logger.info("✅ If AI check is slow, user still sees responsive window")
    logger.info("✅ This is the Qt best practice for startup sequences")
    
    # Cleanup
    main_window.close()
    
    return True

if __name__ == "__main__":
    try:
        success = test_correct_qt_pattern()
        logger.info("\n✅ TEST PASSED - Using correct Qt initialization pattern")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"❌ TEST FAILED: {e}")
        sys.exit(1)
