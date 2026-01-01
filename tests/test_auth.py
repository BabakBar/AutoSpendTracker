"""Tests for the auth module."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autospendtracker.auth import gmail_authenticate, DEFAULT_SCOPES


class TestAuth(unittest.TestCase):
    """Test cases for the auth module."""

    @patch('autospendtracker.auth.build')
    @patch('autospendtracker.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('autospendtracker.auth.Path.write_text')
    @patch('autospendtracker.auth.Path.chmod')
    @patch('autospendtracker.auth.Path.exists')
    def test_gmail_authenticate_new_token(self, mock_exists, mock_chmod, mock_write_text, 
                                        mock_flow, mock_build):
        """Test gmail_authenticate when no valid token exists."""
        # Mock Path.exists to return False (no token file)
        mock_exists.return_value = False
        
        # Mock the OAuth flow
        mock_creds = MagicMock()
        mock_creds.to_json.return_value = '{"token": "fake"}'
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
            
            # Check that write_text was called to save the token
            mock_write_text.assert_called_once()
            
            # Check that build was called correctly
            mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds, cache_discovery=False)
            
            # Check that the function returns the service
            self.assertEqual(result, mock_service)

    # Add more test methods as needed


if __name__ == '__main__':
    unittest.main()