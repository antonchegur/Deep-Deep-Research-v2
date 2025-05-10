"""
Comprehensive error handling for GPT-4 Turbo integration.

This module provides error classification, fallback mechanisms, and utilities
for handling various types of errors that may occur during API calls and
model interactions.
"""

import logging
import time
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for different types of errors."""
    CRITICAL = "critical"  # Fatal, non-recoverable errors
    HIGH = "high"          # Serious errors, affecting core functionality
    MEDIUM = "medium"      # Non-critical errors, but should be addressed
    LOW = "low"            # Minor issues, operation can continue


class ErrorCategory(Enum):
    """Categories of errors for classification."""
    AUTHENTICATION = "authentication"  # API key issues, unauthorized
    RATE_LIMIT = "rate_limit"          # Rate limiting, usage quotas
    MODEL = "model"                    # Model-specific errors (unavailable, deprecated)
    CONTENT_FILTER = "content_filter"  # Content policy violations
    TOKEN_LIMIT = "token_limit"        # Token limit exceeded
    TIMEOUT = "timeout"                # Request timeout
    CONNECTION = "connection"          # Network connectivity issues
    SERVER = "server"                  # OpenAI server errors
    INPUT = "input"                    # Invalid input parameters
    OUTPUT = "output"                  # Output parsing or validation failures
    CONTEXT = "context"                # Context management issues
    UNKNOWN = "unknown"                # Unclassified errors


class ResearchError(Exception):
    """Base exception class for research-related errors."""
    
    def __init__(self, 
                message: str, 
                error_category: ErrorCategory = ErrorCategory.UNKNOWN, 
                error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                status_code: Optional[int] = None, 
                response_text: Optional[str] = None,
                is_retryable: bool = True,
                retry_after: Optional[int] = None,
                original_exception: Optional[Exception] = None):
        """
        Initialize a ResearchError.
        
        Args:
            message: Human-readable error message
            error_category: Category of the error
            error_severity: Severity level of the error
            status_code: HTTP status code (if applicable)
            response_text: Raw response text from API (if applicable)
            is_retryable: Whether the error can be retried
            retry_after: Recommended seconds to wait before retry (if applicable)
            original_exception: Original exception that was caught
        """
        self.message = message
        self.error_category = error_category
        self.error_severity = error_severity
        self.status_code = status_code
        self.response_text = response_text
        self.is_retryable = is_retryable
        self.retry_after = retry_after
        self.original_exception = original_exception
        
        # This helps with logging and debugging
        self.timestamp = time.time()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging and analysis."""
        return {
            "message": self.message,
            "category": self.error_category.value,
            "severity": self.error_severity.value,
            "status_code": self.status_code,
            "is_retryable": self.is_retryable,
            "retry_after": self.retry_after,
            "timestamp": self.timestamp,
            "original_exception_type": type(self.original_exception).__name__ if self.original_exception else None
        }
    
    def get_user_message(self) -> str:
        """Get a user-friendly error message."""
        category_msg = {
            ErrorCategory.AUTHENTICATION: "Authentication error. Please check your API key.",
            ErrorCategory.RATE_LIMIT: "Rate limit exceeded. Please try again later.",
            ErrorCategory.MODEL: "Model error. The requested AI model may be unavailable.",
            ErrorCategory.CONTENT_FILTER: "Content policy violation detected in the request or response.",
            ErrorCategory.TOKEN_LIMIT: "Token limit exceeded. Please reduce the input size or use a model with higher limits.",
            ErrorCategory.TIMEOUT: "Request timed out. Please try again later.",
            ErrorCategory.CONNECTION: "Connection error. Please check your network connection.",
            ErrorCategory.SERVER: "Server error. The service is experiencing technical difficulties.",
            ErrorCategory.INPUT: "Invalid input parameters provided.",
            ErrorCategory.OUTPUT: "Error processing the model's response.",
            ErrorCategory.CONTEXT: "Context management error. The input may be too large or complex.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred."
        }
        
        return f"{category_msg[self.error_category]} {self.message}"


