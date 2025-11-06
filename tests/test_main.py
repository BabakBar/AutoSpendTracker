"""Tests for the main module."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from pathlib import Path

from autospendtracker.main import (
    save_transaction_data,
    process_emails,
    run_pipeline
)


class TestMain(unittest.TestCase):
    """Test cases for the main module."""

    def test_save_transaction_data(self):
        """Test saving transaction data to file."""
        # Test data
        data = [
            ['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise'],
            ['02-05-2023', '3:45 PM', 'Grocery Store', '120.50', 'USD', 'Grocery', 'PayPal']
        ]

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            # Save data
            save_transaction_data(data, temp_file)

            # Load and verify
            with open(temp_file, 'r') as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data, data)
        finally:
            # Clean up
            Path(temp_file).unlink()

    @patch('autospendtracker.main.process_transaction')
    @patch('autospendtracker.main.parse_email')
    @patch('autospendtracker.main.search_messages')
    @patch('autospendtracker.main.gmail_authenticate')
    @patch('autospendtracker.main.initialize_ai_model')
    def test_process_emails_success(self, mock_init_ai, mock_gmail_auth,
                                     mock_search, mock_parse, mock_process):
        """Test successful email processing."""
        # Mock AI client
        mock_client = MagicMock()
        mock_init_ai.return_value = mock_client

        # Mock Gmail service
        mock_service = MagicMock()
        mock_gmail_auth.return_value = mock_service

        # Mock found messages
        mock_search.return_value = [
            {'id': 'msg1'},
            {'id': 'msg2'}
        ]

        # Mock parsed email
        mock_parse.return_value = {
            'date': '01-05-2023 12:34 PM',
            'info': 'You spent 45.67 EUR at Coffee Shop.',
            'account': 'Wise'
        }

        # Mock processed transaction
        mock_process.return_value = [
            '01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise'
        ]

        # Call the function
        result = process_emails()

        # Check that services were initialized
        mock_init_ai.assert_called_once()
        mock_gmail_auth.assert_called_once()

        # Check that messages were searched
        mock_search.assert_called_once_with(mock_service)

        # Check that emails were parsed (once for each message)
        self.assertEqual(mock_parse.call_count, 2)

        # Check that transactions were processed
        self.assertEqual(mock_process.call_count, 2)

        # Check result
        self.assertEqual(len(result), 2)

    @patch('autospendtracker.main.search_messages')
    @patch('autospendtracker.main.gmail_authenticate')
    @patch('autospendtracker.main.initialize_ai_model')
    def test_process_emails_no_messages(self, mock_init_ai, mock_gmail_auth, mock_search):
        """Test processing when no emails are found."""
        # Mock services
        mock_client = MagicMock()
        mock_init_ai.return_value = mock_client

        mock_service = MagicMock()
        mock_gmail_auth.return_value = mock_service

        # Mock no messages found
        mock_search.return_value = []

        # Call the function
        result = process_emails()

        # Check result
        self.assertEqual(result, [])

    @patch('autospendtracker.main.append_to_sheet')
    @patch('autospendtracker.main.save_transaction_data')
    @patch('autospendtracker.main.process_emails')
    def test_run_pipeline_success(self, mock_process_emails, mock_save, mock_append):
        """Test successful pipeline run."""
        # Mock processed data
        mock_data = [
            ['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise']
        ]
        mock_process_emails.return_value = mock_data

        # Call the function
        result = run_pipeline(save_to_file=True, upload_to_sheets=True)

        # Check that emails were processed
        mock_process_emails.assert_called_once()

        # Check that data was saved
        mock_save.assert_called_once_with(mock_data)

        # Check that data was uploaded
        mock_append.assert_called_once()

        # Check result
        self.assertEqual(result, mock_data)

    @patch('autospendtracker.main.process_emails')
    def test_run_pipeline_no_transactions(self, mock_process_emails):
        """Test pipeline when no transactions are found."""
        # Mock no transactions
        mock_process_emails.return_value = []

        # Call the function
        result = run_pipeline()

        # Check result
        self.assertIsNone(result)

    @patch('autospendtracker.main.process_emails')
    def test_run_pipeline_error(self, mock_process_emails):
        """Test pipeline error handling."""
        # Mock error
        mock_process_emails.side_effect = Exception("Test error")

        # Call the function
        result = run_pipeline()

        # Check result
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
