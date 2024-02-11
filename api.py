import os
from dotenv import load_dotenv
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from fetch_mails import search_messages, parse_email
from gmail_auth import gmail_authenticate
load_dotenv()

API_ENDPOINT = os.getenv('API_ENDPOINT')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION')

def get_authenticated_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/cloud-platform'],
    )
    credentials.refresh(Request())
    return build('aiplatform', 'v1', credentials=credentials)

def create_prompt(transaction_info):
    prompt_text = (
        "Format the transaction details as JSON according to the specified schema. "
        "Reply with JSON only, no other text. Example: { \"amount\": \"466.40\", "
        "\"currency\": \"MXN\", \"merchant\": \"Old Peter\", \"category\": \"Food & Dining\", \"date\": \"06-02-2024\",\"time\": \"12:57 PM\", \"account\": \"Wise\" }. "
        "\"category\": should be enriched to the common, well-known merchant name without "
        "store-specific, location, or point-of-sale provider info, formatted for legibility. "
        "- \"category\": can only be: \"Transport\", \"Food & Dining\", "
        "\"Travel\", \"Home\", \"Utilities\", \"People\", \"Shopping\", \"Grocery\" or \"Other\" ONLY. "
        "If the category does not match any of these use \"Other\". "
        f"you will see German transaction details from paypal follow the same rules for providing output even if it's in another language."f"{transaction_info}"
    )
    return {
        "contents": [
            {
                "role": "USER",
                "parts": [
                    {
                        "text": prompt_text
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,  
            "topP": 1.0,
            "maxOutputTokens": 8192,
            "stopSequences": [],  
            "candidateCount": 1
        }
    }

def prompt_vertex(api_endpoint, credentials, prompt):
    if not credentials.valid:
        credentials.refresh(Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(api_endpoint, headers=headers, json=prompt)
    
    if response.status_code != 200:
        print(f"Failed to get a valid response: {response.json()}")
        return None
     
    #Parse only the relevant parts of the response
    model_response = response.json()
    relevant_response = []
    for candidate in model_response:
        content_parts = candidate['candidates'][0]['content']['parts']
        for part in content_parts:
            if 'text' in part:
                relevant_response.append(part['text'])

    return relevant_response

if __name__ == '__main__':
    service = gmail_authenticate()
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    sheet_data = []
    messages = search_messages(service)
    
    if messages:
        for msg in messages:
            transaction_info = parse_email(service, 'me', msg['id'])
            if transaction_info['info']:
                prompt = create_prompt(transaction_info)
                
                model_response = prompt_vertex(API_ENDPOINT, credentials, prompt)
                
                if model_response:
                    # Process each part of the model_response
                    complete_response = ''.join(model_response)  # model_response is a list of strings
                    try:
                        # parse the concatenated response string as JSON
                        transaction_data = json.loads(complete_response)
                        print("Parsed transaction data:", transaction_data)
                        
                        # add the parsed transaction data to list for sheet appending
                        sheet_data.append([
                            transaction_data.get('date', ''),
                            transaction_data.get('time', ''),
                            transaction_data.get('merchant', ''),
                            transaction_data.get('amount', ''),
                            transaction_data.get('currency', ''),
                            transaction_data.get('category', ''),
                            transaction_data.get('account', ''),
                        ])
                        
                    except json.JSONDecodeError as e:
                        print("Error decoding JSON:", e)
                else:
                    print('Failed to get a response from the model for the transaction.')
            else:
                print('Transaction details not found.')
    else:
        print('No messages found.')
    with open('transaction_data.json', 'w') as f:
                            json.dump(sheet_data, f)