"""Tests for the ai module."""

import unittest
from unittest.mock import patch, MagicMock, Mock
import json

from autospendtracker.ai import (
    create_prompt,
    clean_json_response,
    process_transaction,
    initialize_ai_model
)
from autospendtracker.exceptions import ConfigurationError


class TestAI(unittest.TestCase):
    """Test cases for the AI module."""

    def test_create_prompt(self):
        """Test prompt creation with transaction info."""
        transaction_info = {
            'date': '01-05-2023 12:34 PM',
            'info': 'You spent 45.67 EUR at Coffee Shop.',
            'account': 'Wise'
        }

        prompt = create_prompt(transaction_info)

        # Check that prompt contains key elements
        self.assertIn("JSON object", prompt)
        self.assertIn("amount", prompt)
        self.assertIn("currency", prompt)
        self.assertIn("merchant", prompt)
        self.assertIn("category", prompt)
        self.assertIn(str(transaction_info), prompt)

    def test_clean_json_response_with_markdown(self):
        """Test cleaning JSON response with markdown code fences."""
        response = """```json
        {
            "amount": "45.67",
            "currency": "EUR"
        }
        ```"""

        cleaned = clean_json_response(response)

        # Check that markdown is removed
        self.assertNotIn("```", cleaned)
        self.assertIn("amount", cleaned)
        self.assertIn("45.67", cleaned)

    def test_clean_json_response_plain(self):
        """Test cleaning plain JSON response."""
        response = '{"amount": "45.67", "currency": "EUR"}'

        cleaned = clean_json_response(response)

        # Check that JSON is preserved
        self.assertEqual(cleaned.strip(), response.strip())

    def test_clean_json_response_with_extra_text(self):
        """Test cleaning JSON with surrounding text."""
        response = """Here is the transaction:
        {
            "amount": "45.67",
            "currency": "EUR"
        }
        Hope this helps!"""

        cleaned = clean_json_response(response)

        # Check that only JSON is extracted
        self.assertNotIn("Here is", cleaned)
        self.assertNotIn("Hope this", cleaned)
        self.assertIn("amount", cleaned)

    @patch('autospendtracker.ai.prompt_vertex')
    def test_process_transaction_success(self, mock_prompt_vertex):
        """Test successful transaction processing."""
        # Mock AI client
        mock_client = MagicMock()

        # Mock transaction info
        transaction_info = {
            'date': '01-05-2023 12:34 PM',
            'info': 'You spent 45.67 EUR at Coffee Shop.',
            'account': 'Wise'
        }

        # Mock AI response
        mock_response = json.dumps({
            "amount": "45.67",
            "currency": "EUR",
            "merchant": "Coffee Shop",
            "category": "Food & Dining",
            "date": "01-05-2023",
            "time": "12:34 PM",
            "account": "Wise"
        })
        mock_prompt_vertex.return_value = mock_response

        # Call the function
        result = process_transaction(mock_client, transaction_info)

        # Check that result is a list (sheet row)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[3], "45.67")  # amount
        self.assertEqual(result[4], "EUR")    # currency

    @patch('autospendtracker.ai.prompt_vertex')
    def test_process_transaction_no_info(self, mock_prompt_vertex):
        """Test processing transaction with no info."""
        mock_client = MagicMock()
        transaction_info = {'info': None}

        result = process_transaction(mock_client, transaction_info)

        # Should return None when no info
        self.assertIsNone(result)
        mock_prompt_vertex.assert_not_called()

    @patch('autospendtracker.ai.prompt_vertex')
    def test_process_transaction_invalid_json(self, mock_prompt_vertex):
        """Test processing transaction with invalid JSON response."""
        mock_client = MagicMock()
        transaction_info = {
            'info': 'You spent 45.67 EUR at Coffee Shop.',
            'account': 'Wise'
        }

        # Mock invalid JSON response
        mock_prompt_vertex.return_value = "This is not valid JSON"

        result = process_transaction(mock_client, transaction_info)

        # Should return None on JSON error
        self.assertIsNone(result)

    @patch('autospendtracker.ai.service_account.Credentials.from_service_account_file')
    @patch('autospendtracker.ai.genai.Client')
    @patch('autospendtracker.ai.get_credential_path')
    def test_initialize_ai_model(self, mock_get_cred_path, mock_client, mock_creds):
        """Test AI model initialization."""
        # Mock credential path
        mock_get_cred_path.return_value = "/path/to/service-account.json"

        # Mock credentials
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials

        # Mock client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Call the function
        result = initialize_ai_model(
            project_id="test-project",
            location="us-central1"
        )

        # Check that credentials were loaded
        mock_creds.assert_called_once()

        # Check that client was initialized
        mock_client.assert_called_once()

        # Check result
        self.assertEqual(result, mock_client_instance)

    @patch('autospendtracker.ai.get_settings')
    def test_initialize_ai_model_no_project_id(self, mock_get_settings):
        """Test that initialization fails without project ID."""
        # Mock settings to return None for project_id
        mock_settings = MagicMock()
        mock_settings.project_id = None
        mock_settings.location = "us-central1"
        mock_settings.model_name = "gemini-2.5-flash"
        mock_get_settings.return_value = mock_settings

        with self.assertRaises(ConfigurationError) as context:
            initialize_ai_model(project_id=None)

        self.assertIn("PROJECT_ID", str(context.exception))


if __name__ == '__main__':
    unittest.main()
