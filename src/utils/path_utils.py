"""Path utilities for portable root management."""
from pathlib import Path
from typing import Union
import sys


class PathUtils:
    """Utilities for managing portable paths."""
    
    @staticmethod
    def get_portable_root() -> Path:
        """
        Get the portable root directory.
        
        Returns:
            Absolute path to portable root (directory containing main.py)
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return Path(sys.executable).parent.resolve()
        else:
            # Running as script
            # Find main.py in the call stack or use __file__
            main_file = Path(sys.argv[0]).resolve()
            if main_file.is_file():
                return main_file.parent
            # Fallback to current working directory
            return Path.cwd()
    
    def __init__(self, portable_root: Path = None):
        """
        Initialize path utilities.
        
        Args:
            portable_root: Absolute path to the portable root directory.
                          If None, will be auto-detected.
        """
        if portable_root is None:
            portable_root = self.get_portable_root()
        self.portable_root = portable_root.resolve()
    
    def to_relative(self, path: Union[str, Path]) -> Path:
        """
        Convert absolute path to relative path from portable root.
        
        Args:
            path: Absolute or relative path
            
        Returns:
            Path relative to portable root
            
        Raises:
            ValueError: If path is not within portable root
        """
        path = Path(path).resolve()
        
        try:
            return path.relative_to(self.portable_root)
        except ValueError:
            raise ValueError(
                f"Path {path} is not within portable root {self.portable_root}"
            )
    
    def to_absolute(self, path: Union[str, Path]) -> Path:
        """
        Convert relative path to absolute path.
        
        Args:
            path: Relative path from portable root
            
        Returns:
            Absolute path
        """
        path = Path(path)
        
        if path.is_absolute():
            return path
        
        return (self.portable_root / path).resolve()
    
    @staticmethod
    def resolve_path(path: Union[str, Path], base_path: Path = None) -> Path:
        """
        Resolve a path to absolute, using base_path or portable root.
        
        Args:
            path: Path to resolve
            base_path: Base path for relative paths (defaults to portable root)
            
        Returns:
            Resolved absolute path
        """
        path = Path(path)
        
        if path.is_absolute():
            return path.resolve()
        
        if base_path is None:
            base_path = PathUtils.get_portable_root()
        
        return (base_path / path).resolve()
    
    def is_within_portable_root(self, path: Union[str, Path]) -> bool:
        """
        Check if path is within portable root.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is within portable root
        """
        try:
            path = Path(path).resolve()
            path.relative_to(self.portable_root)
            return True
        except ValueError:
            return False
    
    def ensure_relative(self, path: Union[str, Path]) -> Path:
        """
        Ensure path is relative, converting if necessary.
        
        Args:
            path: Path to convert
            
        Returns:
            Relative path
        """
        path = Path(path)
        
        if path.is_absolute():
            return self.to_relative(path)
        
        return path
