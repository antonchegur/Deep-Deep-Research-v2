"""
Centralized Logging Configuration

This module provides a centralized logging system for the application with support for
custom handlers, formatters, and log levels.
"""

import os
import sys
import json
import logging
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class LogLevel(Enum):
    """Standard log levels with descriptive names."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Predefined log formats for different use cases."""
    SIMPLE = '%(levelname)s - %(message)s'
    STANDARD = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DETAILED = '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    JSON = 'json'  # Special format that will log as JSON objects


class FileRotationPolicy(Enum):
    """Rotation policies for file handlers."""
    SIZE = 'size'       # Rotate based on file size
    DAILY = 'daily'     # Rotate daily
    WEEKLY = 'weekly'   # Rotate weekly
    MONTHLY = 'monthly' # Rotate monthly


# Global logging configuration state
_logging_initialized = False
_root_logger = logging.getLogger()
_log_dir = "logs"
_handlers = {}


def configure_logging(
    level: Union[LogLevel, str, int] = LogLevel.INFO,
    format_style: Union[LogFormat, str] = LogFormat.STANDARD,
    log_to_console: bool = True,
    log_to_file: bool = False,
    log_dir: str = "logs",
    file_name: str = "app.log",
    rotation_policy: Optional[FileRotationPolicy] = FileRotationPolicy.DAILY,
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    additional_handlers: Optional[List[logging.Handler]] = None
) -> None:
    """
    Configure the application-wide logging system.
    
    Args:
        level: Log level for the root logger
        format_style: Format style for log messages
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        log_dir: Directory for log files
        file_name: Name of the main log file
        rotation_policy: How log files should rotate
        max_file_size_mb: Maximum size of log files before rotation (in MB)
        backup_count: Number of backup files to keep
        additional_handlers: Additional log handlers to add
    """
    global _logging_initialized, _root_logger, _log_dir
    
    # Store log dir for later use
    _log_dir = log_dir
    
    # Convert level if needed
    if isinstance(level, LogLevel):
        level = level.value
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Convert format if needed
    if isinstance(format_style, LogFormat):
        format_str = format_style.value
    else:
        format_str = format_style
    
    # Reset root logger handlers
    for handler in list(_root_logger.handlers):
        _root_logger.removeHandler(handler)
    
    # Set log level
    _root_logger.setLevel(level)
    
    # Create console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if format_str == 'json':
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(format_str)
        
        console_handler.setFormatter(formatter)
        _root_logger.addHandler(console_handler)
        _handlers['console'] = console_handler
    
    # Create file handler if requested
    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, file_name)
        
        if rotation_policy == FileRotationPolicy.SIZE:
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count
            )
        else:
            # Time-based rotation
            when_map = {
                FileRotationPolicy.DAILY: 'midnight',
                FileRotationPolicy.WEEKLY: 'W0',  # Monday
                FileRotationPolicy.MONTHLY: 'M'
            }
            
            file_handler = TimedRotatingFileHandler(
                file_path,
                when=when_map.get(rotation_policy, 'midnight'),
                backupCount=backup_count
            )
        
        file_handler.setLevel(level)
        
        if format_str == 'json':
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(format_str)
        
        file_handler.setFormatter(formatter)
        _root_logger.addHandler(file_handler)
        _handlers['file'] = file_handler
    
    # Add any additional handlers
    if additional_handlers:
        for handler in additional_handlers:
            _root_logger.addHandler(handler)
            _handlers[f'additional_{id(handler)}'] = handler
    
    _logging_initialized = True
    
    # Log configuration info
    _root_logger.info(
        f"Logging configured: level={logging.getLevelName(level)}, "
        f"console={log_to_console}, file={log_to_file}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    This ensures that all loggers use the same configuration.
    
    Args:
        name: Logger name, typically __name__ from the calling module
        
    Returns:
        Configured logger instance
    """
    # Make sure logging is initialized with at least default config
    if not _logging_initialized:
        configure_logging()
    
    return logging.getLogger(name)


def add_file_handler(
    file_name: str,
    level: Union[LogLevel, str, int] = LogLevel.INFO,
    format_style: Union[LogFormat, str] = LogFormat.STANDARD,
    rotation_policy: Optional[FileRotationPolicy] = FileRotationPolicy.DAILY,
    max_file_size_mb: int = 10,
    backup_count: int = 5
) -> None:
    """
    Add a file handler to the root logger for a specific file.
    
    Args:
        file_name: Name of the log file
        level: Log level for this handler
        format_style: Format style for log messages
        rotation_policy: How log files should rotate
        max_file_size_mb: Maximum size of log files before rotation (in MB)
        backup_count: Number of backup files to keep
    """
    # Convert level if needed
    if isinstance(level, LogLevel):
        level = level.value
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Convert format if needed
    if isinstance(format_style, LogFormat):
        format_str = format_style.value
    else:
        format_str = format_style
    
    # Create log directory if it doesn't exist
    os.makedirs(_log_dir, exist_ok=True)
    file_path = os.path.join(_log_dir, file_name)
    
    # Create the appropriate handler based on rotation policy
    if rotation_policy == FileRotationPolicy.SIZE:
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
    else:
        # Time-based rotation
        when_map = {
            FileRotationPolicy.DAILY: 'midnight',
            FileRotationPolicy.WEEKLY: 'W0',  # Monday
            FileRotationPolicy.MONTHLY: 'M'
        }
        
        file_handler = TimedRotatingFileHandler(
            file_path,
            when=when_map.get(rotation_policy, 'midnight'),
            backupCount=backup_count
        )
    
    file_handler.setLevel(level)
    
    if format_str == 'json':
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(format_str)
    
    file_handler.setFormatter(formatter)
    _root_logger.addHandler(file_handler)
    
    # Store in handlers dictionary
    handler_key = f'file_{file_name}'
    _handlers[handler_key] = file_handler
    
    return handler_key


def add_stream_handler(
    stream=sys.stdout,
    level: Union[LogLevel, str, int] = LogLevel.INFO,
    format_style: Union[LogFormat, str] = LogFormat.STANDARD
) -> str:
    """
    Add a stream handler to the root logger.
    
    Args:
        stream: Stream to write to (default: sys.stdout)
        level: Log level for this handler
        format_style: Format style for log messages
        
    Returns:
        Handler identifier for later reference
    """
    # Convert level if needed
    if isinstance(level, LogLevel):
        level = level.value
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Convert format if needed
    if isinstance(format_style, LogFormat):
        format_str = format_style.value
    else:
        format_str = format_style
    
    # Create handler
    stream_handler = logging.StreamHandler(stream)
    stream_handler.setLevel(level)
    
    if format_str == 'json':
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(format_str)
    
    stream_handler.setFormatter(formatter)
    _root_logger.addHandler(stream_handler)
    
    # Store in handlers dictionary
    handler_id = f'stream_{id(stream_handler)}'
    _handlers[handler_id] = stream_handler
    
    return handler_id


def remove_handler(handler_id: str) -> bool:
    """
    Remove a handler by its ID.
    
    Args:
        handler_id: Handler identifier
        
    Returns:
        True if handler was removed, False otherwise
    """
    if handler_id in _handlers:
        handler = _handlers.pop(handler_id)
        _root_logger.removeHandler(handler)
        return True
    return False


def set_level(
    level: Union[LogLevel, str, int],
    logger_name: Optional[str] = None,
    handler_id: Optional[str] = None
) -> None:
    """
    Set log level for a logger or specific handler.
    
    Args:
        level: New log level
        logger_name: Name of logger to update (None for root logger)
        handler_id: Handler identifier to update (None for all handlers)
    """
    # Convert level if needed
    if isinstance(level, LogLevel):
        level = level.value
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    if handler_id:
        # Update specific handler
        if handler_id in _handlers:
            _handlers[handler_id].setLevel(level)
    else:
        # Update logger
        logger = logging.getLogger(logger_name) if logger_name else _root_logger
        logger.setLevel(level)


class JsonFormatter(logging.Formatter):
    """
    Log formatter that outputs JSON strings.
    """
    
    def format(self, record):
        """
        Format the log record as a JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string representation of the log record
        """
        log_data = {
            'time': self.formatTime(record),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
            }:
                log_data[key] = value
        
        return json.dumps(log_data) 