# Specific error types for different categories
class AuthenticationError(ResearchError):
    """Errors related to authentication failures."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            error_category=ErrorCategory.AUTHENTICATION,
            error_severity=ErrorSeverity.HIGH,
            is_retryable=False,
            **kwargs
        )


class RateLimitError(ResearchError):
    """Errors related to rate limiting and usage quotas."""
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.RATE_LIMIT,
            error_severity=ErrorSeverity.MEDIUM,
            retry_after=retry_after,
            **kwargs
        )


class ModelError(ResearchError):
    """Errors related to model availability or compatibility."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.MODEL,
            error_severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ContentFilterError(ResearchError):
    """Errors related to content policy violations."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.CONTENT_FILTER,
            error_severity=ErrorSeverity.HIGH,
            is_retryable=False,
            **kwargs
        )


class TokenLimitError(ResearchError):
    """Errors related to token limits being exceeded."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.TOKEN_LIMIT,
            error_severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class TimeoutError(ResearchError):
    """Errors related to request timeouts."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.TIMEOUT,
            error_severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ConnectionError(ResearchError):
    """Errors related to network connectivity issues."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.CONNECTION,
            error_severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ServerError(ResearchError):
    """Errors related to OpenAI server issues."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.SERVER,
            error_severity=ErrorSeverity.HIGH,
            **kwargs
        )


class InputError(ResearchError):
    """Errors related to invalid input parameters."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.INPUT,
            error_severity=ErrorSeverity.MEDIUM,
            is_retryable=False,
            **kwargs
        )


class OutputError(ResearchError):
    """Errors related to output parsing or validation failures."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.OUTPUT,
            error_severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ContextError(ResearchError):
    """Errors related to context management issues."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.CONTEXT,
            error_severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


def classify_openai_error(status_code: Optional[int], error_message: str, response_text: Optional[str] = None) -> ResearchError:
    """
    Classify OpenAI API errors based on status code and error message.
    
    Args:
        status_code: HTTP status code from the API response
        error_message: Error message from the exception or API
        response_text: Full response text if available
        
    Returns:
        An appropriate ResearchError subclass
    """
    # Authentication errors
    if status_code in (401, 403):
        return AuthenticationError(
            "Authentication failed. Check your API key and permissions.",
            status_code=status_code,
            response_text=response_text
        )
    
    # Rate limiting
    if status_code == 429:
        retry_after = None
        if response_text:
            # Try to extract retry-after information
            try:
                import json
                data = json.loads(response_text)
                if "error" in data and "retry_after" in data["error"]:
                    retry_after = int(data["error"]["retry_after"])
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        return RateLimitError(
            "Rate limit exceeded. Try again later or reduce request frequency.",
            status_code=status_code,
            response_text=response_text,
            retry_after=retry_after
        )
    
    # Invalid input
    if status_code == 400:
        # Check for token limit issues
        if "maximum context length" in error_message.lower() or "tokens" in error_message.lower():
            return TokenLimitError(
                "Input exceeds maximum token limit for the model.",
                status_code=status_code,
                response_text=response_text
            )
        
        # Content filter issues
        if "content filter" in error_message.lower() or "policy" in error_message.lower():
            return ContentFilterError(
                "Content violates usage policies.",
                status_code=status_code,
                response_text=response_text
            )
        
        # Model errors
        if "model" in error_message.lower() and ("not found" in error_message.lower() or "does not exist" in error_message.lower()):
            return ModelError(
                "The specified model is invalid or unavailable.",
                status_code=status_code,
                response_text=response_text
            )
        
        # Generic input error
        return InputError(
            "Invalid request parameters.",
            status_code=status_code,
            response_text=response_text
        )
    
    # Server errors
    if status_code and status_code >= 500:
        return ServerError(
            "OpenAI server error. The service might be experiencing issues.",
            status_code=status_code,
            response_text=response_text
        )
    
    # Fallback: unknown error
    return ResearchError(
        error_message,
        status_code=status_code,
        response_text=response_text
    )


