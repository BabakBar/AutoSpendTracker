from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re
from datetime import datetime

ALLOWED_CATEGORIES = Literal[
    "Transport", "Food & Dining", "Travel", "Home",
    "Utilities", "People", "Shopping", "Grocery", "Other"
]

class Transaction(BaseModel):
    amount: str = Field(pattern=r'^\d+\.\d{2}$')
    currency: str = Field(min_length=3, max_length=3)
    merchant: str
    category: ALLOWED_CATEGORIES
    date: str
    time: str
    account: Literal["Wise", "PayPal"]

    @field_validator('date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%d-%m-%Y')
        except ValueError:
            raise ValueError('Invalid date format, expected DD-MM-YYYY')
        return v

    @field_validator('time')
    def validate_time_format(cls, v):
        if not re.match(r'^(0?[1-9]|1[0-2]):[0-5][0-9] [AP]M$', v):
             raise ValueError('Invalid time format, expected HH:MM AM/PM')
        return v

    @field_validator('currency')
    def uppercase_currency(cls, v):
        return v.upper()