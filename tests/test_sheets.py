"""Tests for the sheets module."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from pathlib import Path

from autospendtracker.sheets import (
    create_sheets_service,
    append_to_sheet,
    load_transaction_data
)
from autospendtracker.exceptions import ConfigurationError


class TestSheets(unittest.TestCase):
    """Test cases for the sheets module."""

    @patch('autospendtracker.sheets.build')
    @patch('autospendtracker.sheets.service_account.Credentials.from_service_account_file')
    @patch('autospendtracker.sheets.get_credential_path')
    def test_create_sheets_service(self, mock_get_cred_path, mock_creds, mock_build):
        """Test creating sheets service."""
        # Mock credential path
        mock_get_cred_path.return_value = "/path/to/service-account.json"

        # Mock credentials
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials

        # Mock build
        mock_service = MagicMock()
        mock_build.return_value.spreadsheets.return_value = mock_service

        # Call the function
        result = create_sheets_service()

        # Check that credentials were loaded
        mock_creds.assert_called_once()

        # Check that service was built
        mock_build.assert_called_once_with('sheets', 'v4', credentials=mock_credentials)

        # Check result
        self.assertEqual(result, mock_service)

    @patch('autospendtracker.sheets.create_sheets_service')
    def test_append_to_sheet_success(self, mock_create_service):
        """Test successful append to sheet."""
        # Mock sheets service
        mock_service = MagicMock()
        mock_create_service.return_value = mock_service

        # Mock successful response
        mock_response = {
            'updates': {
                'updatedCells': 7
            }
        }
        mock_service.values().append().execute.return_value = mock_response

        # Test data
        values = [['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise']]

        # Call the function
        result = append_to_sheet(
            values=values,
            spreadsheet_id='test-spreadsheet-id',
            range_name='Sheet1!A2:G'
        )

        # Check that service was created
        mock_create_service.assert_called_once()

        # Check result
        self.assertEqual(result, mock_response)

    def test_append_to_sheet_no_spreadsheet_id(self):
        """Test that append fails without spreadsheet ID."""
        values = [['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise']]

        with self.assertRaises(ConfigurationError) as context:
            append_to_sheet(values=values, spreadsheet_id=None)

        self.assertIn("Spreadsheet ID", str(context.exception))

    def test_load_transaction_data_success(self):
        """Test successful loading of transaction data."""
        # Create test data
        test_data = [
            ['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise'],
            ['02-05-2023', '3:45 PM', 'Grocery Store', '120.50', 'USD', 'Grocery', 'PayPal']
        ]

        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            # Load the data
            result = load_transaction_data(temp_file)

            # Check result
            self.assertEqual(result, test_data)
            self.assertEqual(len(result), 2)
        finally:
            # Clean up
            Path(temp_file).unlink()

    def test_load_transaction_data_file_not_found(self):
        """Test loading from non-existent file."""
        with self.assertRaises(Exception):
            load_transaction_data('non_existent_file.json')


if __name__ == '__main__':
    unittest.main()
