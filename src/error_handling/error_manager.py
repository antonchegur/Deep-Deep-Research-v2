"""
Error Management System

This module provides tools for error tracking, management, and recovery strategies.
"""

import logging
import time
import json
import os
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set, Union, Tuple
from threading import Lock
from functools import wraps
from datetime import datetime

from .error_types import ResearchError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class ErrorManager:
    """
    Central error management system that coordinates error handling across the application.
    
    This class provides:
    - Error recording and tracking
    - Centralized error logging
    - Notification for critical errors
    - Recovery strategy coordination
    """
    
    def __init__(self):
        """Initialize the error manager."""
        self._initialized = False
        self.tracker = ErrorTracker()
        self.fallback_manager = FallbackManager()
        self._notification_callbacks = []
        self._recovery_strategies = {}
    
    def initialize(self, enable_file_logging: bool = True, log_dir: str = "logs"):
        """
        Initialize the error manager with configuration.
        
        Args:
            enable_file_logging: Whether to log errors to file
            log_dir: Directory for error log files
        """
        if self._initialized:
            return
        
        if enable_file_logging:
            os.makedirs(log_dir, exist_ok=True)
            error_log_path = os.path.join(log_dir, "errors.log")
            
            # Set up file handler for error logs
            file_handler = logging.FileHandler(error_log_path)
            file_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add the handler to the root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
        
        # Register default recovery strategies
        self._register_default_recovery_strategies()
        
        self._initialized = True
        logger.info("Error manager initialized")
    
    def handle_error(self, error: Union[ResearchError, Exception], component: Optional[str] = None) -> bool:
        """
        Handle an error through the error management system.
        
        Args:
            error: The error to handle
            component: Optional component name where the error occurred
            
        Returns:
            True if the error was handled, False otherwise
        """
        # Convert standard exceptions to ResearchError if needed
        if not isinstance(error, ResearchError):
            from .error_types import classify_exception
            error = classify_exception(error, component)
        
        # Record the error
        self.tracker.record_error(error)
        
        # Log the error
        self._log_error(error)
        
        # Send notifications for high-severity errors
        if error.error_severity in (ErrorSeverity.CRITICAL, ErrorSeverity.HIGH):
            self._send_notifications(error)
        
        # Try to recover from the error
        return self._attempt_recovery(error)
    
    def register_notification_callback(self, callback: Callable[[ResearchError], None]) -> None:
        """
        Register a callback for error notifications.
        
        Args:
            callback: Function to call when a notification-worthy error occurs
        """
        self._notification_callbacks.append(callback)
    
    def register_recovery_strategy(self, error_category: ErrorCategory, 
                                 strategy: Callable[[ResearchError], bool]) -> None:
        """
        Register a recovery strategy for a specific error category.
        
        Args:
            error_category: Category of errors this strategy handles
            strategy: Function that implements the recovery strategy
        """
        if error_category not in self._recovery_strategies:
            self._recovery_strategies[error_category] = []
        
        self._recovery_strategies[error_category].append(strategy)
    
    def _log_error(self, error: ResearchError) -> None:
        """Log an error with appropriate detail level."""
        error_dict = error.to_dict()
        error_json = json.dumps(error_dict)
        
        if error.error_severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error.message} - {error_json}", exc_info=error.original_exception)
        elif error.error_severity == ErrorSeverity.HIGH:
            logger.error(f"ERROR: {error.message} - {error_json}", exc_info=error.original_exception)
        elif error.error_severity == ErrorSeverity.MEDIUM:
            logger.warning(f"WARNING: {error.message} - {error_json}")
        else:  # LOW
            logger.info(f"MINOR ISSUE: {error.message} - {error_json}")
    
    def _send_notifications(self, error: ResearchError) -> None:
        """Send notifications for critical/high-severity errors."""
        for callback in self._notification_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
    
    def _attempt_recovery(self, error: ResearchError) -> bool:
        """
        Attempt to recover from an error.
        
        Args:
            error: The error to recover from
            
        Returns:
            True if recovery was successful, False otherwise
        """
        # First try category-specific strategies
        if error.error_category in self._recovery_strategies:
            for strategy in self._recovery_strategies[error.error_category]:
                try:
                    if strategy(error):
                        return True
                except Exception as e:
                    logger.error(f"Error in recovery strategy: {e}")
        
        # Then try fallback strategies from the fallback manager
        return self.fallback_manager.handle_error(error)
    
    def _register_default_recovery_strategies(self) -> None:
        """Register default recovery strategies for common error categories."""
        # Retry strategy for connection errors
        def retry_connection_errors(error: ResearchError) -> bool:
            if not error.is_retryable:
                return False
            
            # Log that we're retrying
            logger.info(f"Retry recovery strategy: waiting to retry after connection error")
            
            # In a real implementation, we might implement the retry here
            # or signal to the caller that a retry is advisable
            return False  # Return False since we're not actually handling it here
        
        # Rate limit handling strategy
        def handle_rate_limits(error: ResearchError) -> bool:
            if error.retry_after:
                logger.info(f"Rate limit recovery: waiting for {error.retry_after} seconds")
                # In production code, we might actually wait or signal the caller
                return False  # We're not actually handling it here
            return False
        
        # Register these strategies
        self.register_recovery_strategy(ErrorCategory.CONNECTION, retry_connection_errors)
        self.register_recovery_strategy(ErrorCategory.RATE_LIMIT, handle_rate_limits)


