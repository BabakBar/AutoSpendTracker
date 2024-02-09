from gmail_auth import gmail_authenticate
from bs4 import BeautifulSoup
import base64
import re
from datetime import datetime
import email.utils

def search_messages(service, user_id='me'):
    query = '(from:noreply@wise.com ("You spent" OR "is now in")) OR (from:service@paypal.de "Von Ihnen gezahlt")'
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = response.get('messages', [])
        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def get_email_body(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()

        parts = [message['payload']]
        while parts:
            part = parts.pop()
            if part.get('parts'):
                parts.extend(part['parts'])
            if part.get('mimeType') == 'text/html':
                data = part['body']['data']
                html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                return html_content
        return ""
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def parse_email(service, user_id, msg_id):
    html_content = get_email_body(service, user_id, msg_id)

    soup = BeautifulSoup(html_content, 'html.parser')
    if soup.title:
        soup.title.decompose()
    text_content = soup.get_text(separator=" ", strip=True)
    
    transaction_details = {
        'date': None,
        'info': None,
        'account': None
    }

    message = service.users().messages().get(userId=user_id, id=msg_id, format='metadata').execute()
    headers = message['payload']['headers']
    
    from_header = next((header for header in headers if header['name'] == 'From'), None)
    if from_header:
        if 'wise.com' in from_header['value']:
            transaction_details['account'] = 'Wise'
        elif 'paypal.de' in from_header['value']:
            transaction_details['account'] = 'PayPal'
            
    date_header = next((header for header in headers if header['name'] == 'Date'), None)
    if date_header:
        date_tuple = email.utils.parsedate_tz(date_header['value'])
        if date_tuple:
            transaction_details['date'] = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple)).strftime('%d-%m-%Y %H:%M %p')

    wise_pattern = re.compile(r'You spent ([\d,\.]+) ([A-Z]{3}) at ([^.]+)')
    paypal_pattern = re.compile(r'Sie haben .* gesendet(?= Ihre)')

    wise_match = wise_pattern.search(text_content)
    paypal_match = paypal_pattern.search(text_content)

    if wise_match:
        amount, currency, merchant = wise_match.groups()
        transaction_details['info'] = f"You spent {amount} {currency} at {merchant}."
    
    elif paypal_match:
        transaction_details['info'] = paypal_match.group(0).strip()


    return transaction_details

# Integration in the main workflow
if __name__ == '__main__':
    service = gmail_authenticate()
    messages = search_messages(service)
    
    if messages:
        for msg in messages:
            transaction_info = parse_email(service, 'me', msg['id'])
            if transaction_info['info']:

                print(transaction_info)
                #print('Date:', transaction_info['date'])
                #print('AI Model Prompt:', transaction_info['info'])
            else:
                print('Transaction details not found.')
    else:
        print('No messages found.')

