"""
Error Handling and Logging Configuration

This module provides utilities for configuring the error handling and logging system
based on application settings.
"""

import os
import json
import logging
from typing import Dict, Optional, Union, Any, List, Set, Callable

from .logging_config import (
    configure_logging, LogLevel, LogFormat, FileRotationPolicy,
    add_file_handler, add_stream_handler
)
from .error_manager import error_manager, fallback_manager, error_tracker
from .error_types import ErrorCategory, ErrorSeverity, ResearchError


def configure_from_env(
    prefix: str = "DDR_",
    default_log_level: Union[LogLevel, str] = LogLevel.INFO,
    default_log_format: Union[LogFormat, str] = LogFormat.STANDARD,
    default_log_dir: str = "logs",
    default_log_file: str = "app.log",
    default_rotation_policy: FileRotationPolicy = FileRotationPolicy.DAILY,
    enable_error_file: bool = True,
    enable_file_logging: bool = False,
    enable_error_notifications: bool = False,
) -> None:
    """
    Configure error handling and logging from environment variables.
    
    Recognized environment variables (with prefix):
    - {prefix}LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - {prefix}LOG_FORMAT: Log format (SIMPLE, STANDARD, DETAILED, JSON)
    - {prefix}LOG_DIR: Directory for log files
    - {prefix}LOG_FILE: Main log file name
    - {prefix}ERROR_LOG_FILE: Error log file name
    - {prefix}LOG_ROTATION: Log rotation policy (SIZE, DAILY, WEEKLY, MONTHLY)
    - {prefix}MAX_LOG_SIZE_MB: Maximum log file size in MB
    - {prefix}LOG_BACKUP_COUNT: Number of backup log files to keep
    - {prefix}ENABLE_FILE_LOGGING: Whether to enable file logging (true/false)
    - {prefix}ENABLE_ERROR_FILE: Whether to enable separate error log file (true/false)
    - {prefix}ENABLE_ERROR_NOTIFICATIONS: Whether to enable error notifications (true/false)
    
    Args:
        prefix: Prefix for environment variables
        default_log_level: Default log level if not specified in environment
        default_log_format: Default log format if not specified in environment
        default_log_dir: Default log directory if not specified in environment
        default_log_file: Default log file name if not specified in environment
        default_rotation_policy: Default log rotation policy if not specified in environment
        enable_error_file: Whether to create a separate error log file
        enable_file_logging: Whether to enable file logging by default
        enable_error_notifications: Whether to enable error notifications by default
    """
    # Get configuration from environment variables
    log_level_str = os.environ.get(f"{prefix}LOG_LEVEL", None)
    log_format_str = os.environ.get(f"{prefix}LOG_FORMAT", None)
    log_dir = os.environ.get(f"{prefix}LOG_DIR", default_log_dir)
    log_file = os.environ.get(f"{prefix}LOG_FILE", default_log_file)
    error_log_file = os.environ.get(f"{prefix}ERROR_LOG_FILE", "errors.log")
    rotation_policy_str = os.environ.get(f"{prefix}LOG_ROTATION", None)
    max_log_size_mb = int(os.environ.get(f"{prefix}MAX_LOG_SIZE_MB", "10"))
    backup_count = int(os.environ.get(f"{prefix}LOG_BACKUP_COUNT", "5"))
    
    # Boolean flags
    enable_file_logging_str = os.environ.get(f"{prefix}ENABLE_FILE_LOGGING", "").lower()
    if enable_file_logging_str in ("true", "1", "yes", "y"):
        enable_file_logging = True
    elif enable_file_logging_str in ("false", "0", "no", "n"):
        enable_file_logging = False
    
    enable_error_file_str = os.environ.get(f"{prefix}ENABLE_ERROR_FILE", "").lower()
    if enable_error_file_str in ("true", "1", "yes", "y"):
        enable_error_file = True
    elif enable_error_file_str in ("false", "0", "no", "n"):
        enable_error_file = False
    
    enable_error_notifications_str = os.environ.get(f"{prefix}ENABLE_ERROR_NOTIFICATIONS", "").lower()
    if enable_error_notifications_str in ("true", "1", "yes", "y"):
        enable_error_notifications = True
    elif enable_error_notifications_str in ("false", "0", "no", "n"):
        enable_error_notifications = False
    
    # Convert log level string to LogLevel enum if provided
    if log_level_str:
        try:
            log_level = getattr(LogLevel, log_level_str.upper())
        except (AttributeError, TypeError):
            # Fall back to default if invalid
            log_level = default_log_level
    else:
        log_level = default_log_level
    
    # Convert log format string to LogFormat enum if provided
    if log_format_str:
        try:
            log_format = getattr(LogFormat, log_format_str.upper())
        except (AttributeError, TypeError):
            # Fall back to default if invalid
            log_format = default_log_format
    else:
        log_format = default_log_format
    
    # Convert rotation policy string to FileRotationPolicy enum if provided
    if rotation_policy_str:
        try:
            rotation_policy = getattr(FileRotationPolicy, rotation_policy_str.upper())
        except (AttributeError, TypeError):
            # Fall back to default if invalid
            rotation_policy = default_rotation_policy
    else:
        rotation_policy = default_rotation_policy
    
    # Configure logging
    configure_logging(
        level=log_level,
        format_style=log_format,
        log_to_console=True,
        log_to_file=enable_file_logging,
        log_dir=log_dir,
        file_name=log_file,
        rotation_policy=rotation_policy,
        max_file_size_mb=max_log_size_mb,
        backup_count=backup_count
    )
    
    # Add separate error log file if enabled
    if enable_error_file:
        add_file_handler(
            file_name=error_log_file,
            level=LogLevel.ERROR,
            format_style=log_format,
            rotation_policy=rotation_policy,
            max_file_size_mb=max_log_size_mb,
            backup_count=backup_count
        )
    
    # Initialize error manager
    error_manager.initialize(
        enable_file_logging=enable_error_file,
        log_dir=log_dir
    )


