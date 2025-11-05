"""Tests for the models module."""

import unittest
import pytest
from pydantic import ValidationError

from autospendtracker.models import Transaction, ALLOWED_CATEGORIES


class TestTransaction(unittest.TestCase):
    """Test cases for the Transaction model."""

    def test_valid_transaction(self):
        """Test creating a valid transaction."""
        transaction = Transaction(
            amount="45.67",
            currency="EUR",
            merchant="Coffee Shop",
            category="Food & Dining",
            date="01-05-2023",
            time="12:34 PM",
            account="Wise"
        )

        self.assertEqual(transaction.amount, "45.67")
        self.assertEqual(transaction.currency, "EUR")
        self.assertEqual(transaction.merchant, "Coffee Shop")
        self.assertEqual(transaction.category, "Food & Dining")
        self.assertEqual(transaction.date, "01-05-2023")
        self.assertEqual(transaction.time, "12:34 PM")
        self.assertEqual(transaction.account, "Wise")

    def test_currency_uppercase_conversion(self):
        """Test that currency is converted to uppercase."""
        transaction = Transaction(
            amount="10.00",
            currency="usd",
            merchant="Test Merchant",
            category="Shopping",
            date="15-06-2023",
            time="3:45 PM",
            account="PayPal"
        )

        self.assertEqual(transaction.currency, "USD")

    def test_invalid_amount_format(self):
        """Test that invalid amount format raises error."""
        with self.assertRaises(ValidationError):
            Transaction(
                amount="45.6",  # Only one decimal place
                currency="EUR",
                merchant="Coffee Shop",
                category="Food & Dining",
                date="01-05-2023",
                time="12:34 PM",
                account="Wise"
            )

    def test_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with self.assertRaises(ValidationError):
            Transaction(
                amount="45.67",
                currency="EUR",
                merchant="Coffee Shop",
                category="Food & Dining",
                date="2023-05-01",  # Wrong format
                time="12:34 PM",
                account="Wise"
            )

    def test_invalid_time_format(self):
        """Test that invalid time format raises error."""
        with self.assertRaises(ValidationError):
            Transaction(
                amount="45.67",
                currency="EUR",
                merchant="Coffee Shop",
                category="Food & Dining",
                date="01-05-2023",
                time="12:34",  # Missing AM/PM
                account="Wise"
            )

    def test_invalid_category(self):
        """Test that invalid category raises error."""
        with self.assertRaises(ValidationError):
            Transaction(
                amount="45.67",
                currency="EUR",
                merchant="Coffee Shop",
                category="InvalidCategory",
                date="01-05-2023",
                time="12:34 PM",
                account="Wise"
            )

    def test_to_sheet_row(self):
        """Test conversion to sheet row format."""
        transaction = Transaction(
            amount="45.67",
            currency="EUR",
            merchant="Coffee Shop",
            category="Food & Dining",
            date="01-05-2023",
            time="12:34 PM",
            account="Wise"
        )

        row = transaction.to_sheet_row()

        self.assertEqual(len(row), 7)
        self.assertEqual(row[0], "01-05-2023")
        self.assertEqual(row[1], "12:34 PM")
        self.assertEqual(row[2], "Coffee Shop")
        self.assertEqual(row[3], "45.67")
        self.assertEqual(row[4], "EUR")
        self.assertEqual(row[5], "Food & Dining")
        self.assertEqual(row[6], "Wise")

    def test_from_dict(self):
        """Test creating transaction from dictionary."""
        data = {
            "amount": "45.67",
            "currency": "EUR",
            "merchant": "Coffee Shop",
            "category": "Food & Dining",
            "date": "01-05-2023",
            "time": "12:34 PM",
            "account": "Wise"
        }

        transaction = Transaction.from_dict(data)

        self.assertEqual(transaction.amount, "45.67")
        self.assertEqual(transaction.merchant, "Coffee Shop")

    def test_str_representation(self):
        """Test string representation of transaction."""
        transaction = Transaction(
            amount="45.67",
            currency="EUR",
            merchant="Coffee Shop",
            category="Food & Dining",
            date="01-05-2023",
            time="12:34 PM",
            account="Wise"
        )

        str_repr = str(transaction)

        self.assertIn("01-05-2023", str_repr)
        self.assertIn("Coffee Shop", str_repr)
        self.assertIn("45.67", str_repr)
        self.assertIn("EUR", str_repr)


if __name__ == '__main__':
    unittest.main()
