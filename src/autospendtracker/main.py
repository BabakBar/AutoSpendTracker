"""AutoSpendTracker main module.

This is the main entry point for the AutoSpendTracker application.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from tqdm import tqdm

from autospendtracker.auth import gmail_authenticate
from autospendtracker.mail import search_messages, parse_email, get_or_create_label, add_label_to_message
from autospendtracker.ai import initialize_ai_model, process_transaction
from autospendtracker.sheets import append_to_sheet, load_transaction_data
from autospendtracker.config import setup_logging, get_config, CONFIG
from autospendtracker.monitoring import track_performance, log_metrics_summary
from autospendtracker.notifier import send_success_notification, send_failure_notification

# Set up logging
logger = logging.getLogger(__name__)

# Check for verbose logging mode
VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', '').lower() in ('true', '1', 'yes')


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
        if VERBOSE_LOGGING:
            logger.info(f"Saved {len(data)} transactions to {file_path}")
    except Exception as e:
        logger.error(f"Error saving transaction data: {e}")
        raise


@track_performance
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
    elif VERBOSE_LOGGING:
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


@track_performance
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
        if VERBOSE_LOGGING:
            logger.info("=" * 60)
        logger.info("Starting transaction processing pipeline")
        if VERBOSE_LOGGING:
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
            if VERBOSE_LOGGING:
                logger.info("Step 2: Saving data to local file...")
            save_transaction_data(transaction_data)
            if VERBOSE_LOGGING:
                logger.info("✓ Data saved successfully")
            else:
                logger.info("Step 2: ✓ Data saved to local file")

        # Upload data to Google Sheets if requested
        if upload_to_sheets:
            if VERBOSE_LOGGING:
                logger.info("Step 3: Uploading data to Google Sheets...")
            spreadsheet_id = CONFIG.get("SPREADSHEET_ID")
            range_name = CONFIG.get("SHEET_RANGE", "Sheet1!A2:G")
            append_to_sheet(transaction_data, spreadsheet_id, range_name)
            if VERBOSE_LOGGING:
                logger.info("✓ Data uploaded to Google Sheets successfully")
            else:
                logger.info("Step 3: ✓ Data uploaded to Google Sheets")

        # Use singular/plural correctly
        txn_word = "transaction" if len(transaction_data) == 1 else "transactions"
        logger.info(f"✓ Pipeline completed: {len(transaction_data)} {txn_word} processed")

        # Log performance and API metrics summary
        log_metrics_summary()

        return transaction_data

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Error during pipeline execution: {e}", exc_info=True)
        logger.error("=" * 60)

        # Log metrics even on failure for debugging
        log_metrics_summary()

        return None


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    # Set up logging based on configured log level
    log_level = CONFIG.get("LOG_LEVEL", "INFO")
    setup_logging(level=getattr(logging, log_level))

    if VERBOSE_LOGGING:
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
        return 1

    # Track start time for metrics
    start_time = time.time()

    try:
        # Run the pipeline
        result = run_pipeline()

        if not result:
            logger.warning("No transactions processed")
            if VERBOSE_LOGGING:
                logger.info("This could mean: no emails found, or all processing failed")
            # Don't send notification for "no transactions" - not an error
            return 0

        # Calculate metrics for notification
        runtime = time.time() - start_time
        transaction_count = len(result)

        # Calculate total amount from transactions
        total_amount = 0.0
        for transaction_row in result:
            try:
                # Amount is the first column in the row
                amount_str = transaction_row[0] if len(transaction_row) > 0 else "0.00"
                total_amount += float(amount_str)
            except (ValueError, IndexError):
                pass

        # Get API cost from monitoring (if available)
        # This would need to be extracted from monitoring module
        api_cost = 0.0  # Placeholder - can be enhanced with actual cost tracking

        # Send success notification
        send_success_notification(
            email_count=transaction_count,
            transaction_count=transaction_count,
            total_amount=total_amount,
            runtime=runtime,
            api_cost=api_cost
        )

        logger.info(f"✓ AutoSpendTracker completed successfully in {runtime:.1f}s")
        return 0

    except Exception as e:
        # Calculate runtime even on failure
        runtime = time.time() - start_time

        logger.error("=" * 60)
        logger.error(f"AutoSpendTracker failed: {e}", exc_info=True)
        logger.error("=" * 60)

        # Send failure notification
        send_failure_notification(
            error=e,
            context={
                'runtime': f"{runtime:.1f}s",
                'log_level': log_level,
            }
        )

        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())