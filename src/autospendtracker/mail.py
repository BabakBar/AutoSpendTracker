"""Email processing module for AutoSpendTracker.

This module handles fetching and parsing transaction emails.
"""

import base64
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import email.utils

from bs4 import BeautifulSoup

from autospendtracker.auth import gmail_authenticate

# Set up logging (uses centralized configuration from logging_config)
logger = logging.getLogger(__name__)

def search_messages(service, user_id: str = 'me') -> Optional[List[Dict[str, Any]]]:
    """
    Search for transaction emails from Wise and PayPal.
    
    Args:
        service: Gmail API service instance
        user_id: User's email address. Default 'me' refers to authenticated user
        
    Returns:
        List of message objects or None if error occurs
    """
    query = (
        '(from:noreply@wise.com ("You spent" OR "is now in")) OR '
        '(from:service@paypal.de "Von Ihnen gezahlt")'
    )
    try:
        logger.info("Searching for transaction emails")
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
                ).strftime('%d-%m-%Y %H:%M %p')

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