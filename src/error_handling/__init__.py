"""
Error Handling and Logging System

This module provides a centralized system for error handling, logging, and monitoring
throughout the Deep Deep Research v2 application.
"""

from .error_types import (
    ErrorSeverity, ErrorCategory, ResearchError,
    AuthenticationError, RateLimitError, ModelError, ContentFilterError, 
    TokenLimitError, TimeoutError, ConnectionError, ServerError,
    InputError, OutputError, ContextError, DatabaseError, ValidationError
)

from .error_manager import (
    ErrorManager, ErrorTracker, FallbackManager, 
    error_manager, error_tracker, fallback_manager
)

from .logging_config import (
    configure_logging, get_logger, LogLevel, LogFormat,
    FileRotationPolicy, add_file_handler, add_stream_handler
)

__all__ = [
    # Error types
    'ErrorSeverity', 'ErrorCategory', 'ResearchError',
    'AuthenticationError', 'RateLimitError', 'ModelError', 'ContentFilterError',
    'TokenLimitError', 'TimeoutError', 'ConnectionError', 'ServerError',
    'InputError', 'OutputError', 'ContextError', 'DatabaseError', 'ValidationError',
    
    # Error management
    'ErrorManager', 'ErrorTracker', 'FallbackManager',
    'error_manager', 'error_tracker', 'fallback_manager',
    
    # Logging functionality
    'configure_logging', 'get_logger', 'LogLevel', 'LogFormat',
    'FileRotationPolicy', 'add_file_handler', 'add_stream_handler',
]

# Initialize the error manager and fallback manager as application singletons
error_manager.initialize() 