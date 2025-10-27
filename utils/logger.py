"""
Logging utilities for SEO Auditor
Supports console and file logging with rotation, structured logging, and colored output
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import threading


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record):
        """Format log record with colors"""
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            # Add color to log level
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
                )

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class ContextFilter(logging.Filter):
    """
    Filter to add context information to log records
    """

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize context filter

        Args:
            context: Dictionary of context information to add
        """
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class SEOAuditorLogger:
    """
    Custom logger class for SEO Auditor with advanced features
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure single logger instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize logger (only once due to singleton)"""
        if not hasattr(self, 'initialized'):
            self.loggers = {}
            self.initialized = True


def setup_logger(
        name: str,
        config: Optional[Dict] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure logger with console and file handlers

    Args:
        name: Logger name (usually __name__)
        config: Optional configuration dictionary from config.yaml
        log_level: Optional override for log level
        log_file: Optional override for log file path

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Parse configuration
    if config is None:
        config = {}

    logging_config = config.get('logging', {})

    # Determine log level
    level_str = log_level or logging_config.get('log_level', 'INFO')
    level = getattr(logging, level_str.upper(), logging.INFO)
    logger.setLevel(level)

    # Determine log format
    log_format = logging_config.get(
        'format',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    date_format = logging_config.get('date_format', '%Y-%m-%d %H:%M:%S')

    # Console handler
    if logging_config.get('console_output', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Use colored formatter for console
        console_formatter = ColoredFormatter(log_format, datefmt=date_format)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)

    # File handler with rotation
    if logging_config.get('file_output', True):
        # Create logs directory
        log_file_path = log_file or logging_config.get('log_file', 'logs/seo_auditor.log')
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Get rotation settings
        max_bytes = logging_config.get('max_file_size_mb', 10) * 1024 * 1024
        backup_count = logging_config.get('backup_count', 5)

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)

        # Use standard formatter for file
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def setup_json_logger(
        name: str,
        log_file: str = 'logs/seo_auditor.json',
        log_level: str = 'INFO',
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
) -> logging.Logger:
    """
    Set up logger with JSON output for structured logging

    Args:
        name: Logger name
        log_file: Path to JSON log file
        log_level: Logging level
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured JSON logger
    """
    logger = logging.getLogger(f"{name}.json")

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Create log directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)

    # Set JSON formatter
    json_formatter = JSONFormatter()
    file_handler.setFormatter(json_formatter)

    logger.addHandler(file_handler)
    logger.propagate = False

    return logger


def get_logger(name: str, config: Optional[Dict] = None) -> logging.Logger:
    """
    Get or create logger instance

    Args:
        name: Logger name
        config: Optional configuration dictionary

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # Setup if not already configured
    if not logger.handlers:
        return setup_logger(name, config)

    return logger


class LogContext:
    """
    Context manager for adding temporary context to logs

    Usage:
        with LogContext(logger, {'request_id': '123', 'user': 'admin'}):
            logger.info("Processing request")  # Will include request_id and user
    """

    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        """
        Initialize log context

        Args:
            logger: Logger instance
            context: Context data to add to logs
        """
        self.logger = logger
        self.context = context
        self.filter = ContextFilter(context)

    def __enter__(self):
        """Add context filter to logger"""
        self.logger.addFilter(self.filter)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove context filter from logger"""
        self.logger.removeFilter(self.filter)


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls with arguments and return values

    Usage:
        @log_function_call(logger)
        def my_function(arg1, arg2):
            return result
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func_name} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"{func_name} raised exception: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def log_execution_time(logger: logging.Logger):
    """
    Decorator to log function execution time

    Usage:
        @log_execution_time(logger)
        def slow_function():
            # expensive operation
            pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            func_name = func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func_name} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func_name} failed after {execution_time:.3f}s: {e}",
                    exc_info=True
                )
                raise

        return wrapper

    return decorator


class AuditLogger:
    """
    Specialized logger for audit events (API calls, crawls, etc.)
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize audit logger"""
        self.logger = setup_json_logger(
            'seo_auditor.audit',
            log_file='logs/audit.json',
            log_level='INFO'
        )
        self.session_id = None

    def start_session(self, url: str, session_id: str):
        """Log audit session start"""
        self.session_id = session_id
        self.logger.info(
            "Audit session started",
            extra={'extra_data': {
                'session_id': session_id,
                'url': url,
                'event': 'session_start'
            }}
        )

    def end_session(self, results: Dict[str, Any]):
        """Log audit session end"""
        if self.session_id:
            self.logger.info(
                "Audit session completed",
                extra={'extra_data': {
                    'session_id': self.session_id,
                    'event': 'session_end',
                    'results_summary': results
                }}
            )
            self.session_id = None

    def log_api_call(self, api_name: str, endpoint: str, status: str):
        """Log API call"""
        self.logger.info(
            f"API call to {api_name}",
            extra={'extra_data': {
                'session_id': self.session_id,
                'api': api_name,
                'endpoint': endpoint,
                'status': status,
                'event': 'api_call'
            }}
        )

    def log_crawl_event(self, url: str, status_code: int, duration: float):
        """Log crawl event"""
        self.logger.info(
            f"Crawled {url}",
            extra={'extra_data': {
                'session_id': self.session_id,
                'url': url,
                'status_code': status_code,
                'duration_ms': duration * 1000,
                'event': 'crawl'
            }}
        )

    def log_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        """Log error event"""
        error_data = {
            'session_id': self.session_id,
            'error_type': error_type,
            'message': message,
            'event': 'error'
        }
        if details:
            error_data.update(details)

        self.logger.error(
            f"Error: {error_type}",
            extra={'extra_data': error_data}
        )


# Performance monitoring logger
class PerformanceLogger:
    """
    Logger for tracking performance metrics
    """

    def __init__(self):
        """Initialize performance logger"""
        self.logger = setup_json_logger(
            'seo_auditor.performance',
            log_file='logs/performance.json',
            log_level='DEBUG'
        )

    def log_metric(
            self,
            metric_name: str,
            value: float,
            unit: str = 'ms',
            context: Optional[Dict] = None
    ):
        """
        Log performance metric

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            context: Additional context
        """
        metric_data = {
            'metric': metric_name,
            'value': value,
            'unit': unit,
            'event': 'performance_metric'
        }

        if context:
            metric_data.update(context)

        self.logger.info(
            f"Performance: {metric_name} = {value}{unit}",
            extra={'extra_data': metric_data}
        )


# Utility function to suppress logs from noisy libraries
def suppress_library_logs(library_names: list, level: str = 'WARNING'):
    """
    Suppress logs from specific libraries

    Args:
        library_names: List of library names to suppress
        level: Minimum log level to show
    """
    log_level = getattr(logging, level.upper(), logging.WARNING)

    for library in library_names:
        logging.getLogger(library).setLevel(log_level)


# Default logger suppression for common noisy libraries
suppress_library_logs([
    'urllib3',
    'requests',
    'selenium',
    'PIL',
    'matplotlib',
    'asyncio'
])
