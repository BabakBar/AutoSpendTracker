"""Google Sheets integration module for AutoSpendTracker.

This module handles the integration with Google Sheets for storing transaction data.
"""

import json
import os
from typing import List, Any, Dict
import logging

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request

from autospendtracker.security import get_credential_path

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default environment variables
DEFAULT_SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
DEFAULT_RANGE_NAME = os.getenv('SHEET_RANGE', 'Sheet1!A2:G')

def create_sheets_service(service_account_file: str = None):
    """
    Create a Google Sheets service object with appropriate authentication.
    
    Args:
        service_account_file: Path to the service account JSON file
        
    Returns:
        Google Sheets API service object
    """
    try:
        # Use security module to get the service account file path
        if service_account_file is None:
            service_account_file = get_credential_path(
                'service_account', 
                os.getenv('SERVICE_ACCOUNT_FILE', 'ASTservice.json')
            )
            
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets'],
        )
        credentials.refresh(Request())
        service = build('sheets', 'v4', credentials=credentials)
        return service.spreadsheets()
    except Exception as e:
        logger.error(f"Failed to create Sheets service: {e}")
        raise

def append_to_sheet(
    values: List[List[Any]],
    spreadsheet_id: str = DEFAULT_SPREADSHEET_ID,
    range_name: str = DEFAULT_RANGE_NAME
) -> Dict[str, Any]:
    """
    Append values to a Google Sheet.
    
    Args:
        values: Data to append to the sheet (list of rows)
        spreadsheet_id: ID of the target spreadsheet
        range_name: Range where data should be appended
        
    Returns:
        Result of the append operation
    """
    if not spreadsheet_id:
        raise ValueError("Spreadsheet ID is missing. Set SPREADSHEET_ID environment variable.")
        
    try:
        service = create_sheets_service()
        body = {'values': values}
        result = service.values().append(
            spreadsheetId=spreadsheet_id, 
            range=range_name,
            valueInputOption='USER_ENTERED', 
            body=body
        ).execute()
        
        updated_cells = result.get('updates', {}).get('updatedCells', 0)
        logger.info(f"{updated_cells} cells appended to Google Sheet")
        return result
    except Exception as e:
        logger.error(f"Failed to append data to sheet: {e}")
        raise


def load_transaction_data(file_path: str = 'transaction_data.json') -> List[List[Any]]:
    """
    Load transaction data from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing transaction data
        
    Returns:
        Data as a list of rows for appending to a sheet
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load transaction data from {file_path}: {e}")
        raise