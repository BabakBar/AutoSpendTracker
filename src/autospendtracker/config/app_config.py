"""Application configuration module.

This module handles loading and managing application configuration.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Default config values
DEFAULT_CONFIG = {
    # Google Cloud settings
    "PROJECT_ID": None,  # Must be provided by environment or .env
    "LOCATION": "us-central1",
    "SERVICE_ACCOUNT_FILE": "ASTservice.json",
    
    # Google Sheets settings
    "SPREADSHEET_ID": None,  # Must be provided by environment or .env
    "SHEET_RANGE": "Sheet1!A2:G",
    
    # Application settings
    "LOG_LEVEL": "INFO",
    "OUTPUT_FILE": "transaction_data.json",
    "TOKEN_DIR": str(Path.home() / ".autospendtracker" / "secrets"),
    
    # AI Model settings
    "MODEL_NAME": "gemini-1.5-pro-001",  # Updated to a more widely available model
    "MODEL_TEMPERATURE": 0.1,
}


def load_config(env_file: str = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Path to .env file. If None, will try to load from .env in current directory
        
    Returns:
        Dictionary of configuration values
    """
    # Load from .env file if it exists
    if env_file and Path(env_file).exists():
        load_dotenv(env_file)
    else:
        load_dotenv()  # Default behavior - look for .env in current directory
    
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    for key in config:
        if key in os.environ:
            config[key] = os.environ[key]
    
    # Validate required settings
    missing_required = []
    if not config["PROJECT_ID"]:
        missing_required.append("PROJECT_ID")
    if not config["SPREADSHEET_ID"]:
        missing_required.append("SPREADSHEET_ID")
    
    if missing_required:
        logger.warning(f"Missing required configuration: {', '.join(missing_required)}")
    
    return config


def get_config_value(key: str, default: Any = None, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Get a configuration value with fallback to default.
    
    Args:
        key: Configuration key to get
        default: Default value if key is not found
        config: Configuration dictionary (if None, loads config)
        
    Returns:
        Configuration value or default
    """
    if config is None:
        config = load_config()
    
    return config.get(key, default)


# Singleton config object - load once at module import time
CONFIG = load_config()


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    Returns:
        Dictionary of configuration values
    """
    return CONFIG


def reload_config(env_file: str = None) -> Dict[str, Any]:
    """
    Reload configuration (useful for testing).
    
    Args:
        env_file: Path to .env file
        
    Returns:
        Updated configuration dictionary
    """
    global CONFIG
    CONFIG = load_config(env_file)
    return CONFIG