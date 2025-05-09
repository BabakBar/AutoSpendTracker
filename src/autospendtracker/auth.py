"""Gmail authentication module for AutoSpendTracker.

This module handles authentication with Gmail API using OAuth2.
"""

import os
import pickle
from pathlib import Path
from typing import List, Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from autospendtracker.security import get_credential_path, secure_token_path

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
        token_path: Path to token.pickle file (will be created if doesn't exist)
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
        token_path = secure_token_path('gmail_token.pickle')
        
    creds = None
    # Load token file if it exists
    if Path(token_path).exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If credentials are missing or invalid, refresh or get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


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