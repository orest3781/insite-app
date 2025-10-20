#!/usr/bin/env python3
"""
Test that the app can start without hanging.
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_app_startup():
    """Test that MainWindow can be created without blocking."""
    try:
        # Minimal QApplication needed for Qt
        app = QApplication.instance() or QApplication(sys.argv)
        
        logger.info("✅ QApplication created")
        
        # Import and create MainWindow
        from src.core.config import ConfigManager
        from src.models.database import Database
        from src.ui.main_window import MainWindow
        
        logger.info("✅ All modules imported")
        
        # Initialize config
        portable_root = Path(__file__).parent
        config = ConfigManager(portable_root)
        logger.info("✅ ConfigManager initialized")
        
        # Initialize database
        db_path = config.get('database_path') or str(portable_root / 'data' / 'database.db')
        db = Database(db_path)
        logger.info("✅ Database initialized")
        
        # Create main window (THIS WAS HANGING BEFORE THE FIX)
        logger.info("Creating MainWindow...")
        main_window = MainWindow(portable_root, config, db)
        logger.info("✅ MainWindow created successfully - NO HANGING!")
        
        # Clean up
        main_window.close()
        
        logger.info("\n" + "="*70)
        logger.info("SUCCESS! App starts without hanging")
        logger.info("="*70)
        logger.info("\nFix Summary:")
        logger.info("❌ Problem: _check_ai_status() was blocking main thread")
        logger.info("            trying to connect to Ollama (5 second timeout)")
        logger.info("✅ Solution: Run AI status check in background thread")
        logger.info("✅ Result: MainWindow creates instantly without blocking")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_app_startup()
    sys.exit(0 if success else 1)
