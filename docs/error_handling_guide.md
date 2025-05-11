# Error Handling and Logging System Guide

This guide provides detailed information on using the error handling and logging system in Deep Deep Research v2. The system provides a comprehensive framework for consistent error handling, logging, and monitoring throughout the application.

## Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Error Types](#error-types)
- [Logging](#logging)
- [Error Handling Patterns](#error-handling-patterns)
- [Recovery Strategies](#recovery-strategies)
- [Error Tracking and Reporting](#error-tracking-and-reporting)
- [Best Practices](#best-practices)

## Overview

The error handling and logging system provides a centralized approach to managing errors and log messages across the application. Key features include:

- Structured error classification and categorization
- Centralized logging configuration with multiple output formats
- Error tracking and statistics
- Recovery strategies for different error types
- Support for asynchronous operations
- Notification system for critical errors

## Configuration

### Basic Configuration

The error handling and logging system can be configured using various methods:

```python
from src.error_handling import configure_logging, LogLevel, LogFormat, FileRotationPolicy

# Configure with default settings
configure_logging()

# Configure with custom settings
configure_logging(
    level=LogLevel.INFO,
    format_style=LogFormat.STANDARD,
    log_to_console=True,
    log_to_file=True,
    log_dir="logs",
    file_name="app.log",
    rotation_policy=FileRotationPolicy.DAILY,
    max_file_size_mb=10,
    backup_count=5
)
```

### Configuration from Environment Variables

```python
from src.error_handling.config import configure_from_env

# Configure using environment variables with prefix "DDR_"
configure_from_env(
    prefix="DDR_",
    default_log_level=LogLevel.INFO,
    default_log_format=LogFormat.STANDARD,
    default_log_dir="logs",
    enable_file_logging=True
)
```

### Configuration from Dictionary or File

```python
from src.error_handling.config import configure_from_dict, configure_from_file

# From dictionary
config = {
    "logging": {
        "level": "INFO",
        "format": "STANDARD",
        "log_dir": "logs",
        "log_file": "app.log",
        "enable_file_logging": True
    },
    "error_handling": {
        "enable_notifications": True,
        "fallback_models": [
            {"id": "gpt-3.5-turbo", "priority": 1}
        ]
    }
}
configure_from_dict(config)

# From file
configure_from_file("config/logging.json")  # JSON file
configure_from_file("config/logging.yaml")  # YAML file (requires PyYAML)
```

## Error Types

The system defines various error types to cover different categories of errors:

### Error Categories

```python
from src.error_handling import ErrorCategory

# Available categories
ErrorCategory.AUTHENTICATION  # API key issues, unauthorized
ErrorCategory.RATE_LIMIT      # Rate limiting, usage quotas
ErrorCategory.MODEL           # Model-specific errors
ErrorCategory.CONTENT_FILTER  # Content policy violations
ErrorCategory.TOKEN_LIMIT     # Token limit exceeded
ErrorCategory.TIMEOUT         # Request timeout
ErrorCategory.CONNECTION      # Network connectivity issues
ErrorCategory.SERVER          # Server errors
ErrorCategory.INPUT           # Invalid input parameters
ErrorCategory.OUTPUT          # Output parsing or validation failures
ErrorCategory.CONTEXT         # Context management issues
ErrorCategory.DATABASE        # Database-related errors
ErrorCategory.VALIDATION      # Data validation errors
ErrorCategory.SYSTEM          # General system errors
ErrorCategory.UNKNOWN         # Unclassified errors
```

### Error Severity Levels

```python
from src.error_handling import ErrorSeverity

# Available severity levels
ErrorSeverity.CRITICAL  # Fatal, non-recoverable errors
ErrorSeverity.HIGH      # Serious errors, affecting core functionality
ErrorSeverity.MEDIUM    # Non-critical errors, but should be addressed
ErrorSeverity.LOW       # Minor issues, operation can continue
```

### Specific Error Types

The system provides specialized error types for different categories:

```python
from src.error_handling import (
    ResearchError,  # Base error class
    AuthenticationError,
    RateLimitError,
    ModelError,
    ContentFilterError,
    TokenLimitError,
    TimeoutError,
    ConnectionError,
    ServerError,
    InputError,
    OutputError,
    ContextError,
    DatabaseError,
    ValidationError,
    SystemError
)

# Example usage
raise AuthenticationError("Invalid API key")
raise RateLimitError("Rate limit exceeded", retry_after=30)
raise ModelError("Model 'gpt-4' is not available")
```

### Creating Custom Error Types

You can create custom error types by extending the base `ResearchError` class:

```python
from src.error_handling import ResearchError, ErrorCategory, ErrorSeverity

class CustomError(ResearchError):
    def __init__(self, message, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.SYSTEM,  # Choose appropriate category
            error_severity=ErrorSeverity.MEDIUM,  # Choose appropriate severity
            **kwargs
        )
```

## Logging

### Getting a Logger

Always use the `get_logger` function to get a logger instance:

```python
from src.error_handling.logging_config import get_logger

# Get a logger with the module name
logger = get_logger(__name__)

# Use the logger
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Log Formats

The system provides several predefined log formats:

```python
from src.error_handling import LogFormat

LogFormat.SIMPLE    # 'LEVEL - message'
LogFormat.STANDARD  # 'timestamp - name - LEVEL - message'
LogFormat.DETAILED  # 'timestamp - name - LEVEL - path:line - message'
LogFormat.JSON      # JSON format for structured logging
```

### Adding Custom Handlers

You can add custom log handlers for specific needs:

```python
from src.error_handling.logging_config import add_file_handler, add_stream_handler, LogLevel

# Add a file handler for specific log file
error_handler_id = add_file_handler(
    file_name="errors.log",
    level=LogLevel.ERROR
)

# Add a stream handler
stream_handler_id = add_stream_handler(
    level=LogLevel.DEBUG
)

# Remove a handler when no longer needed
from src.error_handling.logging_config import remove_handler
remove_handler(error_handler_id)
```

## Error Handling Patterns

The system provides several patterns for handling errors:

### Using Decorators

```python
from src.error_handling import handle_errors, async_handle_errors

# For synchronous functions
@handle_errors(component="my_component")
def process_data(data):
    # This function will have errors logged and tracked
    # Any exceptions will still be propagated up
    return analyze_data(data)

# For asynchronous functions
@async_handle_errors(component="my_component")
async def fetch_data():
    # Async version of the decorator
    return await api_client.get_data()
```

### Using Context Managers

```python
from src.error_handling import error_context

# Basic usage
try:
    with error_context(component="my_component"):
        # Code that might raise exceptions
        process_data(data)
except Exception as e:
    # Handle the exception
    print(f"Error: {e}")

# Suppressing exceptions
with error_context(component="my_component", suppress_exceptions=True):
    # Exceptions will be logged and tracked, but not raised
    risky_operation()
    
# Handling only specific exception types
with error_context(component="my_component", exception_types=[ValueError, TypeError]):
    # Only ValueError and TypeError will be handled
    validate_input(data)
```

### Using Function Wrappers

```python
from src.error_handling import try_except, async_try_except

# For synchronous functions
result = try_except(
    process_data,
    data,
    error_handler=lambda e: default_value,
    component="my_component"
)

# For asynchronous functions
result = await async_try_except(
    fetch_data,
    error_handler=lambda e: default_value,
    component="my_component"
)
```

### Using Result Types

```python
from src.error_handling import try_result, async_try_result, ErrorResult

# For synchronous functions
result = try_result(process_data, data, component="my_component")

if result.has_error:
    # Handle error case
    print(f"Error: {result.error}")
    fallback_value = default_value
else:
    # Handle success case
    fallback_value = result.value

# Use convenience methods
value = result.unwrap_or(default_value)  # Return value or default
value = result.unwrap_or_else(lambda e: compute_fallback(e))  # Call function to get fallback

# For asynchronous functions
result = await async_try_result(fetch_data, component="my_component")
```

## Recovery Strategies

The system provides mechanisms for implementing error recovery strategies:

### Registering Recovery Strategies

```python
from src.error_handling import error_manager, ErrorCategory

# Register a recovery strategy for a specific error category
def retry_connection_errors(error):
    if not error.is_retryable:
        return False
    
    # Implement retry logic
    print(f"Retrying connection after error: {error.message}")
    # ... retry logic here ...
    return True  # Return True if recovery was successful

# Register the strategy
error_manager.register_recovery_strategy(
    ErrorCategory.CONNECTION, 
    retry_connection_errors
)
```

### Using Fallback Models

```python
from src.error_handling import fallback_manager

# Register fallback models for AI-related operations
fallback_manager.register_fallback_model("gpt-3.5-turbo", priority=1)
fallback_manager.register_fallback_model("gpt-3.5-turbo-16k", priority=2)

# Get the list of fallback models in priority order
models = fallback_manager.get_fallback_models()
```

### Implementing Fallback Handlers

```python
from src.error_handling import fallback_manager, ErrorCategory

# Register a fallback handler for a specific error category
def handle_rate_limit(error):
    if error.retry_after:
        print(f"Rate limit hit. Waiting {error.retry_after} seconds")
        time.sleep(error.retry_after)
        return True  # Indicate that the error was handled
    return False  # Indicate that the error wasn't handled

# Register the handler
fallback_manager.register_fallback_handler(
    ErrorCategory.RATE_LIMIT,
    handle_rate_limit
)
```

## Error Tracking and Reporting

The system provides tools for tracking and reporting on errors:

### Getting Error Statistics

```python
from src.error_handling import error_tracker

# Get a summary of all errors
stats = error_tracker.get_error_summary()

print(f"Total errors: {stats['total_errors']}")
print(f"Errors by category: {stats['by_category']}")
print(f"Errors by severity: {stats['by_severity']}")
print(f"Errors by component: {stats['by_component']}")

# Get recent errors
recent_errors = stats['recent_errors']
```

### Setting Up Error Notifications

```python
from src.error_handling.config import register_notification_email, register_notification_webhook

# Email notifications
register_notification_email(
    smtp_host="smtp.example.com",
    smtp_port=587,
    from_email="alerts@example.com",
    to_emails=["admin@example.com"],
    username="alerts@example.com",
    password="password",
    use_tls=True
)

# Webhook notifications
register_notification_webhook(
    webhook_url="https://example.com/api/error-webhook",
    min_severity=ErrorSeverity.HIGH
)
```

## Best Practices

### General Guidelines

1. **Use Appropriate Error Types**: Always use the most specific error type for the situation. This helps with categorization and appropriate handling.

2. **Include Component Information**: Always specify the component when handling errors to aid in tracking and analysis.

3. **Use Result Types for Functions That May Fail**: For functions that have a high likelihood of failure, use the `ErrorResult` pattern to make error handling explicit.

4. **Log at Appropriate Levels**: Use appropriate log levels based on the severity and importance of the information.

### Patterns by Use Case

#### API Calls

```python
@async_handle_errors(component="api_client")
async def call_api(endpoint, data):
    try:
        response = await client.post(endpoint, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except aiohttp.ClientResponseError as e:
        if e.status == 401:
            raise AuthenticationError("API key invalid or expired")
        elif e.status == 429:
            retry_after = int(e.headers.get("Retry-After", 60))
            raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
        elif e.status >= 500:
            raise ServerError(f"Server error: {e.message}", status_code=e.status)
        else:
            raise InputError(f"Request error: {e.message}", status_code=e.status)
    except aiohttp.ClientConnectorError:
        raise ConnectionError("Failed to connect to API endpoint")
    except asyncio.TimeoutError:
        raise TimeoutError("API request timed out")
```

#### Database Operations

```python
@handle_errors(component="database")
def get_user(user_id):
    try:
        with db.session() as session:
            user = session.query(User).get(user_id)
            if not user:
                raise ValidationError(f"User with ID {user_id} not found")
            return user
    except sqlalchemy.exc.SQLAlchemyError as e:
        raise DatabaseError(f"Database error: {str(e)}")
```

#### File Operations

```python
def read_config_file(file_path):
    with error_context(component="config_loader"):
        try:
            with open(file_path, "r") as f:
                if file_path.endswith(".json"):
                    return json.load(f)
                elif file_path.endswith((".yaml", ".yml")):
                    import yaml
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {file_path}")
        except FileNotFoundError:
            logger.error(f"Config file not found: {file_path}")
            return {}  # Return default empty config
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            return {}
```

#### AI Model Operations

```python
async def generate_text(prompt, model="gpt-4"):
    result = await async_try_result(
        _call_model,
        prompt=prompt,
        model=model,
        component="ai_generation"
    )
    
    if result.has_error:
        # Log the error
        logger.warning(f"Primary model failed: {result.error}")
        
        # Try fallback models
        for fallback_model in fallback_manager.get_fallback_models():
            logger.info(f"Trying fallback model: {fallback_model}")
            fallback_result = await async_try_result(
                _call_model,
                prompt=prompt,
                model=fallback_model,
                component="ai_generation"
            )
            
            if not fallback_result.has_error:
                return fallback_result.value
        
        # If all models failed, return a default response
        return "I'm sorry, I'm having trouble generating a response right now."
    
    return result.value
``` 