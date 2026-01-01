"""AI interaction module for AutoSpendTracker.

This module handles interactions with Google Gen AI for processing transaction data.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import the new Google Gen AI SDK
from google import genai
from google.genai import types
from google.oauth2 import service_account
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from autospendtracker.security import get_credential_path
from autospendtracker.models import Transaction, ALLOWED_CATEGORIES
from autospendtracker.exceptions import AIModelError, CredentialError, ConfigurationError
from autospendtracker.config.settings import get_settings
from autospendtracker.monitoring import track_performance, track_api_call
from autospendtracker.rate_limiter import rate_limit

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Note: Config values are resolved at runtime (not import time) to support dynamic configuration

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


def initialize_ai_model(
    project_id: str = None,
    location: str = None,
    service_account_file: str = None,
    model_name: str = None
) -> Any:
    """
    Initialize the Google Gen AI client.

    Args:
        project_id: Google Cloud project ID (defaults to PROJECT_ID env var)
        location: Google Cloud location (defaults to LOCATION env var or 'us-central1')
        service_account_file: Path to service account JSON file
        model_name: Name of the model to use (defaults to settings.model_name)

    Returns:
        Initialized Google Gen AI client
    """
    # Resolve config at runtime from settings (single source of truth)
    settings = get_settings()
    if project_id is None:
        project_id = settings.project_id
    if location is None:
        location = settings.location
    if model_name is None:
        model_name = settings.model_name

    if not project_id:
        raise ConfigurationError("PROJECT_ID environment variable is required")
    
    # Add diagnostic logging
    logger.debug(f"Initializing AI model with: project_id={project_id}, location={location}, model_name={model_name}")
    
    try:
        # Use security module to get the service account file path
        if service_account_file is None:
            service_account_file = get_credential_path(
                'service_account', 
                os.getenv('SERVICE_ACCOUNT_FILE', 'ASTservice.json')
            )
        
        logger.debug(f"Using service account file: {service_account_file}")
        
        # Load credentials from the service account file
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Initialize Google Gen AI client with Vertex AI integration
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            credentials=credentials
        )
        
        logger.debug(f"Successfully initialized Google Gen AI client with model_name={model_name}")
        return client
    except FileNotFoundError as e:
        logger.error(f"Service account file not found: {e}")
        raise CredentialError(f"Service account file not found: {e}") from e
    except Exception as e:
        logger.error(f"Error initializing AI model: {e}")
        raise AIModelError(f"Failed to initialize AI model: {e}") from e


def create_prompt(transaction_info: Dict[str, Any]) -> str:
    """
    Creates a prompt for the AI model to format transaction data.
    
    Args:
        transaction_info: Dictionary containing transaction details
        
    Returns:
        Formatted prompt string
    """
    # Include categories list for clear reference
    categories_list = ", ".join([f'"{cat}"' for cat in ALLOWED_CATEGORIES.__args__])
    
    # Add example transaction for guidance
    example_transaction = {
        "amount": "24.95",
        "currency": "USD",
        "merchant": "Coffee Shop Downtown",
        "category": "Food & Dining", 
        "date": "15-04-2025",
        "time": "2:30 PM",
        "account": "Wise"
    }
    
    prompt_text = (
        "Format this transaction as a single JSON object. Important rules:\n\n"
        "1. Output MUST be a raw JSON object only - no markdown, no code blocks, no backticks, no extra text\n"
        "2. Field requirements:\n"
        "   - amount: string with exactly 2 decimal places (e.g., \"10.95\", \"466.40\")\n"
        "   - currency: uppercase string (e.g., \"USD\", \"EUR\", \"MXN\")\n"
        "   - merchant: full business name including location if provided\n"
        "   - category: must be exactly one of these categories: " + categories_list + "\n"
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
        f"5. Example of correctly formatted transaction:\n{json.dumps(example_transaction, indent=2)}\n\n"
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@rate_limit(max_calls=60, period=60, name="gemini-api")
@track_api_call("gemini-generate-content")
def prompt_vertex(client: Any, prompt_text: str, model_name: str = None) -> Optional[str]:
    """
    Sends a prompt to the Google Gen AI model with retry logic.

    Args:
        client: Initialized Google Gen AI client
        prompt_text: The prompt to send
        model_name: Name of the model to use (defaults to settings.model_name)

    Returns:
        Model's response text or None if failed
    """
    # Resolve model_name from settings if not provided
    if model_name is None:
        model_name = get_settings().model_name
    try:
        logger.debug("Sending prompt to model")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
                top_p=1.0,
                top_k=40
            )
        )
        logger.debug("Received response from model")
        return response.text if response.text else None
    except Exception as e:
        logger.error(f"Error getting model response: {str(e)}")
        raise AIModelError(f"Failed to get model response: {str(e)}") from e


@track_performance
def process_transaction(client: Any, transaction_info: Dict[str, Any], model_name: str = None) -> Optional[List[str]]:
    """
    Processes a single transaction through the AI model.

    Args:
        client: Initialized Google Gen AI client
        transaction_info: Transaction details to process
        model_name: Name of the model to use (defaults to settings.model_name)

    Returns:
        List of transaction data fields or None if processing failed
    """
    # Resolve model_name from settings if not provided
    if model_name is None:
        model_name = get_settings().model_name
    if not transaction_info.get('info'):
        logger.info("No transaction info found")
        return None
        
    prompt = create_prompt(transaction_info)
    model_response = prompt_vertex(client, prompt, model_name)
    
    if not model_response:
        logger.error("Failed to get model response")
        return None
        
    try:
        cleaned_response = clean_json_response(model_response)
        raw_data = json.loads(cleaned_response)
        
        # Apply category hints if available
        merchant = raw_data.get('merchant', '')
        for key, category in CATEGORY_HINTS.items():
            if key.lower() in merchant.lower():
                raw_data['category'] = category
                break
        
        # Use Pydantic model for validation
        transaction = Transaction.from_dict(raw_data)
        
        # Return the validated data as a list for sheets integration
        return transaction.to_sheet_row()
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.debug(f"Raw response: {model_response}")
        logger.debug(f"Cleaned response: {cleaned_response}")
        return None
    except Exception as e:
        logger.error(f"Transaction validation error: {str(e)}")
        # Log the raw data for debugging purposes
        try:
            logger.debug(f"Raw transaction data: {raw_data}")
        except:
            pass
        return None