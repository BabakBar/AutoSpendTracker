"""AutoSpendTracker main module.

This is the main entry point for the AutoSpendTracker application.
"""

import json
import logging
import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from tqdm import tqdm

from autospendtracker.auth import gmail_authenticate
from autospendtracker.mail import search_messages, parse_email, get_or_create_label, add_label_to_message
from autospendtracker.ai import initialize_ai_model, process_transaction
from autospendtracker.models import Transaction
from autospendtracker.sheets import append_to_sheet, load_transaction_data
from autospendtracker.config import setup_logging, get_settings
from autospendtracker.monitoring import track_performance, log_metrics_summary
from autospendtracker.notifier import send_success_notification, send_failure_notification

# Set up logging
logger = logging.getLogger(__name__)

# Check for verbose logging mode
VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', '').lower() in ('true', '1', 'yes')


@dataclass(frozen=True)
class ServiceBundle:
    ai_client: Any
    gmail_service: Any
    label_id: Optional[str]
    label_name: str


def build_services() -> ServiceBundle:
    settings = get_settings()
    client = initialize_ai_model(
        project_id=settings.project_id,
        location=settings.location,
        model_name=settings.model_name
    )

    service = gmail_authenticate()

    label_name = settings.gmail_label_name
    label_id = get_or_create_label(service, label_name)

    if not label_id:
        logger.warning(f"Failed to get/create label '{label_name}' - emails won't be marked as processed")
        logger.warning("This may result in duplicate processing on subsequent runs")
    elif VERBOSE_LOGGING:
        logger.info(f"Using Gmail label: {label_name} (ID: {label_id})")

    return ServiceBundle(
        ai_client=client,
        gmail_service=service,
        label_id=label_id,
        label_name=label_name
    )


def save_transaction_data(data: List[List[str]], file_path: str = None) -> None:
    """
    Save transaction data to a JSON file.
    
    Args:
        data: Transaction data as a list of rows
        file_path: Path to save the JSON file (default from config)
    """
    if file_path is None:
        file_path = get_settings().output_file
        
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        if VERBOSE_LOGGING:
            logger.info(f"Saved {len(data)} transactions to {file_path}")
    except Exception as e:
        logger.error(f"Error saving transaction data: {e}")
        raise


@track_performance
def process_emails(services: Optional[ServiceBundle] = None) -> List[Transaction]:
    """
    Process emails to extract transaction information.

    Returns:
        List of processed transaction data rows
    """
    if services is None:
        services = build_services()

    # Find transaction emails
    sheet_data: List[Transaction] = []
    messages = search_messages(services.gmail_service)

    if not messages:
        logger.info("No transaction emails found")
        return sheet_data

    # Process each message with progress bar
    logger.info(f"Processing {len(messages)} emails...")
    for msg in tqdm(messages, desc="Processing emails", unit="email"):
        # Process first; only mark as processed after a successful transaction
        transaction_info = parse_email(services.gmail_service, 'me', msg['id'])
        logger.debug(f"Processing transaction from message {msg['id']}")

        # Process through AI client
        result = process_transaction(services.ai_client, transaction_info)
        if result:
            sheet_data.append(result)
            if services.label_id:
                labeled = add_label_to_message(services.gmail_service, msg['id'], services.label_id)
                if not labeled:
                    logger.warning(f"Processed {msg['id']} but failed to label as processed")
                else:
                    logger.debug(f"Labeled email {msg['id']} as processed")

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
        transactions = process_emails()

        if not transactions:
            logger.warning("No transactions were processed successfully")
            logger.info("Possible reasons:")
            logger.info("  - No transaction emails found in Gmail")
            logger.info("  - Emails found but failed to parse")
            logger.info("  - AI processing failed for all transactions")
            return None

        logger.info(f"Successfully processed {len(transactions)} transactions")

        sheet_rows = [transaction.to_sheet_row() for transaction in transactions]

        # Save data to file if requested
        if save_to_file:
            if VERBOSE_LOGGING:
                logger.info("Step 2: Saving data to local file...")
            save_transaction_data(sheet_rows)
            if VERBOSE_LOGGING:
                logger.info("✓ Data saved successfully")
            else:
                logger.info("Step 2: ✓ Data saved to local file")

        # Upload data to Google Sheets if requested
        if upload_to_sheets:
            if VERBOSE_LOGGING:
                logger.info("Step 3: Uploading data to Google Sheets...")
            settings = get_settings()
            spreadsheet_id = settings.spreadsheet_id
            range_name = settings.sheet_range
            append_to_sheet(sheet_rows, spreadsheet_id, range_name)
            if VERBOSE_LOGGING:
                logger.info("✓ Data uploaded to Google Sheets successfully")
            else:
                logger.info("Step 3: ✓ Data uploaded to Google Sheets")

        # Use singular/plural correctly
        txn_word = "transaction" if len(sheet_rows) == 1 else "transactions"
        logger.info(f"✓ Pipeline completed: {len(sheet_rows)} {txn_word} processed")

        # Log performance and API metrics summary
        log_metrics_summary()

        return sheet_rows

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
    log_level = get_settings().log_level
    setup_logging(level=getattr(logging, log_level))

    if VERBOSE_LOGGING:
        logger.info("Starting AutoSpendTracker")

    # Validate required configuration
    missing_config = []
    settings = get_settings()
    if not settings.project_id:
        missing_config.append("PROJECT_ID")
    if not settings.spreadsheet_id:
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
                # Amount is the fourth column in the row
                amount_str = transaction_row[3] if len(transaction_row) > 3 else "0.00"
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
