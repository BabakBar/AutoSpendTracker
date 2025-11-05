"""Email processing module for AutoSpendTracker.

This module handles fetching and parsing transaction emails.
"""

import base64
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import email.utils

from bs4 import BeautifulSoup

from autospendtracker.auth import gmail_authenticate
from autospendtracker.config import CONFIG

# Set up logging (uses centralized configuration from logging_config)
logger = logging.getLogger(__name__)

def get_or_create_label(service, label_name: str) -> Optional[str]:
    """
    Get the ID of a Gmail label, creating it if it doesn't exist.

    Args:
        service: Gmail API service instance
        label_name: Name of the label to get or create

    Returns:
        Label ID if successful, None if error occurs
    """
    try:
        # List all existing labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        # Search for existing label
        for label in labels:
            if label['name'] == label_name:
                logger.info(f"Found existing Gmail label: {label_name} (ID: {label['id']})")
                return label['id']

        # Label doesn't exist, create it
        logger.info(f"Creating new Gmail label: {label_name}")
        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        created = service.users().labels().create(userId='me', body=label_object).execute()
        logger.info(f"Created Gmail label: {label_name} (ID: {created['id']})")
        return created['id']

    except Exception as error:
        logger.error(f"Error getting/creating label '{label_name}': {error}")
        return None

def add_label_to_message(service, msg_id: str, label_id: str) -> bool:
    """
    Add a label to a Gmail message.

    Args:
        service: Gmail API service instance
        msg_id: Message ID to label
        label_id: ID of the label to add

    Returns:
        True if successful, False if error occurs
    """
    try:
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        return True
    except Exception as error:
        logger.error(f"Error adding label to message {msg_id}: {error}")
        return False

def search_messages(service, user_id: str = 'me', days_back: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Search for transaction emails from Wise and PayPal.

    Args:
        service: Gmail API service instance
        user_id: User's email address. Default 'me' refers to authenticated user
        days_back: Number of days to look back. If None, uses EMAIL_DAYS_BACK from config (default: 7)

    Returns:
        List of message objects or None if error occurs
    """
    # Get days_back from config if not provided
    if days_back is None:
        days_back = int(CONFIG.get("EMAIL_DAYS_BACK", 7))

    # Calculate the date to search from
    search_date = datetime.now() - timedelta(days=days_back)
    date_str = search_date.strftime('%Y/%m/%d')

    # Get label name from config
    label_name = CONFIG.get("GMAIL_LABEL_NAME", "AutoSpendTracker/Processed")

    # Build query with date filter and exclude processed emails
    query = (
        f'after:{date_str} AND '
        f'-label:{label_name} AND '
        '((from:noreply@wise.com ("You spent" OR "is now in")) OR '
        '(from:service@paypal.de "Von Ihnen gezahlt"))'
    )
    try:
        logger.info(f"Searching for transaction emails from the last {days_back} days (since {date_str})")
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = response.get('messages', [])
        logger.info(f"Found {len(messages)} transaction emails")
        return messages
    except Exception as error:
        logger.error(f'Error searching messages: {error}')
        return None

def get_email_body(service, user_id: str, msg_id: str) -> Optional[str]:
    """
    Get the HTML body of an email message.
    
    Args:
        service: Gmail API service instance
        user_id: User's email address
        msg_id: Message ID
        
    Returns:
        HTML content of the email or None if error occurs
    """
    try:
        message = service.users().messages().get(
            userId=user_id, 
            id=msg_id, 
            format='full'
        ).execute()

        parts = [message['payload']]
        while parts:
            part = parts.pop()
            if part.get('parts'):
                parts.extend(part['parts'])
            if part.get('mimeType') == 'text/html':
                data = part['body']['data']
                return base64.urlsafe_b64decode(data).decode('utf-8')
        return None
    except Exception as error:
        logger.error(f'Error getting email body: {error}')
        return None

def parse_email(service, user_id: str, msg_id: str) -> Dict[str, Optional[str]]:
    """
    Parse transaction details from an email.
    
    Args:
        service: Gmail API service instance
        user_id: User's email address
        msg_id: Message ID
        
    Returns:
        Dictionary containing transaction details
    """
    transaction_details = {
        'date': None,
        'info': None,
        'account': None
    }

    html_content = get_email_body(service, user_id, msg_id)
    if not html_content:
        logger.error("Failed to get email body")
        return transaction_details

    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    if soup.title:
        soup.title.decompose()
    text_content = soup.get_text(separator=" ", strip=True)
    
    try:
        # Get message metadata
        message = service.users().messages().get(
            userId=user_id, 
            id=msg_id, 
            format='metadata'
        ).execute()
        headers = message['payload']['headers']
        
        # Determine account type from sender
        from_header = next((h for h in headers if h['name'] == 'From'), None)
        if from_header:
            if 'wise.com' in from_header['value']:
                transaction_details['account'] = 'Wise'
            elif 'paypal.de' in from_header['value']:
                transaction_details['account'] = 'PayPal'
                
        # Parse date
        date_header = next((h for h in headers if h['name'] == 'Date'), None)
        if date_header:
            date_tuple = email.utils.parsedate_tz(date_header['value'])
            if date_tuple:
                transaction_details['date'] = datetime.fromtimestamp(
                    email.utils.mktime_tz(date_tuple)
                ).strftime('%d-%m-%Y %I:%M %p')

        # Parse transaction details
        wise_pattern = re.compile(r'You spent ([\d,\.]+) ([A-Z]{3}) at ([^.]+)')
        paypal_pattern = re.compile(
            r'Sie haben ([\d,\.]+) ([A-Z]{3}) (?:an |to )([^.]+) gesendet'
        )

        wise_match = wise_pattern.search(text_content)
        paypal_match = paypal_pattern.search(text_content)

        if wise_match:
            amount, currency, merchant = wise_match.groups()
            transaction_details['info'] = (
                f"You spent {amount} {currency} at {merchant}."
            )
        elif paypal_match:
            amount, currency, merchant = paypal_match.groups()
            # Convert German PayPal format to standard format
            transaction_details['info'] = (
                f"You spent {amount} {currency} at {merchant}."
            )
        
        if transaction_details['info']:
            logger.info(f"Successfully parsed transaction: {transaction_details}")
        else:
            logger.warning("No transaction details found in email")
            
    except Exception as e:
        logger.error(f"Error parsing email: {e}")

    return transaction_details