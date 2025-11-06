"""Logging configuration for AutoSpendTracker.

This module provides a centralized configuration for logging across the application.
"""

import logging
import sys
import io
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union

# Default locations
DEFAULT_LOG_DIR = Path.home() / ".autospendtracker" / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "autospendtracker.log"

def setup_logging(
    level: int = logging.INFO,
    log_file: Union[str, Path, None] = DEFAULT_LOG_FILE,
    console: bool = True
) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        level: The logging level (default: INFO)
        log_file: Path to log file (default: ~/.autospendtracker/logs/autospendtracker.log)
        console: Whether to log to console (default: True)
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Set up file logging
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        log_dir = log_path.parent
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            
        # Create rotating file handler (10MB max, keep 3 backups)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'  # Ensure UTF-8 encoding for file logs
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Set up console logging with UTF-8 encoding
    if console:
        # Try to reconfigure stdout for UTF-8 if possible (Python 3.7+)
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            pass  # Not critical if this fails

        # Use regular StreamHandler - sys.stdout should now handle UTF-8
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Silence noisy third-party libraries (INFO/DEBUG level noise)
    # httpx logs every HTTP request at INFO - too verbose
    logging.getLogger('httpx').setLevel(logging.WARNING)
    # Google Gen AI SDK logs internal implementation details
    logging.getLogger('google_genai').setLevel(logging.WARNING)
    logging.getLogger('google_genai.models').setLevel(logging.WARNING)
    logging.getLogger('google_genai._api_client').setLevel(logging.WARNING)

    return logger