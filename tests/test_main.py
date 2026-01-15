"""Tests for the main module."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from pathlib import Path

from autospendtracker.main import (
    save_transaction_data,
    process_emails,
    run_pipeline,
    ServiceBundle
)
from autospendtracker.models import Transaction


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
    def test_process_emails_success(self, mock_search, mock_parse, mock_process):
        """Test successful email processing."""
        # Mock services bundle
        mock_client = MagicMock()
        mock_service = MagicMock()
        services = ServiceBundle(
            ai_client=mock_client,
            gmail_service=mock_service,
            label_id="label-id",
            label_name="AutoSpendTracker/Processed"
        )

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
        mock_process.return_value = Transaction(
            amount="45.67",
            currency="EUR",
            merchant="Coffee Shop",
            category="Food & Dining",
            date="01-05-2023",
            time="12:34 PM",
            account="Wise"
        )

        # Call the function
        result = process_emails(services=services)

        # Check that messages were searched
        mock_search.assert_called_once_with(mock_service)

        # Check that emails were parsed (once for each message)
        self.assertEqual(mock_parse.call_count, 2)

        # Check that transactions were processed
        self.assertEqual(mock_process.call_count, 2)

        # Check result
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Transaction)

    @patch('autospendtracker.main.search_messages')
    def test_process_emails_no_messages(self, mock_search):
        """Test processing when no emails are found."""
        mock_client = MagicMock()
        mock_service = MagicMock()
        services = ServiceBundle(
            ai_client=mock_client,
            gmail_service=mock_service,
            label_id=None,
            label_name="AutoSpendTracker/Processed"
        )

        # Mock no messages found
        mock_search.return_value = []

        # Call the function
        result = process_emails(services=services)

        # Check result
        self.assertEqual(result, [])

    @patch('autospendtracker.main.append_to_sheet')
    @patch('autospendtracker.main.save_transaction_data')
    @patch('autospendtracker.main.process_emails')
    def test_run_pipeline_success(self, mock_process_emails, mock_save, mock_append):
        """Test successful pipeline run."""
        # Mock processed data
        mock_transactions = [
            Transaction(
                amount="45.67",
                currency="EUR",
                merchant="Coffee Shop",
                category="Food & Dining",
                date="01-05-2023",
                time="12:34 PM",
                account="Wise"
            )
        ]
        mock_process_emails.return_value = mock_transactions

        # Call the function
        result = run_pipeline(save_to_file=True, upload_to_sheets=True)

        # Check that emails were processed
        mock_process_emails.assert_called_once()

        # Check that data was saved
        mock_save.assert_called_once()

        # Check that data was uploaded
        mock_append.assert_called_once()

        # Check result
        self.assertEqual(len(result), 1)

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
