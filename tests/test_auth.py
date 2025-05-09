"""Tests for the auth module."""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from autospendtracker.auth import gmail_authenticate, DEFAULT_SCOPES


class TestAuth(unittest.TestCase):
    """Test cases for the auth module."""

    @patch('autospendtracker.auth.build')
    @patch('autospendtracker.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('autospendtracker.auth.pickle.dump')
    @patch('autospendtracker.auth.pickle.load')
    @patch('autospendtracker.auth.Path.exists')
    def test_gmail_authenticate_new_token(self, mock_exists, mock_pickle_load, 
                                        mock_pickle_dump, mock_flow, mock_build):
        """Test gmail_authenticate when no valid token exists."""
        # Mock Path.exists to return False (no token file)
        mock_exists.return_value = False
        
        # Mock the OAuth flow
        mock_creds = MagicMock()
        mock_flow.return_value.run_local_server.return_value = mock_creds
        
        # Mock the build function
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call the function
        with tempfile.NamedTemporaryFile() as temp_token:
            result = gmail_authenticate(
                credentials_path="dummy_credentials.json",
                token_path=temp_token.name
            )
            
            # Check that InstalledAppFlow was called correctly
            mock_flow.assert_called_once_with("dummy_credentials.json", DEFAULT_SCOPES)
            mock_flow.return_value.run_local_server.assert_called_once_with(port=0)
            
            # Check that pickle.dump was called to save the token
            mock_pickle_dump.assert_called_once()
            
            # Check that build was called correctly
            mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
            
            # Check that the function returns the service
            self.assertEqual(result, mock_service)

    # Add more test methods as needed


if __name__ == '__main__':
    unittest.main()