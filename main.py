"""
Previewless Insight Viewer
Main entry point for the application.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.core.config import ConfigManager
from src.ui.main_window import MainWindow
from src.utils.logging_utils import setup_logging
from src.models.database import get_database
from src.utils.path_utils import PathUtils
# Import database extensions for backward compatibility
import src.models.database_extensions


def main() -> int:
    """Main application entry point."""
    # Set high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Previewless Insight Viewer")
    app.setOrganizationName("PreviewlessInsight")
    app.setApplicationVersion("1.0.0")
    
    # Initialize portable root
    portable_root = Path(__file__).parent.resolve()
    
    # Setup logging
    log_dir = portable_root / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = setup_logging(log_dir)
    logger.info("=" * 60)
    logger.info("Previewless Insight Viewer starting")
    logger.info(f"Portable root: {portable_root}")
    logger.info("=" * 60)
    
    try:
        # Initialize configuration
        config_manager = ConfigManager(portable_root)
        
        # Initialize database
        db_path = config_manager.get("paths.database_file", "data/previewless.db")
        abs_db_path = PathUtils.resolve_path(db_path, portable_root)
        database = get_database(str(abs_db_path))
        logger.info(f"Database initialized: {abs_db_path}")
        
        # Load theme
        theme_name = config_manager.get("ui.theme", "dark")
        theme_path = portable_root / "config" / "themes" / f"{theme_name}.qss"
        
        if theme_path.exists():
            with open(theme_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            logger.info(f"Loaded theme: {theme_name}")
        else:
            logger.warning(f"Theme file not found: {theme_path}")
        
        # Create and show main window
        main_window = MainWindow(portable_root, config_manager, database)
        main_window.show()
        
        logger.info("Application initialized successfully")
        
        # Run application
        return app.exec()
        
    except Exception as e:
        logger.exception(f"Fatal error during startup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
