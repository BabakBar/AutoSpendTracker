"""Tests for the mail module."""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from autospendtracker.mail import search_messages, parse_email, get_email_body


class TestMail(unittest.TestCase):
    """Test cases for the mail module."""

    @patch('autospendtracker.mail.logging')
    def test_search_messages_success(self, mock_logging):
        """Test successful search_messages."""
        # Mock Gmail service and response
        mock_service = MagicMock()
        mock_response = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'}
            ]
        }
        mock_service.users().messages().list().execute.return_value = mock_response
        
        # Call the function
        result = search_messages(mock_service)
        
        # Check that the API was called with the correct parameters
        mock_service.users().messages().list.assert_called_once_with(
            userId='me',
            q='(from:noreply@wise.com ("You spent" OR "is now in")) OR '
              '(from:service@paypal.de "Von Ihnen gezahlt")'
        )
        
        # Check that the function returns the messages
        self.assertEqual(result, [{'id': 'msg1'}, {'id': 'msg2'}])
        
        # Check that the function logs the correct info
        mock_logging.info.assert_any_call("Searching for transaction emails")
        mock_logging.info.assert_any_call("Found 2 transaction emails")

    @patch('autospendtracker.mail.logging')
    def test_search_messages_failure(self, mock_logging):
        """Test search_messages with API error."""
        # Mock Gmail service to raise an exception
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = Exception("API Error")
        
        # Call the function
        result = search_messages(mock_service)
        
        # Check that the function returns None
        self.assertIsNone(result)
        
        # Check that the error is logged
        mock_logging.error.assert_called_with("Error searching messages: API Error")

    @patch('autospendtracker.mail.get_email_body')
    def test_parse_email_wise_transaction(self, mock_get_email_body):
        """Test parsing a Wise transaction email."""
        # Mock dependencies
        mock_service = MagicMock()
        mock_message = {
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'Wise <noreply@wise.com>'},
                    {'name': 'Date', 'value': 'Mon, 1 May 2023 12:34:56 +0000'}
                ]
            }
        }
        mock_service.users().messages().get().execute.return_value = mock_message
        
        # Mock the email body to have a Wise transaction
        mock_get_email_body.return_value = """
        <html>
            <body>
                You spent 45.67 EUR at Coffee Shop. Your balance is now 123.45 EUR.
            </body>
        </html>
        """
        
        # Call the function
        result = parse_email(mock_service, 'me', 'msg_id')
        
        # Check result contains expected data
        self.assertEqual(result['account'], 'Wise')
        self.assertIn('You spent', result['info'])
        self.assertIsNotNone(result['date'])

    # Add more test methods as needed


if __name__ == '__main__':
    unittest.main()