def configure_from_dict(config: Dict[str, Any]) -> None:
    """
    Configure error handling and logging from a dictionary.
    
    Args:
        config: Dictionary with configuration settings
        
    Example config:
    {
        "logging": {
            "level": "INFO",
            "format": "STANDARD",
            "log_dir": "logs",
            "log_file": "app.log",
            "error_log_file": "errors.log",
            "rotation_policy": "DAILY",
            "max_file_size_mb": 10,
            "backup_count": 5,
            "enable_file_logging": true,
            "enable_error_file": true
        },
        "error_handling": {
            "enable_notifications": true,
            "error_tracking_max_history": 100,
            "fallback_models": [
                {"id": "gpt-3.5-turbo", "priority": 1},
                {"id": "gpt-3.5-turbo-16k", "priority": 2}
            ]
        }
    }
    """
    # Extract logging configuration
    logging_config = config.get("logging", {})
    
    log_level = logging_config.get("level", "INFO")
    log_format = logging_config.get("format", "STANDARD")
    log_dir = logging_config.get("log_dir", "logs")
    log_file = logging_config.get("log_file", "app.log")
    error_log_file = logging_config.get("error_log_file", "errors.log")
    rotation_policy = logging_config.get("rotation_policy", "DAILY")
    max_file_size_mb = logging_config.get("max_file_size_mb", 10)
    backup_count = logging_config.get("backup_count", 5)
    enable_file_logging = logging_config.get("enable_file_logging", False)
    enable_error_file = logging_config.get("enable_error_file", True)
    
    # Extract error handling configuration
    error_config = config.get("error_handling", {})
    
    enable_notifications = error_config.get("enable_notifications", False)
    error_tracking_max_history = error_config.get("error_tracking_max_history", 100)
    fallback_models = error_config.get("fallback_models", [])
    
    # Configure logging
    configure_logging(
        level=log_level,
        format_style=log_format,
        log_to_console=True,
        log_to_file=enable_file_logging,
        log_dir=log_dir,
        file_name=log_file,
        rotation_policy=rotation_policy,
        max_file_size_mb=max_file_size_mb,
        backup_count=backup_count
    )
    
    # Add separate error log file if enabled
    if enable_error_file:
        add_file_handler(
            file_name=error_log_file,
            level=LogLevel.ERROR,
            format_style=log_format,
            rotation_policy=rotation_policy,
            max_file_size_mb=max_file_size_mb,
            backup_count=backup_count
        )
    
    # Initialize error manager
    error_manager.initialize(
        enable_file_logging=enable_error_file,
        log_dir=log_dir
    )
    
    # Configure error tracker capacity
    error_tracker.max_history = error_tracking_max_history
    
    # Register fallback models
    for model in fallback_models:
        fallback_manager.register_fallback_model(
            model_id=model["id"],
            priority=model.get("priority", 0)
        )


