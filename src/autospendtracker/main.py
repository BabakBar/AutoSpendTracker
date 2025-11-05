"""AutoSpendTracker main module.

This is the main entry point for the AutoSpendTracker application.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from tqdm import tqdm

from autospendtracker.auth import gmail_authenticate
from autospendtracker.mail import search_messages, parse_email, get_or_create_label, add_label_to_message
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

    # Initialize Gmail label for marking processed emails
    label_name = CONFIG.get("GMAIL_LABEL_NAME", "AutoSpendTracker/Processed")
    label_id = get_or_create_label(service, label_name)

    if not label_id:
        logger.warning(f"Failed to get/create label '{label_name}' - emails won't be marked as processed")
        logger.warning("This may result in duplicate processing on subsequent runs")
    else:
        logger.info(f"Using Gmail label: {label_name} (ID: {label_id})")

    # Find transaction emails
    sheet_data = []
    messages = search_messages(service)

    if not messages:
        logger.info("No transaction emails found")
        return sheet_data

    # Process each message with progress bar
    logger.info(f"Processing {len(messages)} emails...")
    for msg in tqdm(messages, desc="Processing emails", unit="email"):
        # CRITICAL: Label email FIRST to prevent duplicate processing if crash occurs
        # This fixes the race condition where crashes before labeling cause duplicates
        if label_id:
            labeled = add_label_to_message(service, msg['id'], label_id)
            if not labeled:
                logger.warning(f"Skipping {msg['id']} - failed to label (won't process to avoid duplicates)")
                continue
            logger.debug(f"Labeled email {msg['id']} as processed")

        # Now safe to process - email is already marked
        transaction_info = parse_email(service, 'me', msg['id'])
        logger.debug(f"Processing transaction: {transaction_info}")

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
        logger.info("=" * 60)
        logger.info("Starting transaction processing pipeline")
        logger.info("=" * 60)

        # Process emails to extract transaction data
        logger.info("Step 1: Processing emails from Gmail...")
        transaction_data = process_emails()

        if not transaction_data:
            logger.warning("No transactions were processed successfully")
            logger.info("Possible reasons:")
            logger.info("  - No transaction emails found in Gmail")
            logger.info("  - Emails found but failed to parse")
            logger.info("  - AI processing failed for all transactions")
            return None

        logger.info(f"Successfully processed {len(transaction_data)} transactions")

        # Save data to file if requested
        if save_to_file:
            logger.info("Step 2: Saving data to local file...")
            save_transaction_data(transaction_data)
            logger.info("✓ Data saved successfully")

        # Upload data to Google Sheets if requested
        if upload_to_sheets:
            logger.info("Step 3: Uploading data to Google Sheets...")
            spreadsheet_id = CONFIG.get("SPREADSHEET_ID")
            range_name = CONFIG.get("SHEET_RANGE", "Sheet1!A2:G")
            append_to_sheet(transaction_data, spreadsheet_id, range_name)
            logger.info("✓ Data uploaded to Google Sheets successfully")

        logger.info("=" * 60)
        logger.info(f"Pipeline completed successfully: {len(transaction_data)} transactions processed")
        logger.info("=" * 60)
        return transaction_data

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Error during pipeline execution: {e}", exc_info=True)
        logger.error("=" * 60)
        return None


def main():
    """Main entry point for the application."""
    # Set up logging based on configured log level
    log_level = CONFIG.get("LOG_LEVEL", "INFO")
    setup_logging(level=getattr(logging, log_level))

    logger.info("Starting AutoSpendTracker")

    # Validate required configuration
    missing_config = []
    if not CONFIG.get("PROJECT_ID"):
        missing_config.append("PROJECT_ID")
    if not CONFIG.get("SPREADSHEET_ID"):
        missing_config.append("SPREADSHEET_ID")

    if missing_config:
        logger.error(f"Missing required configuration: {', '.join(missing_config)}")
        logger.error("Please set these values in your .env file")
        logger.error("Example: PROJECT_ID=your-google-cloud-project-id")
        return

    # Run the pipeline
    result = run_pipeline()

    if result:
        logger.info(f"AutoSpendTracker completed successfully - processed {len(result)} transactions")
    else:
        logger.warning("AutoSpendTracker completed but no transactions were processed")
        logger.info("This could mean: no emails found, or all processing failed")

    logger.info("AutoSpendTracker finished")


if __name__ == '__main__':
    main()