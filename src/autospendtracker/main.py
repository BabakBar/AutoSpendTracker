# Main entry point for AutoSpendTracker

import logging
import json
import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

# Import functions from other modules within the package
from .email_parser import search_messages, parse_email
from .google_auth import gmail_authenticate
from .api import process_transaction # Assuming process_transaction is the main function in api.py
from .sheets_integration import append_to_sheet

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv() # Load environment variables from .env file

PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'ASTservice.json') # Default value if not in .env
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = os.getenv('RANGE_NAME', 'Sheet1!A2:G')


def main():
    """Main function to orchestrate the AutoSpendTracker workflow."""
    logger.info("Starting AutoSpendTracker...")
    try:
        # Load credentials from the service account file
        # Ensure SERVICE_ACCOUNT_FILE path is correct relative to project root or absolute
        # If SERVICE_ACCOUNT_FILE is in the root, this should work when run from root
        credentials_path = os.path.join(os.getcwd(), SERVICE_ACCOUNT_FILE)
        if not os.path.exists(credentials_path):
            logger.error(f"Service account file not found at: {credentials_path}")
            # Attempt relative path from script location (less ideal)
            script_dir = os.path.dirname(__file__)
            credentials_path = os.path.join(script_dir, '..', '..', SERVICE_ACCOUNT_FILE) # Go up two levels from src/autospendtracker
            if not os.path.exists(credentials_path):
                 logger.error(f"Service account file also not found relative to script: {credentials_path}")
                 return # Exit if credentials not found

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/gmail.readonly'] # Add necessary scopes
        )

        # Initialize Vertex AI with credentials
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

        # Initialize the Gemini model
        model = GenerativeModel("gemini-1.5-flash-001") # Corrected model name based on common usage

        # Initialize Gmail service using the same credentials logic if possible, or separate auth
        # Assuming gmail_authenticate handles its own credential loading ('credentials.json', 'token.pickle')
        # It might need adjustment based on where those files are located now.
        # For now, assume it finds them relative to the execution directory (project root)
        gmail_service = gmail_authenticate() # Uses google_auth.py

        sheet_data = []
        messages = search_messages(gmail_service) # Uses email_parser.py

        if messages:
            logger.info(f"Found {len(messages)} relevant emails.")
            for msg in messages:
                # Ensure parse_email uses the correct path for its dependencies if any
                transaction_info = parse_email(gmail_service, 'me', msg['id']) # Uses email_parser.py
                if transaction_info and transaction_info.get('info'):
                    logger.info(f"Processing transaction: {transaction_info['info']}")
                    # Ensure process_transaction uses the correct paths for its dependencies
                    result = process_transaction(model, transaction_info) # Uses api.py
                    if result:
                        sheet_data.append(result)
                    else:
                        logger.warning(f"Failed to process transaction from email ID: {msg['id']}")
                else:
                     logger.warning(f"Could not parse transaction info from email ID: {msg['id']}")
        else:
            logger.info("No relevant messages found")

        # Save the transaction data (consider moving this path or making configurable)
        output_file_path = os.path.join(os.getcwd(), 'transaction_data.json')
        if sheet_data:
            with open(output_file_path, 'w') as f:
                json.dump(sheet_data, f, indent=2)
            logger.info(f"Saved {len(sheet_data)} transactions to {output_file_path}")
            # Append data directly to sheets if any was processed
            if sheet_data:
                logger.info(f"Appending {len(sheet_data)} transactions to Google Sheet.")
                append_to_sheet(SPREADSHEET_ID, RANGE_NAME, sheet_data)
                logger.info("Successfully appended data to Google Sheet.")
            else:
                logger.info("No transactions processed successfully to append.")
        else:
            logger.warning("No transactions were processed successfully")

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)

    logger.info("AutoSpendTracker finished.")