def classify_network_error(error: Exception) -> ResearchError:
    """
    Classify network-related errors.
    
    Args:
        error: The original exception
        
    Returns:
        An appropriate ResearchError subclass
    """
    error_text = str(error)
    
    # Timeout errors
    if "timeout" in error_text.lower():
        return TimeoutError(
            "Request timed out. The server took too long to respond.",
            original_exception=error
        )
    
    # Connection errors
    connection_patterns = ["connection", "network", "unreachable", "dns", "ssl", "certificate"]
    if any(pattern in error_text.lower() for pattern in connection_patterns):
        return ConnectionError(
            "Network connection error. Check your internet connection.",
            original_exception=error
        )
    
    # Default to generic connection error
    return ConnectionError(
        "Communication error occurred while contacting the API service.",
        original_exception=error
    )


class ErrorTracker:
    """Tracks and analyzes errors for diagnostics and reporting."""
    
    def __init__(self, max_history: int = 100):
        """
        Initialize error tracker.
        
        Args:
            max_history: Maximum number of errors to retain in history
        """
        self.errors: List[ResearchError] = []
        self.max_history = max_history
        self.error_counts: Dict[ErrorCategory, int] = {cat: 0 for cat in ErrorCategory}
    
    def record_error(self, error: ResearchError):
        """
        Record an error in the tracker.
        
        Args:
            error: The error to record
        """
        # Add to history
        self.errors.append(error)
        
        # Trim history if needed
        if len(self.errors) > self.max_history:
            self.errors = self.errors[-self.max_history:]
        
        # Update counts
        self.error_counts[error.error_category] = self.error_counts.get(error.error_category, 0) + 1
        
        # Log the error
        logger.error(f"{error.error_category.value.upper()} ({error.error_severity.value}): {error.message}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recorded errors.
        
        Returns:
            Dictionary with error statistics
        """
        if not self.errors:
            return {"total_errors": 0, "categories": {}}
        
        # Calculate statistics
        total = len(self.errors)
        by_category = {cat.value: count for cat, count in self.error_counts.items() if count > 0}
        by_severity = {}
        
        for severity in ErrorSeverity:
            count = sum(1 for e in self.errors if e.error_severity == severity)
            if count > 0:
                by_severity[severity.value] = count
        
        # Get most recent errors
        recent = [e.to_dict() for e in self.errors[-5:]]
        
        return {
            "total_errors": total,
            "categories": by_category,
            "severities": by_severity,
            "recent_errors": recent
        }
    
    def clear(self):
        """Clear all error history."""
        self.errors = []
        self.error_counts = {cat: 0 for cat in ErrorCategory}


class FallbackManager:
    """Manages fallback strategies for handling errors."""
    
    def __init__(self):
        """Initialize the fallback manager."""
        self.fallback_models = []
        self.fallback_handlers: Dict[ErrorCategory, List[Callable]] = {cat: [] for cat in ErrorCategory}
    
    def register_fallback_model(self, model_id: str, priority: int = 0):
        """
        Register a fallback model to try if the primary model fails.
        
        Args:
            model_id: ID of the model to use as fallback
            priority: Priority (higher numbers = higher priority)
        """
        self.fallback_models.append((model_id, priority))
        self.fallback_models.sort(key=lambda x: -x[1])  # Sort by priority (descending)
    
    def register_fallback_handler(self, error_category: ErrorCategory, handler: Callable):
        """
        Register a fallback handler function for a specific error category.
        
        Args:
            error_category: The category of errors this handler manages
            handler: Function to call when this type of error occurs
        """
        self.fallback_handlers[error_category].append(handler)
    
    def get_fallback_models(self) -> List[str]:
        """
        Get the list of fallback models in priority order.
        
        Returns:
            List of model IDs
        """
        return [model for model, _ in self.fallback_models]
    
    def handle_error(self, error: ResearchError) -> bool:
        """
        Try to handle an error with registered fallback handlers.
        
        Args:
            error: The error to handle
            
        Returns:
            True if the error was handled, False otherwise
        """
        handlers = self.fallback_handlers.get(error.error_category, [])
        
        for handler in handlers:
            try:
                if handler(error):
                    return True
            except Exception as e:
                logger.error(f"Error in fallback handler: {e}")
        
        return False


# Global instances for module-level access
error_tracker = ErrorTracker()
fallback_manager = FallbackManager() 