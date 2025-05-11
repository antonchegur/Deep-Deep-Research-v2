#!/usr/bin/env python3
"""
Error Handling and Logging System Demo

This script demonstrates the comprehensive error handling and logging capabilities
of the Deep Deep Research v2 application.
"""

import os
import sys
import time
import asyncio
import random
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import error handling and logging modules
from src.error_handling import (
    configure_logging, LogLevel, LogFormat, FileRotationPolicy,
    ErrorCategory, ErrorSeverity, ResearchError,
    AuthenticationError, RateLimitError, TokenLimitError, 
    TimeoutError, ConnectionError, ServerError,
    InputError, OutputError, DatabaseError,
    error_manager, error_tracker, fallback_manager,
    handle_errors, async_handle_errors,
    error_context, try_except, async_try_except,
    try_result, async_try_result, ErrorResult, 
    get_exception_details
)
from src.error_handling.logging_config import get_logger


# Configure logging for this demo
configure_logging(
    level=LogLevel.DEBUG,
    format_style=LogFormat.DETAILED,
    log_to_console=True,
    log_to_file=True,
    log_dir="logs",
    file_name="error_demo.log",
    rotation_policy=FileRotationPolicy.SIZE,
    max_file_size_mb=10,
    backup_count=3
)

# Get a logger for this module
logger = get_logger(__name__)


# Simulation functions that generate different types of errors
class ErrorSimulator:
    """Class to simulate various error scenarios for demonstration purposes."""
    
    @staticmethod
    def simulate_authentication_error() -> None:
        """Simulate an authentication error."""
        logger.info("Simulating authentication error...")
        raise AuthenticationError("Invalid API key provided")
    
    @staticmethod
    def simulate_rate_limit_error() -> None:
        """Simulate a rate limit error."""
        logger.info("Simulating rate limit error...")
        raise RateLimitError("Rate limit exceeded", retry_after=30)
    
    @staticmethod
    def simulate_token_limit_error() -> None:
        """Simulate a token limit error."""
        logger.info("Simulating token limit error...")
        raise TokenLimitError("Input exceeds model's token limit")
    
    @staticmethod
    def simulate_timeout_error() -> None:
        """Simulate a timeout error."""
        logger.info("Simulating timeout error...")
        raise TimeoutError("Request timed out after 60 seconds")
    
    @staticmethod
    def simulate_connection_error() -> None:
        """Simulate a connection error."""
        logger.info("Simulating connection error...")
        raise ConnectionError("Failed to connect to API endpoint")
    
    @staticmethod
    def simulate_server_error() -> None:
        """Simulate a server error."""
        logger.info("Simulating server error...")
        raise ServerError("Internal server error", status_code=500)
    
    @staticmethod
    def simulate_input_error() -> None:
        """Simulate an input validation error."""
        logger.info("Simulating input error...")
        raise InputError("Invalid search query format")
    
    @staticmethod
    def simulate_output_error() -> None:
        """Simulate an output processing error."""
        logger.info("Simulating output error...")
        raise OutputError("Failed to parse API response")
    
    @staticmethod
    def simulate_database_error() -> None:
        """Simulate a database error."""
        logger.info("Simulating database error...")
        raise DatabaseError("Failed to connect to database")
    
    @staticmethod
    def simulate_standard_exception() -> None:
        """Simulate a standard Python exception."""
        logger.info("Simulating standard Python exception...")
        raise ValueError("This is a standard ValueError")
    
    @staticmethod
    async def simulate_async_error() -> None:
        """Simulate an asynchronous error."""
        logger.info("Simulating asynchronous error...")
        await asyncio.sleep(0.1)  # Simulate some async operation
        raise ConnectionError("Async operation failed")


# Demo 1: Basic error handling with decorators
@handle_errors(component="demo_basic")
def demo_basic_error_handling() -> None:
    """Demonstrate basic error handling with decorators."""
    logger.info("=== Demo 1: Basic Error Handling with Decorators ===")
    
    # Pick a random error to simulate
    error_methods = [
        ErrorSimulator.simulate_authentication_error,
        ErrorSimulator.simulate_rate_limit_error,
        ErrorSimulator.simulate_token_limit_error,
        ErrorSimulator.simulate_standard_exception
    ]
    
    try:
        # Choose a random error type
        random.choice(error_methods)()
    except Exception as e:
        logger.info(f"Caught exception in demo_basic_error_handling: {e}")
        # The decorator will handle logging and tracking


# Demo 2: Context manager for error handling
def demo_context_manager() -> None:
    """Demonstrate error handling with context managers."""
    logger.info("\n=== Demo 2: Error Handling with Context Managers ===")
    
    # First example: re-raise exceptions after handling
    try:
        with error_context(component="demo_context"):
            logger.info("Executing code that might raise an exception (will re-raise)...")
            ErrorSimulator.simulate_server_error()
    except Exception as e:
        logger.info(f"Exception was re-raised and caught: {e}")
    
    # Second example: suppress exceptions
    logger.info("\nNow with exception suppression:")
    with error_context(component="demo_context", suppress_exceptions=True):
        logger.info("Executing code that might raise an exception (suppressed)...")
        try:
            ErrorSimulator.simulate_connection_error()
        except Exception:
            pass  # Exception will be suppressed by the context manager
    
    logger.info("Continued execution after suppressed exception")


