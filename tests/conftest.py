"""Configuration file for pytest.

This file contains fixtures and setup for pytest.
"""

import sys
import pytest
from pathlib import Path

# Add src directory to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv("PROJECT_ID", "test-project")
    monkeypatch.setenv("SPREADSHEET_ID", "test-spreadsheet-id")
    monkeypatch.setenv("SERVICE_ACCOUNT_FILE", "test-service-account.json")
    
    return {
        "PROJECT_ID": "test-project",
        "SPREADSHEET_ID": "test-spreadsheet-id",
        "SERVICE_ACCOUNT_FILE": "test-service-account.json"
    }

@pytest.fixture
def sample_transaction_info():
    """Sample transaction info for testing."""
    return {
        'date': '01-05-2023 12:34 PM',
        'info': 'You spent 45.67 EUR at Coffee Shop.',
        'account': 'Wise'
    }

@pytest.fixture
def sample_ai_response():
    """Sample AI response for testing."""
    return """
    {
        "amount": "45.67",
        "currency": "EUR",
        "merchant": "Coffee Shop",
        "category": "Food & Dining",
        "date": "01-05-2023",
        "time": "12:34 PM",
        "account": "Wise"
    }
    """