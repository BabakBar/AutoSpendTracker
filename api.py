import os
import re
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
from fetch_mails import search_messages, parse_email
from gmail_auth import gmail_authenticate
from tenacity import retry, stop_after_attempt, wait_exponential

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION')
SERVICE_ACCOUNT_FILE = 'ASTservice.json'

ALLOWED_CATEGORIES = [
    "Transport", "Food & Dining", "Travel", "Home", 
    "Utilities", "People", "Shopping", "Grocery", "Other"
]

# Category hints for better classification
CATEGORY_HINTS = {
    "OpenRouter": "Utilities",  # Web service
    "Namecheap": "Utilities",   # Domain/hosting service
    "Old Peter": "Food & Dining",  # Restaurant
    "Balam": "Food & Dining",   # Restaurant
    "City Market": "Grocery",   # Supermarket
    "Deckers": "Shopping",      # Retail
    "Mood Up": "Shopping",      # Retail
    "Cosmet": "Shopping",       # Cosmetics/Retail
    "Casa De Los Cirios": "Food & Dining"  # Restaurant
}

def create_prompt(transaction_info: Dict[str, Any]) -> str:
    """
    Creates a prompt for the AI model to format transaction data.
    
    Args:
        transaction_info: Dictionary containing transaction details
        
    Returns:
        Formatted prompt string
    """
    prompt_text = (
        "Format this transaction as a single JSON object. Important rules:\n\n"
        "1. Output MUST be a raw JSON object only - no markdown, no code blocks, no backticks, no extra text\n"
        "2. Field requirements:\n"
        "   - amount: string with exactly 2 decimal places (e.g., \"10.95\", \"466.40\")\n"
        "   - currency: uppercase string (e.g., \"USD\", \"EUR\", \"MXN\")\n"
        "   - merchant: full business name including location if provided\n"
        "   - category: must be exactly one of the allowed categories\n"
        "   - date: string in DD-MM-YYYY format\n"
        "   - time: string in HH:MM AM/PM format\n"
        "   - account: string (e.g., \"Wise\", \"PayPal\")\n\n"
        "3. Allowed categories and their rules:\n"
        "   - Transport: rides, fuel, parking, vehicle services\n"
        "   - Food & Dining: restaurants, cafes, bars, food delivery\n"
        "   - Travel: hotels, flights, tourism activities\n"
        "   - Home: furniture, maintenance, home services\n"
        "   - Utilities: internet, phone, web services, hosting, domains, subscriptions\n"
        "   - People: transfers, gifts, personal services\n"
        "   - Shopping: retail stores, online shopping, general merchandise\n"
        "   - Grocery: supermarkets, food stores, markets\n"
        "   - Other: anything that doesn't fit above categories\n\n"
        "4. Specific merchant categorization:\n"
        "   - Web services (like OpenRouter, Namecheap) -> Utilities\n"
        "   - Restaurants (like Old Peter, Balam) -> Food & Dining\n"
        "   - Retail stores (like Deckers) -> Shopping\n"
        "   - Supermarkets (like City Market) -> Grocery\n\n"
        f"Transaction to format: {transaction_info}"
    )
    return prompt_text

def clean_json_response(response: str) -> str:
    """
    Cleans the model's response to extract only the JSON object.
    
    Args:
        response: Raw response from the model
        
    Returns:
        Cleaned JSON string
    """
    # Remove any markdown code fences and language identifiers
    cleaned = re.sub(r'```(?:json)?\s*', '', response)
    cleaned = cleaned.strip('`').strip()
    
    # Find the JSON object boundaries
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1
    
    if start != -1 and end != -1:
        return cleaned[start:end]
    return cleaned