# Demo 3: Function result handling with ErrorResult
def demo_error_result() -> None:
    """Demonstrate error result pattern."""
    logger.info("\n=== Demo 3: Error Result Pattern ===")
    
    # Function that returns an ErrorResult
    def process_data(data: Dict[str, Any]) -> ErrorResult:
        try:
            logger.info(f"Processing data: {data}")
            
            if "id" not in data:
                raise InputError("Missing 'id' field in data")
            
            if not isinstance(data.get("value"), (int, float)):
                raise InputError("'value' must be a number")
            
            # Process the data
            result = {
                "id": data["id"],
                "processed_value": data["value"] * 2,
                "timestamp": time.time()
            }
            
            return ErrorResult.success(result)
        except Exception as e:
            error_manager.handle_error(e, component="data_processor")
            return ErrorResult.failure(e)
    
    # Test with valid data
    logger.info("Processing valid data:")
    valid_result = process_data({"id": "test-123", "value": 42})
    
    if not valid_result.has_error:
        logger.info(f"Success! Processed result: {valid_result.value}")
    else:
        logger.error(f"Unexpected error: {valid_result.error}")
    
    # Test with invalid data
    logger.info("\nProcessing invalid data:")
    invalid_result = process_data({"value": "not-a-number"})
    
    if invalid_result.has_error:
        logger.info(f"Expected error occurred: {invalid_result.error}")
        # Use unwrap_or to provide a default value
        default_value = {"id": "default", "processed_value": 0, "timestamp": time.time()}
        result = invalid_result.unwrap_or(default_value)
        logger.info(f"Using default value instead: {result}")
    else:
        logger.error("Expected an error but got success!")


# Demo A4: Asynchronous error handling
async def demo_async_error_handling() -> None:
    """Demonstrate asynchronous error handling."""
    logger.info("\n=== Demo 4: Asynchronous Error Handling ===")
    
    @async_handle_errors(component="async_demo")
    async def fetch_data() -> Dict[str, Any]:
        """Simulated async data fetching function that might fail."""
        await asyncio.sleep(0.5)  # Simulate network delay
        
        # Randomly succeed or fail
        if random.random() < 0.5:
            await ErrorSimulator.simulate_async_error()
        
        return {"data": "success", "timestamp": time.time()}
    
    # Try the async function with the decorator
    try:
        logger.info("Fetching data asynchronously...")
        result = await fetch_data()
        logger.info(f"Fetch succeeded: {result}")
    except Exception as e:
        logger.info(f"Fetch failed as expected: {e}")
    
    # Try with the async_try_result helper
    logger.info("\nFetching again with async_try_result...")
    result = await async_try_result(fetch_data)
    
    if result.has_error:
        logger.info(f"Fetch failed (captured in ErrorResult): {result.error}")
    else:
        logger.info(f"Fetch succeeded: {result.value}")


# Demo 5: Error recovery strategies
def demo_recovery_strategies() -> None:
    """Demonstrate error recovery strategies."""
    logger.info("\n=== Demo 5: Error Recovery Strategies ===")
    
    # Register a custom fallback handler for rate limit errors
    def handle_rate_limit(error: ResearchError) -> bool:
        if not isinstance(error, RateLimitError):
            return False
        
        logger.info(f"Custom rate limit handler: waiting for {error.retry_after} seconds")
        # In a real implementation, we would probably wait or schedule a retry
        # For demo purposes, we'll just pretend we handled it
        return True
    
    # Register fallback models
    fallback_manager.register_fallback_model("gpt-3.5-turbo", priority=1)
    
    # Register the rate limit handler
    fallback_manager.register_fallback_handler(ErrorCategory.RATE_LIMIT, handle_rate_limit)
    
    # Test the handler with a rate limit error
    logger.info("Testing rate limit recovery:")
    try:
        ErrorSimulator.simulate_rate_limit_error()
    except RateLimitError as e:
        handled = error_manager.handle_error(e)
        logger.info(f"Error was handled by recovery strategy: {handled}")


# Demo 6: Error tracking and statistics
def demo_error_tracking() -> None:
    """Demonstrate error tracking and statistics."""
    logger.info("\n=== Demo 6: Error Tracking and Statistics ===")
    
    # Generate a variety of errors for tracking
    errors_to_simulate = [
        ErrorSimulator.simulate_authentication_error,
        ErrorSimulator.simulate_rate_limit_error,
        ErrorSimulator.simulate_token_limit_error,
        ErrorSimulator.simulate_timeout_error,
        ErrorSimulator.simulate_connection_error,
        ErrorSimulator.simulate_server_error,
        ErrorSimulator.simulate_input_error,
        ErrorSimulator.simulate_output_error,
        ErrorSimulator.simulate_database_error
    ]
    
    logger.info("Generating various errors for tracking...")
    
    # Generate each error type and handle it
    for error_func in errors_to_simulate:
        try:
            error_func()
        except ResearchError as e:
            error_manager.handle_error(e)
    
    # Get error statistics
    stats = error_tracker.get_error_summary()
    
    logger.info("\nError Tracking Statistics:")
    logger.info(f"Total errors tracked: {stats['total_errors']}")
    logger.info(f"Errors by category: {stats['by_category']}")
    logger.info(f"Errors by severity: {stats['by_severity']}")
    
    # Most recent errors
    logger.info("\nMost recent errors:")
    for i, error in enumerate(stats['recent_errors'][-3:]):
        logger.info(f"{i+1}. {error['category']}: {error['message']}")


async def main() -> None:
    """Run all demos."""
    # Set up logging banner
    logger.info("=" * 80)
    logger.info("DEEP DEEP RESEARCH v2 - ERROR HANDLING AND LOGGING SYSTEM DEMO")
    logger.info("=" * 80)
    
    try:
        # Run the demos
        demo_basic_error_handling()
        demo_context_manager()
        demo_error_result()
        await demo_async_error_handling()
        demo_recovery_strategies()
        demo_error_tracking()
        
        logger.info("\n" + "=" * 80)
        logger.info("Demo completed successfully!")
        logger.info("=" * 80)
    except Exception as e:
        logger.critical(f"Unhandled exception in demo: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 