class ErrorTracker:
    """
    Tracks errors across the application for monitoring and analysis.
    """
    
    def __init__(self, max_history: int = 100):
        """
        Initialize the error tracker.
        
        Args:
            max_history: Maximum number of recent errors to store
        """
        self.max_history = max_history
        self.recent_errors = []
        self.error_counts = {category: 0 for category in ErrorCategory}
        self.error_counts_by_component = {}
        self.severity_counts = {severity: 0 for severity in ErrorSeverity}
        self.first_occurrence = {}
        self.last_occurrence = {}
        self._lock = Lock()  # Thread safety
    
    def record_error(self, error: ResearchError) -> None:
        """
        Record an error in the tracking system.
        
        Args:
            error: The error to record
        """
        with self._lock:
            # Add to recent errors list, maintaining max size
            self.recent_errors.append(error.to_dict())
            if len(self.recent_errors) > self.max_history:
                self.recent_errors.pop(0)
            
            # Update category counts
            self.error_counts[error.error_category] = self.error_counts.get(error.error_category, 0) + 1
            
            # Update severity counts
            self.severity_counts[error.error_severity] = self.severity_counts.get(error.error_severity, 0) + 1
            
            # Update component counts if component is specified
            if error.component:
                if error.component not in self.error_counts_by_component:
                    self.error_counts_by_component[error.component] = {}
                
                category_key = error.error_category.value
                self.error_counts_by_component[error.component][category_key] = \
                    self.error_counts_by_component[error.component].get(category_key, 0) + 1
            
            # Update first/last occurrence
            error_key = (error.error_category.value, error.message)
            current_time = time.time()
            
            if error_key not in self.first_occurrence:
                self.first_occurrence[error_key] = current_time
            
            self.last_occurrence[error_key] = current_time
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recorded errors.
        
        Returns:
            Dictionary with error statistics
        """
        with self._lock:
            # Convert Enum keys to strings for JSON serialization
            category_counts = {cat.value: count for cat, count in self.error_counts.items()}
            severity_counts = {sev.value: count for sev, count in self.severity_counts.items()}
            
            # Calculate total errors
            total_errors = sum(category_counts.values())
            
            # Format timestamps
            first_occurrence_formatted = {}
            last_occurrence_formatted = {}
            
            for key, timestamp in self.first_occurrence.items():
                first_occurrence_formatted[str(key)] = datetime.fromtimestamp(timestamp).isoformat()
            
            for key, timestamp in self.last_occurrence.items():
                last_occurrence_formatted[str(key)] = datetime.fromtimestamp(timestamp).isoformat()
            
            return {
                "total_errors": total_errors,
                "by_category": category_counts,
                "by_severity": severity_counts,
                "by_component": self.error_counts_by_component,
                "first_occurrence": first_occurrence_formatted,
                "last_occurrence": last_occurrence_formatted,
                "recent_errors": self.recent_errors
            }
    
    def clear(self) -> None:
        """Reset all error tracking data."""
        with self._lock:
            self.recent_errors = []
            self.error_counts = {category: 0 for category in ErrorCategory}
            self.error_counts_by_component = {}
            self.severity_counts = {severity: 0 for severity in ErrorSeverity}
            self.first_occurrence = {}
            self.last_occurrence = {}


class FallbackManager:
    """
    Manages fallback strategies for handling errors, such as using alternative models.
    """
    
    def __init__(self):
        """Initialize the fallback manager."""
        self.fallback_models = []
        self.fallback_handlers = {cat: [] for cat in ErrorCategory}
    
    def register_fallback_model(self, model_id: str, priority: int = 0) -> None:
        """
        Register a fallback model to use when the primary model fails.
        
        Args:
            model_id: Identifier for the model
            priority: Priority level (higher numbers = higher priority)
        """
        self.fallback_models.append((model_id, priority))
        self.fallback_models.sort(key=lambda x: x[1], reverse=True)
    
    def register_fallback_handler(self, error_category: ErrorCategory, 
                                handler: Callable[[ResearchError], bool]) -> None:
        """
        Register a fallback handler for a specific error category.
        
        Args:
            error_category: Category of errors this handler addresses
            handler: Function that handles the error
        """
        self.fallback_handlers[error_category].append(handler)
    
    def get_fallback_models(self) -> List[str]:
        """
        Get the list of fallback models in priority order.
        
        Returns:
            List of model IDs
        """
        return [model_id for model_id, _ in self.fallback_models]
    
    def handle_error(self, error: ResearchError) -> bool:
        """
        Handle an error through registered fallback handlers.
        
        Args:
            error: The error to handle
            
        Returns:
            True if the error was handled, False otherwise
        """
        # Try specific category handlers first
        if error.error_category in self.fallback_handlers:
            for handler in self.fallback_handlers[error.error_category]:
                try:
                    if handler(error):
                        return True
                except Exception as e:
                    logger.error(f"Error in fallback handler: {e}")
        
        # No handler succeeded
        return False


# Create singleton instances
error_manager = ErrorManager()
error_tracker = ErrorTracker()
fallback_manager = FallbackManager()


def handle_errors(component: Optional[str] = None):
    """
    Decorator for handling errors in functions.
    
    Args:
        component: Name of the component for error tracking
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_manager.handle_error(e, component)
                # Re-raise to let caller decide how to proceed
                raise
        return wrapper
    return decorator


def async_handle_errors(component: Optional[str] = None):
    """
    Decorator for handling errors in async functions.
    
    Args:
        component: Name of the component for error tracking
        
    Returns:
        Decorated async function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_manager.handle_error(e, component)
                # Re-raise to let caller decide how to proceed
                raise
        return wrapper
    return decorator 