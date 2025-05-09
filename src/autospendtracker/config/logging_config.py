"""Logging configuration for AutoSpendTracker.

This module provides a centralized configuration for logging across the application.
"""

import logging
import os
import sys
import io
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Default locations
DEFAULT_LOG_DIR = os.path.join(os.path.expanduser("~"), ".autospendtracker", "logs")
DEFAULT_LOG_FILE = os.path.join(DEFAULT_LOG_DIR, "autospendtracker.log")

def setup_logging(
    level=logging.INFO, 
    log_file=DEFAULT_LOG_FILE,
    console=True
):
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
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
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
        # Use TextIOWrapper with UTF-8 encoding to handle international characters
        console_handler = logging.StreamHandler(
            stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger