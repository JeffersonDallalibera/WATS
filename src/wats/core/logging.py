"""Enhanced logging configuration for WATS application."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        return json.dumps(log_data, ensure_ascii=False)


class WASTLogger:
    """Enhanced logging manager for WATS application."""
    
    def __init__(self, base_dir: Path, log_level: str = "INFO"):
        self.base_dir = base_dir
        self.log_level = getattr(logging, log_level.upper())
        self.loggers: Dict[str, logging.Logger] = {}
        
    def setup_logging(self) -> None:
        """Configure logging for the entire application."""
        # Create logs directory if it doesn't exist
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs (rotating)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "wats_app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
        
        # Structured JSON handler for analysis
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / "wats_structured.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(json_handler)
        
        # Error-only handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "wats_errors.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        root_logger.addHandler(error_handler)
        
        # Performance handler
        perf_handler = logging.FileHandler(
            log_dir / "wats_performance.log",
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(StructuredFormatter())
        
        # Create specialized loggers
        self._setup_module_loggers()
        
    def _setup_module_loggers(self) -> None:
        """Setup specialized loggers for different modules."""
        modules = [
            "src.wats.db",
            "src.wats.api", 
            "src.wats.recording",
            "src.wats.admin_panels",
            "src.wats.app_window"
        ]
        
        for module in modules:
            logger = logging.getLogger(module)
            logger.setLevel(self.log_level)
            self.loggers[module] = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger for a specific module."""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self.log_level)
            self.loggers[name] = logger
        return self.loggers[name]
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics."""
        perf_logger = logging.getLogger("performance")
        extra_data = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            **kwargs
        }
        perf_logger.info(f"Performance: {operation}", extra={'extra_fields': extra_data})
    
    def log_user_action(self, user: str, action: str, **kwargs) -> None:
        """Log user actions for audit trail."""
        audit_logger = logging.getLogger("audit")
        extra_data = {
            "user": user,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        audit_logger.info(f"User action: {action}", extra={'extra_fields': extra_data})


# Global logger instance
_logger_instance: Optional[WASTLogger] = None


def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance for the specified module."""
    if _logger_instance:
        return _logger_instance.get_logger(name)
    return logging.getLogger(name)


def setup_enhanced_logging(base_dir: Path, log_level: str = "INFO") -> WASTLogger:
    """Setup enhanced logging for the application."""
    global _logger_instance
    _logger_instance = WASTLogger(base_dir, log_level)
    _logger_instance.setup_logging()
    return _logger_instance