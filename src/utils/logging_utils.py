"""
Logging utilities for the application.
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    log_dir: Path,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 10
) -> logging.Logger:
    """
    Setup application logging with file and console handlers.
    
    Args:
        log_dir: Directory to store log files
        level: Logging level
        max_bytes: Maximum size of each log file
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("previewless_insight")
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_formatter = logging.Formatter(
        "%(levelname)-8s | %(message)s"
    )
    
    # File handler (rotating)
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings+ to console
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (e.g., module name). If None, returns root app logger.
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"previewless_insight.{name}")
    return logging.getLogger("previewless_insight")
