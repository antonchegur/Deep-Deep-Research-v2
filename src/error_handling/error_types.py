"""
Error Types and Classification

This module defines the error types, severities, and categories used throughout the application.
It provides a structured approach to error classification and handling.
"""

import time
from enum import Enum
from typing import Any, Dict, Optional


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
    SERVER = "server"                  # Server errors (e.g., OpenAI server issues)
    INPUT = "input"                    # Invalid input parameters
    OUTPUT = "output"                  # Output parsing or validation failures
    CONTEXT = "context"                # Context management issues
    DATABASE = "database"              # Database-related errors
    VALIDATION = "validation"          # Data validation errors
    SYSTEM = "system"                  # General system errors
    MULTILINGUAL = "multilingual"      # Errors specific to multilingual system
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
                original_exception: Optional[Exception] = None,
                component: Optional[str] = None):
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
            component: Component where the error occurred
        """
        self.message = message
        self.error_category = error_category
        self.error_severity = error_severity
        self.status_code = status_code
        self.response_text = response_text
        self.is_retryable = is_retryable
        self.retry_after = retry_after
        self.original_exception = original_exception
        self.component = component
        
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
            "component": self.component,
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
            ErrorCategory.OUTPUT: "Error processing the response data.",
            ErrorCategory.CONTEXT: "Context management error. The input may be too large or complex.",
            ErrorCategory.DATABASE: "Database error. There was a problem accessing the data.",
            ErrorCategory.VALIDATION: "Validation error. The provided data is invalid.",
            ErrorCategory.SYSTEM: "System error. An internal system component has failed.",
            ErrorCategory.MULTILINGUAL: "Multilingual system error. Problem with language processing.",
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
    """Errors related to remote server issues."""
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


class DatabaseError(ResearchError):
    """Errors related to database operations."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.DATABASE,
            error_severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ValidationError(ResearchError):
    """Errors related to data validation."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.VALIDATION,
            error_severity=ErrorSeverity.MEDIUM,
            is_retryable=False,
            **kwargs
        )


class SystemError(ResearchError):
    """Errors related to general system operations."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.SYSTEM,
            error_severity=ErrorSeverity.HIGH,
            **kwargs
        )


def classify_exception(exception: Exception, component: Optional[str] = None) -> ResearchError:
    """
    Classify a general exception into an appropriate ResearchError type.
    
    Args:
        exception: The exception to classify
        component: Optional component name where the exception occurred
        
    Returns:
        A ResearchError instance with appropriate classification
    """
    # If it's already a ResearchError, just set the component if not already set
    if isinstance(exception, ResearchError):
        if component and not exception.component:
            exception.component = component
        return exception
    
    # Classify by exception type
    error_message = str(exception)
    
    # Connection-related errors
    if any(conn_err in error_message.lower() for conn_err in 
           ["connection", "timeout", "network", "socket", "unreachable"]):
        return ConnectionError(
            f"Connection failed: {error_message}",
            original_exception=exception,
            component=component
        )
    
    # Database-related errors
    if any(db_err in error_message.lower() for db_err in 
           ["database", "sql", "query", "db", "connection pool"]):
        return DatabaseError(
            f"Database operation failed: {error_message}",
            original_exception=exception,
            component=component
        )
    
    # Validation-related errors
    if any(val_err in error_message.lower() for val_err in 
           ["validation", "invalid", "schema", "required field", "value error"]):
        return ValidationError(
            f"Validation failed: {error_message}",
            original_exception=exception,
            component=component
        )
    
    # Other system errors with context
    return SystemError(
        f"System error: {error_message}",
        original_exception=exception,
        component=component
    ) 