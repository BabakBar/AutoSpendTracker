"""AutoSpendTracker main module.

This is the main entry point for the AutoSpendTracker application.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from autospendtracker.auth import gmail_authenticate
from autospendtracker.mail import search_messages, parse_email
from autospendtracker.ai import initialize_ai_model, process_transaction
from autospendtracker.sheets import append_to_sheet, load_transaction_data
from autospendtracker.config import setup_logging, get_config, CONFIG

# Set up logging
logger = logging.getLogger(__name__)


def save_transaction_data(data: List[List[str]], file_path: str = None) -> None:
    """
    Save transaction data to a JSON file.
    
    Args:
        data: Transaction data as a list of rows
        file_path: Path to save the JSON file (default from config)
    """
    if file_path is None:
        file_path = CONFIG.get("OUTPUT_FILE", "transaction_data.json")
        
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} transactions to {file_path}")
    except Exception as e:
        logger.error(f"Error saving transaction data: {e}")
        raise


def process_emails() -> List[List[str]]:
    """
    Process emails to extract transaction information.
    
    Returns:
        List of processed transaction data rows
    """
    # Initialize the AI client
    client = initialize_ai_model(
        project_id=CONFIG.get("PROJECT_ID"),
        location=CONFIG.get("LOCATION"),
        model_name=CONFIG.get("MODEL_NAME")
    )
    
    # Initialize Gmail service
    service = gmail_authenticate()
    
    # Find transaction emails
    sheet_data = []
    messages = search_messages(service)
    
    if not messages:
        logger.info("No transaction emails found")
        return sheet_data
        
    # Process each message
    for msg in messages:
        transaction_info = parse_email(service, 'me', msg['id'])
        logger.info(f"Processing transaction: {transaction_info}")
        
        # Process through AI client
        result = process_transaction(client, transaction_info)
        if result:
            sheet_data.append(result)
    
    return sheet_data


def run_pipeline(save_to_file: bool = True, upload_to_sheets: bool = True) -> Optional[List[List[str]]]:
    """
    Run the full AutoSpendTracker pipeline.
    
    Args:
        save_to_file: Whether to save results to a local JSON file
        upload_to_sheets: Whether to upload results to Google Sheets
        
    Returns:
        Processed transaction data or None if an error occurred
    """
    try:
        # Process emails to extract transaction data
        transaction_data = process_emails()
        
        if not transaction_data:
            logger.warning("No transactions were processed successfully")
            return None
            
        # Save data to file if requested
        if save_to_file:
            save_transaction_data(transaction_data)
            
        # Upload data to Google Sheets if requested
        if upload_to_sheets:
            spreadsheet_id = CONFIG.get("SPREADSHEET_ID")
            range_name = CONFIG.get("SHEET_RANGE", "Sheet1!A2:G")
            append_to_sheet(transaction_data, spreadsheet_id, range_name)
            
        return transaction_data
        
    except Exception as e:
        logger.error(f"Error during pipeline execution: {e}", exc_info=True)
        return None


def main():
    """Main entry point for the application."""
    # Set up logging based on configured log level
    log_level = CONFIG.get("LOG_LEVEL", "INFO")
    setup_logging(level=getattr(logging, log_level))
    
    logger.info("Starting AutoSpendTracker")
    run_pipeline()
    logger.info("AutoSpendTracker completed")


if __name__ == '__main__':
    main()