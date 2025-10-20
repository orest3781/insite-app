"""
Configuration management for the application.
Handles loading, saving, and accessing settings in a portable manner.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from src.utils.logging_utils import get_logger
from src.utils.path_utils import PathUtils


logger = get_logger("config")


class ConfigManager:
    """Manages application configuration with portable paths."""
    
    DEFAULT_CONFIG = {
        "paths": {
            "data_dir": "data",
            "database_file": "data/previewless.db",
            "logs_dir": "logs",
            "models_dir": "models",
            "exports_dir": "exports",
        },
        "ocr": {
            "default_mode": "fast",
            "languages": ["eng"],
            "psm": "auto",
            "oem": "auto",
            "retries": 1,
            "preproc_profile": "light",
        },
        "ollama": {
            "host": "http://localhost:11434",
            "default_model": None,
            "default_model_vision": None,
            "default_model_ocr": None,
            "default_model_text": None,
            "temperature": 0.2,
            "max_tokens": 220,
            "top_p": 0.9,
            "timeout_s": 30,
        },
        "cloud": {
            "enabled_globally": False,
            "provider": None,
            "api_key": None,
        },
        "batch": {
            "concurrency": 1,
            "max_retry_count": 1,
            "stop_on_error": False,
        },
        "search": {
            "fts_descriptions_enabled": True,
            "fts_text_enabled": False,
            "fts_tokenizer": "unicode61",
            "max_query_time_ms": 3000,
        },
        "ui": {
            "theme": "dark",
            "font_scale": 1.0,
            "high_contrast": False,
            "table_page_size": 1000,
        },
        "diagnostics": {
            "debug_mode": False,
            "verbose_logging": False,
            "log_rotation_files": 10,
            "log_rotation_size_mb": 5,
        },
    }
    
    def __init__(self, portable_root: Path):
        """
        Initialize configuration manager.
        
        Args:
            portable_root: Path to the portable root directory
        """
        self.portable_root = portable_root.resolve()
        self.path_utils = PathUtils(self.portable_root)
        self.config_file = self.portable_root / "config" / "settings.json"
        self.config: Dict[str, Any] = {}
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or create configuration
        self.load()
    
    def load(self) -> None:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                
                # Merge with defaults for any missing keys
                self._merge_defaults()
            except Exception as e:
                logger.error(f"Failed to load config: {e}. Using defaults.")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            logger.info("No configuration file found. Creating default.")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "ui.theme")
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "ui.theme")
            value: Value to set
            save: Whether to save configuration to file
        """
        keys = key.split(".")
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        if save:
            self.save()
    
    def _merge_defaults(self) -> None:
        """Merge default configuration with loaded config."""
        def merge_dict(base: dict, overlay: dict) -> dict:
            """Recursively merge dictionaries."""
            result = base.copy()
            for key, value in overlay.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        self.config = merge_dict(self.DEFAULT_CONFIG, self.config)
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """
        Get absolute path from relative path.
        
        Args:
            relative_path: Path relative to portable root
            
        Returns:
            Absolute path
        """
        return self.path_utils.to_absolute(relative_path)
    
    def get_relative_path(self, absolute_path: Path) -> Path:
        """
        Get relative path from absolute path.
        
        Args:
            absolute_path: Absolute path
            
        Returns:
            Path relative to portable root
        """
        return self.path_utils.to_relative(absolute_path)
