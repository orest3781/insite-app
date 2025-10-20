#!/usr/bin/env python3
"""
Quick test to see if app imports and can be created.
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_app():
    """Test app initialization."""
    try:
        logger.info("="*60)
        logger.info("APP STARTUP TEST")
        logger.info("="*60)
        
        logger.info("\n1. Testing imports...")
        from src.ui.main_window import MainWindow
        from src.core.config import ConfigManager
        from src.models.database import Database
        from pathlib import Path
        logger.info("✅ All imports successful")
        
        logger.info("\n2. Testing configuration...")
        portable_root = Path(__file__).parent
        config = ConfigManager(portable_root)
        logger.info("✅ Config loaded")
        
        logger.info("\n3. Testing database...")
        db_path = config.get('database_path') or str(portable_root / 'data' / 'database.db')
        db = Database(db_path)
        logger.info("✅ Database initialized")
        
        logger.info("\n4. Testing app object creation...")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        logger.info("✅ QApplication created")
        
        logger.info("\n5. Testing MainWindow creation...")
        window = MainWindow(portable_root, config, db)
        logger.info("✅ MainWindow created successfully")
        
        logger.info("\n" + "="*60)
        logger.info("SUCCESS - APP CAN BE STARTED")
        logger.info("="*60)
        logger.info("\nThe app is working! You can run it with:")
        logger.info("  python main.py")
        logger.info("\nThe window should appear on your screen.")
        logger.info("If you don't see it, check if it's behind other windows.")
        
        window.close()
        return True
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app()
    sys.exit(0 if success else 1)
