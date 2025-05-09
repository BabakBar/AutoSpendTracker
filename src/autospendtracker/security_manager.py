"""Security Manager for Google Secret Manager integration.

This module handles interactions with Google Cloud Secret Manager for securely
accessing sensitive configuration and credentials.
"""

import json
import logging
import os
from typing import Any, Dict, Optional
from pathlib import Path
import tempfile

try:
    from google.cloud import secretmanager
    from google.cloud.secretmanager_v1 import SecretManagerServiceClient
    HAS_SECRET_MANAGER = True
except ImportError:
    HAS_SECRET_MANAGER = False

from autospendtracker.utils import handle_exceptions

# Set up logging
logger = logging.getLogger(__name__)


class SecretManagerNotAvailable(Exception):
    """Exception raised when Secret Manager library is not available."""
    pass


class SecretManagerClient:
    """Client for interacting with Google Cloud Secret Manager.
    
    This class provides methods for retrieving secrets from Google Cloud Secret Manager,
    with fallback mechanisms for local development.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize the Secret Manager client.
        
        Args:
            project_id: Google Cloud project ID (if None, will try to get from environment)
        
        Raises:
            SecretManagerNotAvailable: If the Secret Manager library is not available
            ValueError: If project_id is not provided and not in environment
        """
        if not HAS_SECRET_MANAGER:
            logger.warning("Google Cloud Secret Manager library not available. "
                          "Install with 'pip install google-cloud-secret-manager'")
            raise SecretManagerNotAvailable(
                "Google Cloud Secret Manager library not installed"
            )
        
        # Get project ID from environment if not provided
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError(
                "Project ID must be provided or set in GOOGLE_CLOUD_PROJECT environment variable"
            )
            
        # Initialize the client
        try:
            self.client = secretmanager.SecretManagerServiceClient()
            logger.info(f"Secret Manager client initialized for project {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Secret Manager client: {e}")
            raise
    
    @handle_exceptions(reraise=True)
    def get_secret(self, secret_id: str, version_id: str = "latest") -> str:
        """Get a secret from Secret Manager.
        
        Args:
            secret_id: ID of the secret to retrieve
            version_id: Version of the secret (default: latest)
            
        Returns:
            Secret value as a string
            
        Raises:
            Exception: If the secret cannot be accessed
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        logger.debug(f"Accessing secret: {secret_id}")
        
        response = self.client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        
        return payload
    
    @handle_exceptions(fallback_return=None)
    def get_json_secret(self, secret_id: str, version_id: str = "latest") -> Optional[Dict[str, Any]]:
        """Get a JSON secret from Secret Manager.
        
        Args:
            secret_id: ID of the secret to retrieve
            version_id: Version of the secret (default: latest)
            
        Returns:
            Parsed JSON data or None if failed
        """
        payload = self.get_secret(secret_id, version_id)
        return json.loads(payload)
    
    @handle_exceptions(fallback_return=None)
    def get_service_account_credentials(
        self, 
        secret_id: str, 
        version_id: str = "latest",
        scopes: Optional[list] = None
    ) -> Optional[Any]:
        """Get service account credentials from Secret Manager.
        
        Retrieves a service account JSON from Secret Manager and converts it
        to a credentials object that can be used for authentication.
        
        Args:
            secret_id: ID of the secret containing the service account JSON
            version_id: Version of the secret (default: latest)
            scopes: OAuth scopes to request (optional)
            
        Returns:
            Service account credentials object or None if failed
        """
        from google.oauth2 import service_account
        
        try:
            # Get the service account JSON
            sa_json = self.get_secret(secret_id, version_id)
            
            # Create a temporary file to store the JSON
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
                tmp.write(sa_json)
                tmp_path = tmp.name
            
            # Load credentials from the temporary file
            try:
                if scopes:
                    credentials = service_account.Credentials.from_service_account_file(
                        tmp_path, scopes=scopes
                    )
                else:
                    credentials = service_account.Credentials.from_service_account_file(
                        tmp_path
                    )
                return credentials
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to get service account credentials: {e}")
            return None


def get_secret_manager_client(project_id: Optional[str] = None) -> Optional[SecretManagerClient]:
    """Get a Secret Manager client if available, or None if not.
    
    Args:
        project_id: Google Cloud project ID
        
    Returns:
        SecretManagerClient instance or None if not available
    """
    try:
        return SecretManagerClient(project_id)
    except (SecretManagerNotAvailable, ValueError, Exception) as e:
        logger.warning(f"Secret Manager not available: {e}")
        return None


def get_secret(
    secret_id: str, 
    project_id: Optional[str] = None,
    fallback_value: Optional[str] = None,
    fallback_env_var: Optional[str] = None
) -> Optional[str]:
    """Get a secret from Secret Manager with fallback options.
    
    This is the main function to use for getting secrets. It will try:
    1. Secret Manager
    2. Environment variable (if specified)
    3. Fallback value
    
    Args:
        secret_id: ID of the secret in Secret Manager
        project_id: Google Cloud project ID
        fallback_value: Value to return if Secret Manager fails
        fallback_env_var: Environment variable to check if Secret Manager fails
        
    Returns:
        Secret value or fallback or None
    """
    # Try Secret Manager first
    client = get_secret_manager_client(project_id)
    if client:
        try:
            return client.get_secret(secret_id)
        except Exception as e:
            logger.warning(f"Failed to get secret {secret_id} from Secret Manager: {e}")
    
    # Try environment variable
    if fallback_env_var and fallback_env_var in os.environ:
        logger.info(f"Using {fallback_env_var} environment variable as fallback for {secret_id}")
        return os.environ[fallback_env_var]
    
    # Use fallback value
    if fallback_value is not None:
        logger.info(f"Using fallback value for {secret_id}")
        return fallback_value
    
    logger.warning(f"No value available for secret {secret_id}")
    return None