"""Custom exceptions for AutoSpendTracker.

This module defines application-specific exceptions for better error handling.
"""


class AutoSpendTrackerError(Exception):
    """Base exception for all AutoSpendTracker errors."""
    pass


class ConfigurationError(AutoSpendTrackerError):
    """Raised when there's a configuration error."""
    pass


class CredentialError(AutoSpendTrackerError):
    """Raised when there's an issue with credentials."""
    pass


class AIModelError(AutoSpendTrackerError):
    """Raised when there's an error with the AI model."""
    pass


class EmailParsingError(AutoSpendTrackerError):
    """Raised when there's an error parsing email content."""
    pass


class SheetsError(AutoSpendTrackerError):
    """Raised when there's an error with Google Sheets operations."""
    pass


class TransactionValidationError(AutoSpendTrackerError):
    """Raised when transaction data validation fails."""
    pass
