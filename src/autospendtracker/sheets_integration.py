import json
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
load_dotenv()

# The ID and range of the spreadsheet.
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = 'Sheet1!A2:G' 

def sheets_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets'],
    )
    credentials.refresh(Request())
    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()

def append_to_sheet(spreadsheet_id, range_name, values):
    service = sheets_service()
    body = {'values': values}
    result = service.values().append(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()
    print('{0} cells appended.'.format(result.get('updates').get('updatedCells')))