def validate_transaction_data(data: Dict[str, str]) -> bool:
    """
    Validates the parsed transaction data.
    
    Args:
        data: Dictionary containing transaction data
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['amount', 'currency', 'merchant', 'category', 'date', 'time', 'account']
    
    try:
        # Check all required fields exist
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields. Got: {list(data.keys())}")
            return False
            
        # Validate amount format (number with 2 decimal places)
        amount = float(data['amount'])
        if not re.match(r'^\d+\.\d{2}$', data['amount']):
            logger.error(f"Invalid amount format: {data['amount']}")
            return False
            
        # Validate category
        if data['category'] not in ALLOWED_CATEGORIES:
            logger.error(f"Invalid category: {data['category']}")
            return False
            
        # Validate date format
        datetime.strptime(data['date'], '%d-%m-%Y')
        
        # Validate time format
        if not re.match(r'^(0?[1-9]|1[0-2]):[0-5][0-9] [AP]M$', data['time']):
            logger.error(f"Invalid time format: {data['time']}")
            return False
            
        return True
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error: {str(e)}")
        return False

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def prompt_vertex(model: GenerativeModel, prompt_text: str) -> Optional[str]:
    """
    Sends a prompt to the Vertex AI model with retry logic.
    
    Args:
        model: Initialized Vertex AI model
        prompt_text: The prompt to send
        
    Returns:
        Model's response text or None if failed
    """
    try:
        logger.info("Sending prompt to model")
        response = model.generate_content(
            prompt_text,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
                "top_p": 1.0,
                "top_k": 40
            }
        )
        logger.info("Received response from model")
        return response.text if response.text else None
    except Exception as e:
        logger.error(f"Error getting model response: {str(e)}")
        raise

def process_transaction(model: GenerativeModel, transaction_info: Dict[str, Any]) -> Optional[List[str]]:
    """
    Processes a single transaction through the AI model.
    
    Args:
        model: Initialized Vertex AI model
        transaction_info: Transaction details to process
        
    Returns:
        List of transaction data fields or None if processing failed
    """
    if not transaction_info.get('info'):
        logger.info("No transaction info found")
        return None
        
    prompt = create_prompt(transaction_info)
    model_response = prompt_vertex(model, prompt)
    
    if not model_response:
        logger.error("Failed to get model response")
        return None
        
    try:
        cleaned_response = clean_json_response(model_response)
        transaction_data = json.loads(cleaned_response)
        
        # Apply category hints if available
        merchant = transaction_data.get('merchant', '')
        for key, category in CATEGORY_HINTS.items():
            if key.lower() in merchant.lower():
                transaction_data['category'] = category
                break
        
        if not validate_transaction_data(transaction_data):
            logger.error("Transaction data validation failed")
            return None
            
        return [
            transaction_data.get('date', ''),
            transaction_data.get('time', ''),
            transaction_data.get('merchant', ''),
            transaction_data.get('amount', ''),
            transaction_data.get('currency', ''),
            transaction_data.get('category', ''),
            transaction_data.get('account', ''),
        ]
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.debug(f"Raw response: {model_response}")
        logger.debug(f"Cleaned response: {cleaned_response}")
        return None

if __name__ == '__main__':
    try:
        # Load credentials from the service account file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Initialize Vertex AI with credentials
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        
        # Initialize the Gemini model
        model = GenerativeModel("gemini-1.5-flash-002")
        
        # Initialize Gmail service
        service = gmail_authenticate()
        
        sheet_data = []
        messages = search_messages(service)
        
        if messages:
            for msg in messages:
                transaction_info = parse_email(service, 'me', msg['id'])
                logger.info(f"Processing transaction: {transaction_info}")
                
                result = process_transaction(model, transaction_info)
                if result:
                    sheet_data.append(result)
        else:
            logger.info("No messages found")
        
        # Save the transaction data
        if sheet_data:
            with open('transaction_data.json', 'w') as f:
                json.dump(sheet_data, f, indent=2)
            logger.info(f"Saved {len(sheet_data)} transactions to transaction_data.json")
        else:
            logger.warning("No transactions were processed successfully")
            
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
