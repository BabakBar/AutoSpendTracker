"""End-to-End tests for AutoSpendTracker.

These tests validate the complete pipeline from email retrieval to Sheets upload.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import os

from autospendtracker.main import run_pipeline, process_emails


class TestEndToEnd(unittest.TestCase):
    """End-to-end test cases for the complete AutoSpendTracker pipeline."""

    @patch('autospendtracker.main.append_to_sheet')
    @patch('autospendtracker.main.save_transaction_data')
    @patch('autospendtracker.main.process_transaction')
    @patch('autospendtracker.main.parse_email')
    @patch('autospendtracker.main.search_messages')
    @patch('autospendtracker.main.gmail_authenticate')
    @patch('autospendtracker.main.initialize_ai_model')
    @patch('autospendtracker.main.CONFIG')
    def test_complete_pipeline_success(
        self, mock_config, mock_init_ai, mock_gmail_auth,
        mock_search, mock_parse, mock_process,
        mock_save, mock_append
    ):
        """Test the complete pipeline from email retrieval to Sheets upload."""

        # Setup configuration
        mock_config.get.side_effect = lambda key, default=None: {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'MODEL_NAME': 'gemini-2.5-flash',
            'SPREADSHEET_ID': 'test-spreadsheet-id',
            'SHEET_RANGE': 'Sheet1!A2:G',
            'OUTPUT_FILE': 'test_output.json'
        }.get(key, default)

        # Mock AI client
        mock_ai_client = MagicMock()
        mock_init_ai.return_value = mock_ai_client

        # Mock Gmail service
        mock_gmail_service = MagicMock()
        mock_gmail_auth.return_value = mock_gmail_service

        # Mock email messages found
        mock_search.return_value = [
            {'id': 'msg1'},
            {'id': 'msg2'},
            {'id': 'msg3'}
        ]

        # Mock parsed email transactions
        mock_parse.side_effect = [
            {
                'date': '01-05-2023 12:34 PM',
                'info': 'You spent 45.67 EUR at Coffee Shop.',
                'account': 'Wise'
            },
            {
                'date': '02-05-2023 3:45 PM',
                'info': 'You spent 120.50 USD at Grocery Store.',
                'account': 'PayPal'
            },
            {
                'date': '03-05-2023 8:20 AM',
                'info': 'You spent 25.00 MXN at Taco Stand.',
                'account': 'Wise'
            }
        ]

        # Mock AI-processed transactions
        mock_process.side_effect = [
            ['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise'],
            ['02-05-2023', '3:45 PM', 'Grocery Store', '120.50', 'USD', 'Grocery', 'PayPal'],
            ['03-05-2023', '8:20 AM', 'Taco Stand', '25.00', 'MXN', 'Food & Dining', 'Wise']
        ]

        # Mock successful save
        mock_save.return_value = None

        # Mock successful append
        mock_append.return_value = {'updates': {'updatedCells': 21}}

        # Run the complete pipeline
        result = run_pipeline(save_to_file=True, upload_to_sheets=True)

        # Verify the pipeline executed successfully
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

        # Verify AI model was initialized
        mock_init_ai.assert_called_once_with(
            project_id='test-project',
            location='us-central1',
            model_name='gemini-2.5-flash'
        )

        # Verify Gmail authentication
        mock_gmail_auth.assert_called_once()

        # Verify email search
        mock_search.assert_called_once_with(mock_gmail_service)

        # Verify all emails were parsed
        self.assertEqual(mock_parse.call_count, 3)

        # Verify all transactions were processed
        self.assertEqual(mock_process.call_count, 3)

        # Verify data was saved to file
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        self.assertEqual(len(saved_data), 3)

        # Verify data was uploaded to Sheets
        mock_append.assert_called_once()
        sheets_data = mock_append.call_args[0][0]
        self.assertEqual(len(sheets_data), 3)

        # Verify first transaction data
        first_transaction = result[0]
        self.assertEqual(first_transaction[0], '01-05-2023')  # date
        self.assertEqual(first_transaction[2], 'Coffee Shop')  # merchant
        self.assertEqual(first_transaction[3], '45.67')  # amount
        self.assertEqual(first_transaction[5], 'Food & Dining')  # category

    @patch('autospendtracker.main.search_messages')
    @patch('autospendtracker.main.gmail_authenticate')
    @patch('autospendtracker.main.initialize_ai_model')
    @patch('autospendtracker.main.CONFIG')
    def test_pipeline_with_no_emails_found(
        self, mock_config, mock_init_ai, mock_gmail_auth, mock_search
    ):
        """Test pipeline behavior when no transaction emails are found."""

        # Setup configuration
        mock_config.get.side_effect = lambda key, default=None: {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'MODEL_NAME': 'gemini-2.5-flash'
        }.get(key, default)

        # Mock services
        mock_ai_client = MagicMock()
        mock_init_ai.return_value = mock_ai_client
        mock_gmail_service = MagicMock()
        mock_gmail_auth.return_value = mock_gmail_service

        # Mock no emails found
        mock_search.return_value = []

        # Run pipeline
        result = run_pipeline()

        # Verify result is None when no emails found
        self.assertIsNone(result)

        # Verify services were still initialized
        mock_init_ai.assert_called_once()
        mock_gmail_auth.assert_called_once()
        mock_search.assert_called_once()

    @patch('autospendtracker.main.process_transaction')
    @patch('autospendtracker.main.parse_email')
    @patch('autospendtracker.main.search_messages')
    @patch('autospendtracker.main.gmail_authenticate')
    @patch('autospendtracker.main.initialize_ai_model')
    @patch('autospendtracker.main.CONFIG')
    def test_pipeline_with_partial_failures(
        self, mock_config, mock_init_ai, mock_gmail_auth,
        mock_search, mock_parse, mock_process
    ):
        """Test pipeline handles partial failures gracefully."""

        # Setup configuration
        mock_config.get.side_effect = lambda key, default=None: {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'MODEL_NAME': 'gemini-2.5-flash'
        }.get(key, default)

        # Mock services
        mock_ai_client = MagicMock()
        mock_init_ai.return_value = mock_ai_client
        mock_gmail_service = MagicMock()
        mock_gmail_auth.return_value = mock_gmail_service

        # Mock 3 emails found
        mock_search.return_value = [
            {'id': 'msg1'},
            {'id': 'msg2'},
            {'id': 'msg3'}
        ]

        # Mock parsed emails - one with no info
        mock_parse.side_effect = [
            {
                'date': '01-05-2023 12:34 PM',
                'info': 'You spent 45.67 EUR at Coffee Shop.',
                'account': 'Wise'
            },
            {
                'date': None,
                'info': None,  # This one fails
                'account': None
            },
            {
                'date': '03-05-2023 8:20 AM',
                'info': 'You spent 25.00 MXN at Taco Stand.',
                'account': 'Wise'
            }
        ]

        # Mock AI processing - one succeeds, one returns None, one succeeds
        mock_process.side_effect = [
            ['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise'],
            None,  # Second transaction fails to process
            ['03-05-2023', '8:20 AM', 'Taco Stand', '25.00', 'MXN', 'Food & Dining', 'Wise']
        ]

        # Run pipeline
        result = process_emails()

        # Verify only successful transactions are returned
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)  # Only 2 out of 3 succeeded

        # Verify all emails were attempted
        self.assertEqual(mock_parse.call_count, 3)
        self.assertEqual(mock_process.call_count, 3)

    @patch('autospendtracker.main.initialize_ai_model')
    @patch('autospendtracker.main.CONFIG')
    def test_pipeline_initialization_failure(self, mock_config, mock_init_ai):
        """Test pipeline handles initialization failures gracefully."""

        # Setup configuration
        mock_config.get.side_effect = lambda key, default=None: {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'MODEL_NAME': 'gemini-2.5-flash'
        }.get(key, default)

        # Mock AI initialization failure
        mock_init_ai.side_effect = Exception("Failed to initialize AI model")

        # Run pipeline
        result = run_pipeline()

        # Verify pipeline returns None on initialization failure
        self.assertIsNone(result)


class TestEndToEndIntegration(unittest.TestCase):
    """Integration tests with minimal mocking for near-real scenarios."""

    @patch('autospendtracker.sheets.build')
    @patch('autospendtracker.sheets.service_account.Credentials.from_service_account_file')
    @patch('autospendtracker.ai.genai.Client')
    @patch('autospendtracker.ai.service_account.Credentials.from_service_account_file')
    @patch('autospendtracker.auth.build')
    @patch('autospendtracker.auth.InstalledAppFlow.from_client_secrets_file')
    def test_data_transformation_through_pipeline(
        self, mock_gmail_flow, mock_gmail_build,
        mock_ai_creds, mock_ai_client,
        mock_sheets_creds, mock_sheets_build
    ):
        """Test data transformation from raw email to sheet format."""

        # This test validates the data transformation logic
        # without actually calling external APIs

        from autospendtracker.models import Transaction

        # Simulate raw transaction data from AI
        raw_data = {
            "amount": "45.67",
            "currency": "eur",  # lowercase - should be uppercased
            "merchant": "Coffee Shop Downtown",
            "category": "Food & Dining",
            "date": "01-05-2023",
            "time": "12:34 PM",
            "account": "Wise"
        }

        # Validate and transform using Transaction model
        transaction = Transaction.from_dict(raw_data)

        # Verify transformation
        self.assertEqual(transaction.currency, "EUR")  # Uppercased
        self.assertEqual(transaction.amount, "45.67")

        # Convert to sheet row format
        sheet_row = transaction.to_sheet_row()

        # Verify sheet row format
        self.assertEqual(len(sheet_row), 7)
        self.assertEqual(sheet_row[0], "01-05-2023")  # date
        self.assertEqual(sheet_row[1], "12:34 PM")     # time
        self.assertEqual(sheet_row[2], "Coffee Shop Downtown")  # merchant
        self.assertEqual(sheet_row[3], "45.67")        # amount
        self.assertEqual(sheet_row[4], "EUR")          # currency (uppercased)
        self.assertEqual(sheet_row[5], "Food & Dining")  # category
        self.assertEqual(sheet_row[6], "Wise")         # account


if __name__ == '__main__':
    unittest.main()
