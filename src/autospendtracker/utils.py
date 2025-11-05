"""Utility functions and classes for AutoSpendTracker.

This module contains various utility functions used across the application.
"""

import logging
import functools
import traceback
import sys
import io
from typing import Callable, TypeVar, Any, Optional, Dict

# Import exceptions from the centralized exceptions module
from autospendtracker.exceptions import (
    AutoSpendTrackerError,
    ConfigurationError,
    AIModelError,
    TransactionValidationError
)

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])

# Re-export exceptions for backward compatibility
APIError = AIModelError
DataValidationError = TransactionValidationError


def configure_unicode_logging():
    """
    Configure logging handlers to properly handle Unicode characters.
    
    This solves issues with non-ASCII characters (like Turkish, Chinese, etc.)
    in Windows console output which uses cp1252 encoding by default.
    """
    root_logger = logging.getLogger()
    
    # Remove any existing StreamHandlers to avoid duplication
    handlers_to_remove = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
    for handler in handlers_to_remove:
        root_logger.removeHandler(handler)
    
    # Add a new StreamHandler with proper Unicode handling
    handler = logging.StreamHandler(stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    logger.info("Configured logging for Unicode character handling")


def handle_exceptions(
    fallback_return: Optional[Any] = None,
    log_level: int = logging.ERROR,
    reraise: bool = False,
    message: str = "An error occurred"
) -> Callable[[F], F]:
    """
    Decorator for standardized exception handling.
    
    Args:
        fallback_return: Value to return if an exception occurs
        log_level: Logging level for the exception
        reraise: Whether to reraise the exception after handling
        message: Custom message to log with the exception
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get exception details
                exc_type, exc_value, exc_tb = sys.exc_info()
                tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
                
                # Log the exception
                logger.log(log_level, f"{message}: {str(e)}\n{tb_str}")
                
                # Reraise if requested
                if reraise:
                    raise
                    
                # Return fallback value
                return fallback_return
                
        return wrapper  # type: ignore
    return decorator


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary, with nested key support.
    
    Args:
        dictionary: Dictionary to get value from
        key: Key to get, can be dot-separated for nested dictionaries
        default: Default value to return if key not found
        
    Returns:
        Value from dictionary or default
    
    Example:
        >>> data = {"user": {"name": "John", "profile": {"age": 30}}}
        >>> safe_get(data, "user.profile.age")
        30
    """
    if not dictionary or not isinstance(dictionary, dict):
        return default
        
    # Handle simple case
    if '.' not in key:
        return dictionary.get(key, default)
    
    # Handle nested case
    parts = key.split('.')
    current = dictionary
    
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    
    return current