def configure_from_file(file_path: str) -> None:
    """
    Configure error handling and logging from a JSON or YAML file.
    
    Args:
        file_path: Path to the configuration file
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    # Determine file type from extension
    if file_path.endswith((".json", ".js")):
        # JSON file
        with open(file_path, "r") as f:
            config = json.load(f)
    elif file_path.endswith((".yaml", ".yml")):
        # YAML file
        try:
            import yaml
            with open(file_path, "r") as f:
                config = yaml.safe_load(f)
        except ImportError:
            raise ImportError("YAML support requires PyYAML. Please install with: pip install pyyaml")
    else:
        raise ValueError(f"Unsupported configuration file format: {file_path}")
    
    # Configure from the loaded dictionary
    configure_from_dict(config)


def register_notification_email(
    smtp_host: str,
    smtp_port: int,
    from_email: str,
    to_emails: List[str],
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_tls: bool = True,
    subject_prefix: str = "[ERROR]"
) -> None:
    """
    Register an email notification handler for critical errors.
    
    Args:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        from_email: Sender email address
        to_emails: Recipient email addresses
        username: SMTP username (if authentication is required)
        password: SMTP password (if authentication is required)
        use_tls: Whether to use TLS for SMTP connection
        subject_prefix: Prefix for email subject line
    """
    # Define email notification callback
    def send_error_email(error: ResearchError) -> None:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import datetime
        
        # Only send notifications for high-severity errors
        if error.error_severity not in (ErrorSeverity.CRITICAL, ErrorSeverity.HIGH):
            return
        
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = f"{subject_prefix} {error.error_category.value.upper()}: {error.message}"
        
        # Create the email body
        body = f"""
        Error Details:
        --------------
        Time: {datetime.fromtimestamp(error.timestamp).isoformat()}
        Category: {error.error_category.value}
        Severity: {error.error_severity.value}
        Component: {error.component or 'Unknown'}
        Message: {error.message}
        Status Code: {error.status_code or 'N/A'}
        
        Additional Information:
        ----------------------
        {error.response_text or 'No additional information available.'}
        
        This is an automated notification from the Deep Deep Research error handling system.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            # Connect to the SMTP server
            server = smtplib.SMTP(smtp_host, smtp_port)
            if use_tls:
                server.starttls()
            
            # Login if credentials provided
            if username and password:
                server.login(username, password)
            
            # Send the email
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Sent error notification email for {error.error_category.value} error")
        except Exception as e:
            logging.error(f"Failed to send error notification email: {e}")
    
    # Register the callback with the error manager
    error_manager.register_notification_callback(send_error_email)


def register_notification_webhook(
    webhook_url: str,
    error_categories: Optional[Set[ErrorCategory]] = None,
    min_severity: ErrorSeverity = ErrorSeverity.HIGH,
    custom_formatter: Optional[Callable[[ResearchError], Dict[str, Any]]] = None
) -> None:
    """
    Register a webhook notification handler for errors.
    
    Args:
        webhook_url: URL for the webhook
        error_categories: Categories of errors to send notifications for (None = all)
        min_severity: Minimum severity level for notifications
        custom_formatter: Optional function to format the error data for the webhook
    """
    # Define webhook notification callback
    def send_webhook_notification(error: ResearchError) -> None:
        import requests
        from datetime import datetime
        
        # Filter by severity
        if error.error_severity.value < min_severity.value:
            return
        
        # Filter by category if specified
        if error_categories and error.error_category not in error_categories:
            return
        
        # Format the data
        if custom_formatter:
            data = custom_formatter(error)
        else:
            # Default formatting
            data = {
                'timestamp': datetime.fromtimestamp(error.timestamp).isoformat(),
                'category': error.error_category.value,
                'severity': error.error_severity.value,
                'component': error.component or 'Unknown',
                'message': error.message,
                'status_code': error.status_code,
                'is_retryable': error.is_retryable,
                'retry_after': error.retry_after
            }
        
        try:
            # Send the webhook request
            response = requests.post(
                webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=5  # 5 second timeout
            )
            
            if response.status_code < 200 or response.status_code >= 300:
                logging.warning(
                    f"Webhook notification returned non-success status code: "
                    f"{response.status_code} - {response.text}"
                )
            else:
                logging.info(f"Sent webhook notification for {error.error_category.value} error")
        
        except Exception as e:
            logging.error(f"Failed to send webhook notification: {e}")
    
    # Register the callback with the error manager
    error_manager.register_notification_callback(send_webhook_notification) 