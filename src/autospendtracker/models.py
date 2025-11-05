"""Data models for AutoSpendTracker.

This module contains Pydantic models for validating and processing data.
"""

from datetime import datetime
import re
from typing import Literal, Optional

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseModel, Field
    from pydantic.validator import validator as field_validator

# Define allowed transaction categories
ALLOWED_CATEGORIES = Literal[
    "Transport", "Food & Dining", "Travel", "Home",
    "Utilities", "People", "Shopping", "Grocery", "Other"
]

class Transaction(BaseModel):
    """Transaction model for validated AI-processed transaction data.
    
    This model provides strong validation for transaction data returned from the AI model.
    """
    
    amount: str = Field(pattern=r'^\d+\.\d{2}$', description="Amount with exactly 2 decimal places")
    currency: str = Field(min_length=3, max_length=3, description="Currency code (e.g., USD)")
    merchant: str = Field(description="Merchant name")
    category: ALLOWED_CATEGORIES = Field(description="Transaction category")
    date: str = Field(description="Date in DD-MM-YYYY format")
    time: str = Field(description="Time in 12-hour format (HH:MM AM/PM)")
    account: Literal["Wise", "PayPal"] = Field(description="Source account")

    @field_validator('date')
    def validate_date_format(cls, v):
        """Validate that the date is in DD-MM-YYYY format."""
        try:
            datetime.strptime(v, '%d-%m-%Y')
        except ValueError:
            raise ValueError('Invalid date format, expected DD-MM-YYYY')
        return v

    @field_validator('time')
    def validate_time_format(cls, v):
        """Validate that the time is in HH:MM AM/PM format.

        Valid hours: 1-12 with or without leading zero
        Examples: "1:30 PM", "01:30 PM", "08:59 PM", "12:00 AM"
        Invalid: "0:30 AM" (hour 0 doesn't exist in 12-hour format)
        """
        # Pattern: (0[1-9]|1[0-2]|[1-9]) allows:
        #   0[1-9] = 01-09 (with leading zero)
        #   1[0-2] = 10, 11, 12
        #   [1-9]  = 1-9 (without leading zero)
        # This rejects "0" but accepts both "8" and "08"
        if not re.match(r'^(0[1-9]|1[0-2]|[1-9]):[0-5][0-9] [AP]M$', v):
            raise ValueError('Invalid time format, expected HH:MM AM/PM (hours 1-12)')
        return v

    @field_validator('currency')
    def uppercase_currency(cls, v):
        """Convert currency code to uppercase."""
        return v.upper()

    def to_sheet_row(self) -> list:
        """Convert the transaction to a row format for Google Sheets.
        
        Returns:
            List of values in the order required for sheet rows
        """
        return [
            self.date,
            self.time,
            self.merchant,
            self.amount,
            self.currency,
            self.category,
            self.account,
        ]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create a Transaction from a dictionary of values.
        
        Args:
            data: Dictionary with transaction data
            
        Returns:
            Validated Transaction instance
        """
        return cls(**data)
        
    def __str__(self) -> str:
        """String representation of the transaction."""
        return f"{self.date} {self.time} - {self.merchant} - {self.amount} {self.currency} - {self.category}"