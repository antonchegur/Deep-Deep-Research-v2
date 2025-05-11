"""
Error Handling Utilities

This module provides common utility functions and context managers for error handling.
"""

import sys
import logging
import traceback
import contextlib
from typing import Any, Callable, Optional, Type, Union, List, Dict, Generator, TypeVar, Generic

from .error_types import ResearchError, ErrorCategory, ErrorSeverity
from .error_manager import error_manager

logger = logging.getLogger(__name__)

T = TypeVar('T')


def try_except(
    func: Callable,
    *args,
    error_handler: Optional[Callable[[Exception], Any]] = None,
    component: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        error_handler: Optional function to handle any exceptions
        component: Optional component name for error tracking
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call or error handler
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Log and track the error
        error_manager.handle_error(e, component)
        
        # If an error handler was provided, call it
        if error_handler:
            return error_handler(e)
        
        # Re-raise the exception
        raise


async def async_try_except(
    func: Callable,
    *args,
    error_handler: Optional[Callable[[Exception], Any]] = None,
    component: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Execute an async function with error handling.
    
    Args:
        func: Async function to execute
        *args: Arguments to pass to the function
        error_handler: Optional function to handle any exceptions
        component: Optional component name for error tracking
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call or error handler
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        # Log and track the error
        error_manager.handle_error(e, component)
        
        # If an error handler was provided, call it
        if error_handler:
            return error_handler(e)
        
        # Re-raise the exception
        raise


@contextlib.contextmanager
def error_context(
    component: Optional[str] = None,
    error_handler: Optional[Callable[[Exception], Any]] = None,
    suppress_exceptions: bool = False,
    exception_types: Optional[List[Type[Exception]]] = None
) -> Generator[None, None, None]:
    """
    Context manager for error handling.
    
    Args:
        component: Optional component name for error tracking
        error_handler: Optional function to handle any exceptions
        suppress_exceptions: Whether to suppress exceptions after handling
        exception_types: List of exception types to handle (None = all exceptions)
        
    Yields:
        None
    """
    try:
        yield
    except Exception as e:
        # Check if this exception type should be handled
        if exception_types and not any(isinstance(e, exc_type) for exc_type in exception_types):
            raise
        
        # Log and track the error
        error_manager.handle_error(e, component)
        
        # If an error handler was provided, call it
        if error_handler:
            error_handler(e)
        
        # Re-raise the exception if not suppressing
        if not suppress_exceptions:
            raise


class ErrorResult(Generic[T]):
    """
    Container for a result or error from a function.
    
    This is similar to Rust's Result type or Go's multiple return values pattern.
    It allows functions to return either a successful result or an error.
    """
    
    def __init__(
        self, 
        value: Optional[T] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize an ErrorResult.
        
        Args:
            value: The result value (None if there was an error)
            error: The error that occurred (None if there was no error)
        """
        self.value = value
        self.error = error
        self.has_error = error is not None
    
    @classmethod
    def success(cls, value: T) -> 'ErrorResult[T]':
        """Create a successful result."""
        return cls(value=value)
    
    @classmethod
    def failure(cls, error: Exception) -> 'ErrorResult[T]':
        """Create a failure result."""
        return cls(error=error)
    
    def unwrap(self) -> T:
        """
        Get the value if successful, otherwise raise the error.
        
        Returns:
            The result value
            
        Raises:
            The original exception if there was an error
        """
        if self.has_error:
            raise self.error
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        """
        Get the value if successful, otherwise return the default.
        
        Args:
            default: Default value to return if there was an error
            
        Returns:
            The result value or the default
        """
        if self.has_error:
            return default
        return self.value
    
    def unwrap_or_else(self, func: Callable[[Exception], T]) -> T:
        """
        Get the value if successful, otherwise call the function with the error.
        
        Args:
            func: Function to call with the error to get a default value
            
        Returns:
            The result value or the result of the function
        """
        if self.has_error:
            return func(self.error)
        return self.value
    
    def map(self, func: Callable[[T], Any]) -> 'ErrorResult':
        """
        Apply a function to the value if successful.
        
        Args:
            func: Function to apply to the value
            
        Returns:
            A new ErrorResult with the function applied to the value
        """
        if self.has_error:
            return ErrorResult.failure(self.error)
        try:
            return ErrorResult.success(func(self.value))
        except Exception as e:
            return ErrorResult.failure(e)
    
    def and_then(self, func: Callable[[T], 'ErrorResult']) -> 'ErrorResult':
        """
        Apply a function that returns an ErrorResult to the value if successful.
        
        Args:
            func: Function to apply to the value
            
        Returns:
            The ErrorResult returned by the function
        """
        if self.has_error:
            return ErrorResult.failure(self.error)
        try:
            return func(self.value)
        except Exception as e:
            return ErrorResult.failure(e)


def try_result(
    func: Callable,
    *args,
    component: Optional[str] = None,
    **kwargs
) -> ErrorResult:
    """
    Execute a function and return an ErrorResult.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        component: Optional component name for error tracking
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        ErrorResult containing either the result or the error
    """
    try:
        result = func(*args, **kwargs)
        return ErrorResult.success(result)
    except Exception as e:
        # Log and track the error
        error_manager.handle_error(e, component)
        
        # Return the error result
        return ErrorResult.failure(e)


async def async_try_result(
    func: Callable,
    *args,
    component: Optional[str] = None,
    **kwargs
) -> ErrorResult:
    """
    Execute an async function and return an ErrorResult.
    
    Args:
        func: Async function to execute
        *args: Arguments to pass to the function
        component: Optional component name for error tracking
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        ErrorResult containing either the result or the error
    """
    try:
        result = await func(*args, **kwargs)
        return ErrorResult.success(result)
    except Exception as e:
        # Log and track the error
        error_manager.handle_error(e, component)
        
        # Return the error result
        return ErrorResult.failure(e)


def get_exception_details(exc: Exception) -> Dict[str, Any]:
    """
    Get detailed information about an exception.
    
    Args:
        exc: The exception to analyze
        
    Returns:
        Dictionary with exception details
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    return {
        'type': type(exc).__name__,
        'message': str(exc),
        'module': type(exc).__module__,
        'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback) if exc_traceback else None,
        'args': getattr(exc, 'args', None),
        'cause': str(exc.__cause__) if exc.__cause__ else None
    } 