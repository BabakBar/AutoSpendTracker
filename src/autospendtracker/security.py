"""Security module for AutoSpendTracker.

This module handles secure credential storage and access.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

def get_credential_path(credential_name: str, default_path: str) -> str:
    """
    Get the path to a credential file, checking environment variables first.
    
    Args:
        credential_name: Name of the credential (used for env var lookup)
        default_path: Default path to use if no env var is set
        
    Returns:
        Path to the credential file
    """
    # Check if path is provided via environment variable
    env_var_name = f"{credential_name.upper()}_PATH"
    if env_var_name in os.environ:
        return os.environ[env_var_name]
    
    # If not, use the default path
    return default_path

def load_credentials(file_path: str) -> Dict[str, Any]:
    """
    Load credentials from a JSON file.
    
    Args:
        file_path: Path to the credentials JSON file
        
    Returns:
        Dictionary of credential data
    
    Raises:
        FileNotFoundError: If the credentials file doesn't exist
        json.JSONDecodeError: If the credentials file isn't valid JSON
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Credentials file not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid credentials file format: {file_path}")
        raise

def secure_token_path(base_path: str = 'token.pickle') -> str:
    """
    Create a secure token storage path.
    
    Args:
        base_path: Base filename for the token
        
    Returns:
        Full path to store the token securely
    """
    # Check if custom path provided in environment
    if 'TOKEN_PATH' in os.environ:
        return os.environ['TOKEN_PATH']
    
    # Create a secure storage location in user's home directory
    home_dir = Path.home()
    secure_dir = home_dir / '.autospendtracker' / 'secrets'
    secure_dir.mkdir(parents=True, exist_ok=True)
    
    # Set appropriate permissions on Unix systems
    try:
        if os.name == 'posix':  # Unix-like system
            os.chmod(secure_dir, 0o700)  # rwx for user only
    except Exception as e:
        logger.warning(f"Could not set secure permissions: {e}")
    
    return str(secure_dir / base_path)