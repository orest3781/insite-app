"""
Diagnostics service for checking system dependencies and health.

This module performs comprehensive checks of:
- Tesseract OCR installation and availability
- Ollama LLM service connectivity
- GPU availability for acceleration
- Database integrity
- File system permissions
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import logging

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from PySide6.QtCore import QSysInfo
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

logger = logging.getLogger(__name__)


class DiagnosticsService:
    """
    System diagnostics and health check service.
    
    Performs comprehensive checks of all external dependencies
    and system resources required for application operation.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize diagnostics service.
        
        Args:
            config_manager: Optional ConfigManager instance for reading settings
        """
        self.config = config_manager
        self.results: Dict[str, Any] = {}
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all diagnostic checks.
        
        Returns:
            Dictionary with results from all checks
        """
        logger.info("Running comprehensive system diagnostics...")
        
        self.results = {
            "timestamp": self._get_timestamp(),
            "platform": self._check_platform(),
            "python": self._check_python(),
            "dependencies": self._check_dependencies(),
            "tesseract": self._check_tesseract(),
            "ollama": self._check_ollama(),
            "gpu": self._check_gpu(),
            "database": self._check_database(),
            "filesystem": self._check_filesystem(),
            "overall_status": "pending"
        }
        
        # Determine overall status
        self.results["overall_status"] = self._calculate_overall_status()
        
        logger.info(f"Diagnostics complete. Status: {self.results['overall_status']}")
        
        return self.results
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _check_platform(self) -> Dict[str, Any]:
        """Check platform information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "status": "ok"
        }
    
    def _check_python(self) -> Dict[str, Any]:
        """Check Python version and environment."""
        version_info = sys.version_info
        
        is_compatible = version_info.major == 3 and version_info.minor >= 10
        
        return {
            "version": f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            "version_full": sys.version,
            "executable": sys.executable,
            "compatible": is_compatible,
            "status": "ok" if is_compatible else "error",
            "message": "Python 3.10+ required" if not is_compatible else "Compatible"
        }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check Python package dependencies."""
        dependencies = {
            "PySide6": PYSIDE6_AVAILABLE,
            "pytesseract": TESSERACT_AVAILABLE,
            "PIL": TESSERACT_AVAILABLE,  # Pillow
            "requests": REQUESTS_AVAILABLE,
        }
        
        missing = [name for name, available in dependencies.items() if not available]
        
        return {
            "installed": dependencies,
            "missing": missing,
            "all_present": len(missing) == 0,
            "status": "ok" if len(missing) == 0 else "warning",
            "message": f"Missing: {', '.join(missing)}" if missing else "All dependencies installed"
        }
    
    def _check_tesseract(self) -> Dict[str, Any]:
        """Check Tesseract OCR installation and configuration."""
        if not TESSERACT_AVAILABLE:
            return {
                "installed": False,
                "status": "error",
                "message": "pytesseract package not installed"
            }
        
        result = {
            "installed": False,
            "path": None,
            "version": None,
            "languages": [],
            "status": "error",
            "message": "Tesseract not found"
        }
        
        try:
            # Try to get Tesseract executable path
            tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
            
            # Check if it exists
            if shutil.which(tesseract_cmd) or Path(tesseract_cmd).exists():
                result["installed"] = True
                result["path"] = tesseract_cmd
                
                # Get version
                try:
                    version_output = pytesseract.get_tesseract_version()
                    result["version"] = str(version_output)
                except Exception as e:
                    logger.warning(f"Could not get Tesseract version: {e}")
                
                # Get available languages
                try:
                    langs = pytesseract.get_languages()
                    result["languages"] = langs
                except Exception as e:
                    logger.warning(f"Could not get Tesseract languages: {e}")
                    result["languages"] = ["Unknown"]
                
                result["status"] = "ok"
                result["message"] = f"Tesseract found: {result['version']}"
            else:
                result["message"] = f"Tesseract executable not found at: {tesseract_cmd}"
                result["status"] = "error"
        
        except Exception as e:
            logger.error(f"Tesseract check failed: {e}")
            result["message"] = f"Error checking Tesseract: {str(e)}"
            result["status"] = "error"
        
        return result
    
    def _check_ollama(self) -> Dict[str, Any]:
        """Check Ollama LLM service connectivity."""
        if not REQUESTS_AVAILABLE:
            return {
                "available": False,
                "status": "error",
                "message": "requests package not installed"
            }
        
        # Get Ollama host from config or use default
        ollama_host = "http://localhost:11434"
        if self.config:
            ollama_host = self.config.get("ollama.host", ollama_host)
        
        result = {
            "available": False,
            "host": ollama_host,
            "models": [],
            "status": "error",
            "message": "Ollama service not reachable"
        }
        
        try:
            # Try to connect to Ollama API
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            
            if response.status_code == 200:
                result["available"] = True
                result["status"] = "ok"
                
                # Parse models list
                try:
                    data = response.json()
                    models = data.get("models", [])
                    result["models"] = [m.get("name", "Unknown") for m in models]
                    result["message"] = f"Ollama running, {len(models)} models available"
                except Exception as e:
                    logger.warning(f"Could not parse Ollama models: {e}")
                    result["message"] = "Ollama running (could not list models)"
            else:
                result["message"] = f"Ollama returned status {response.status_code}"
                result["status"] = "warning"
        
        except requests.exceptions.ConnectionError:
            result["message"] = f"Could not connect to Ollama at {ollama_host}"
            result["status"] = "error"
        except requests.exceptions.Timeout:
            result["message"] = "Ollama connection timed out"
            result["status"] = "error"
        except Exception as e:
            logger.error(f"Ollama check failed: {e}")
            result["message"] = f"Error checking Ollama: {str(e)}"
            result["status"] = "error"
        
        return result
    
    def _check_gpu(self) -> Dict[str, Any]:
        """Check GPU availability for potential acceleration."""
        result = {
            "available": False,
            "vendor": None,
            "devices": [],
            "status": "info",
            "message": "GPU not detected or not supported"
        }
        
        # Try to detect NVIDIA GPU (CUDA)
        try:
            nvidia_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if nvidia_result.returncode == 0:
                result["available"] = True
                result["vendor"] = "NVIDIA"
                result["devices"] = nvidia_result.stdout.strip().split('\n')
                result["status"] = "ok"
                result["message"] = f"NVIDIA GPU detected: {result['devices'][0]}"
                return result
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try to detect AMD GPU (ROCm)
        try:
            rocm_result = subprocess.run(
                ["rocm-smi", "--showproductname"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if rocm_result.returncode == 0:
                result["available"] = True
                result["vendor"] = "AMD"
                result["status"] = "ok"
                result["message"] = "AMD GPU detected"
                return result
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # GPU not critical for this application
        result["message"] = "No GPU detected (not required)"
        result["status"] = "info"
        
        return result
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and integrity."""
        if not self.config:
            return {
                "accessible": False,
                "status": "warning",
                "message": "Config manager not available"
            }
        
        result = {
            "accessible": False,
            "path": None,
            "size_mb": 0,
            "schema_version": 0,
            "status": "error",
            "message": "Database check failed"
        }
        
        try:
            # Get database path from config
            db_path = self.config.get("paths.database_file", "data/previewless.db")
            
            # Convert to absolute path
            from src.utils.path_utils import PathUtils
            abs_path = PathUtils.resolve_path(db_path)
            result["path"] = str(abs_path)
            
            # Check if database exists
            if abs_path.exists():
                result["size_mb"] = round(abs_path.stat().st_size / (1024 * 1024), 2)
                
                # Try to connect and get schema version
                try:
                    from src.models.database import Database
                    db = Database(str(abs_path))
                    result["schema_version"] = db.get_schema_version()
                    result["accessible"] = True
                    result["status"] = "ok"
                    result["message"] = f"Database accessible (v{result['schema_version']}, {result['size_mb']} MB)"
                except Exception as e:
                    logger.error(f"Database connection failed: {e}")
                    result["message"] = f"Database exists but not accessible: {str(e)}"
                    result["status"] = "warning"
            else:
                result["message"] = "Database not yet created (will be initialized on first run)"
                result["status"] = "info"
        
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            result["message"] = f"Error checking database: {str(e)}"
            result["status"] = "error"
        
        return result
    
    def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem permissions and disk space."""
        result = {
            "writable": False,
            "readable": False,
            "disk_space_gb": 0,
            "status": "error",
            "message": "Filesystem check failed"
        }
        
        try:
            # Get portable root
            from src.utils.path_utils import PathUtils
            portable_root = PathUtils.get_portable_root()
            
            # Check read permissions
            result["readable"] = os.access(portable_root, os.R_OK)
            
            # Check write permissions
            result["writable"] = os.access(portable_root, os.W_OK)
            
            # Get disk space
            if sys.platform == 'win32':
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    str(portable_root), None, None, ctypes.pointer(free_bytes)
                )
                result["disk_space_gb"] = round(free_bytes.value / (1024**3), 2)
            else:
                stat = os.statvfs(portable_root)
                result["disk_space_gb"] = round((stat.f_bavail * stat.f_frsize) / (1024**3), 2)
            
            # Determine status
            if result["readable"] and result["writable"]:
                result["status"] = "ok"
                result["message"] = f"Filesystem accessible, {result['disk_space_gb']} GB free"
            else:
                result["status"] = "error"
                issues = []
                if not result["readable"]:
                    issues.append("not readable")
                if not result["writable"]:
                    issues.append("not writable")
                result["message"] = f"Filesystem issues: {', '.join(issues)}"
        
        except Exception as e:
            logger.error(f"Filesystem check failed: {e}")
            result["message"] = f"Error checking filesystem: {str(e)}"
            result["status"] = "error"
        
        return result
    
    def _calculate_overall_status(self) -> str:
        """
        Calculate overall system status based on all checks.
        
        Returns:
            'ok', 'warning', or 'error'
        """
        critical_checks = ["python", "dependencies", "filesystem"]
        important_checks = ["tesseract", "database"]
        optional_checks = ["ollama", "gpu"]
        
        # Check for critical errors
        for check in critical_checks:
            if self.results.get(check, {}).get("status") == "error":
                return "error"
        
        # Check for important warnings
        warning_count = 0
        for check in important_checks:
            if self.results.get(check, {}).get("status") in ("error", "warning"):
                warning_count += 1
        
        if warning_count >= 2:
            return "warning"
        
        # Check optional components
        for check in optional_checks:
            if self.results.get(check, {}).get("status") == "error":
                return "warning"
        
        return "ok"
    
    def get_status_summary(self) -> str:
        """
        Get human-readable status summary.
        
        Returns:
            Multi-line string with status summary
        """
        if not self.results:
            return "No diagnostics run yet"
        
        lines = []
        lines.append(f"Overall Status: {self.results['overall_status'].upper()}")
        lines.append("")
        
        for category, data in self.results.items():
            if category in ("timestamp", "overall_status", "platform"):
                continue
            
            if isinstance(data, dict) and "status" in data:
                status_icon = {"ok": "✓", "warning": "⚠", "error": "✗", "info": "ℹ"}.get(data["status"], "?")
                lines.append(f"{status_icon} {category.title()}: {data.get('message', 'N/A')}")
        
        return "\n".join(lines)
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export diagnostics results as dictionary."""
        return self.results.copy()
    
    def export_to_file(self, file_path: str):
        """
        Export diagnostics results to JSON file.
        
        Args:
            file_path: Path to output file
        """
        import json
        with open(file_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Diagnostics exported to {file_path}")


# Convenience function
def run_diagnostics(config_manager=None) -> DiagnosticsService:
    """
    Run system diagnostics and return service instance.
    
    Args:
        config_manager: Optional ConfigManager instance
        
    Returns:
        DiagnosticsService with completed checks
    """
    service = DiagnosticsService(config_manager)
    service.run_all_checks()
    return service
