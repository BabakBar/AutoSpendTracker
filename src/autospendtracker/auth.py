"""Gmail authentication module for AutoSpendTracker.

This module handles authentication with Gmail API using OAuth2.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from autospendtracker.security import get_credential_path, secure_token_path

# Set up logging
logger = logging.getLogger(__name__)

# Default scopes required for the application
DEFAULT_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

def gmail_authenticate(
    credentials_path: str = None,
    token_path: str = None,
    scopes: Optional[List[str]] = None
):
    """Authenticate with Gmail API using OAuth2.

    Args:
        credentials_path: Path to credentials.json file
        token_path: Path to gmail-token.json file (will be created if doesn't exist)
        scopes: OAuth scopes to request (defaults to DEFAULT_SCOPES)

    Returns:
        A Gmail API service object
    """
    if scopes is None:
        scopes = DEFAULT_SCOPES
    
    # Use security module to get secure paths
    if credentials_path is None:
        credentials_path = get_credential_path('credentials', 'credentials.json')
    
    if token_path is None:
        token_path = secure_token_path('gmail-token.json')

    creds = None
    # Load token file if it exists
    token_file = Path(token_path)
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    # If credentials are missing or invalid, refresh or get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Attempting to refresh expired OAuth token...")
                creds.refresh(Request())
                logger.info("Token refreshed successfully")
            except Exception as e:
                # Refresh failed - delete old token and get new credentials
                logger.warning(f"Token refresh failed: {e}")
                logger.info("Deleting old token and starting new OAuth flow...")
                if Path(token_path).exists():
                    Path(token_path).unlink()
                    logger.info(f"Deleted old token file: {token_path}")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
                creds = flow.run_local_server(port=0)
                logger.info("New OAuth credentials obtained successfully")
        else:
            logger.info("Starting OAuth flow to obtain credentials...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
            logger.info("OAuth credentials obtained successfully")
        # Save the credentials for the next run
        token_file = Path(token_path)
        token_file.write_text(creds.to_json(), encoding='utf-8')
        token_file.chmod(0o600)  # Secure file permissions
        logger.info(f"Credentials saved to: {token_path}")
    
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


if __name__ == '__main__':
    service = gmail_authenticate()
    # Simple test to list labels
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])