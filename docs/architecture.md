# AutoSpendTracker Architecture

## System Overview

AutoSpendTracker is a Python application that automatically extracts expense data from email notifications, categorizes them using AI, and stores them in Google Sheets for tracking.

## High-Level Architecture

```
┌─────────────┐
│   Gmail     │
│   Inbox     │
└──────┬──────┘
       │ Email notifications
       │ (Wise, PayPal)
       ↓
┌──────────────────────────────────────────────────────┐
│               AutoSpendTracker                       │
│                                                      │
│  ┌───────────┐    ┌──────────┐    ┌─────────────┐ │
│  │   Auth    │───→│   Mail   │───→│     AI      │ │
│  │  Module   │    │  Parser  │    │   (Gemini)  │ │
│  └───────────┘    └──────────┘    └──────┬──────┘ │
│                                           │         │
│                                           ↓         │
│                                    ┌──────────────┐ │
│                                    │    Models    │ │
│                                    │ (Validation) │ │
│                                    └──────┬───────┘ │
│                                           │         │
│                                           ↓         │
│                                    ┌──────────────┐ │
│                                    │   Sheets     │ │
│                                    │  Integration │ │
│                                    └──────────────┘ │
└──────────────────────────────────────────────────────┘
                                           │
                                           ↓
                                   ┌───────────────┐
                                   │ Google Sheets │
                                   │  Spreadsheet  │
                                   └───────────────┘
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  run_app.py  →  main.py (orchestration)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ↓               ↓               ↓
┌──────────────┐ ┌─────────────┐ ┌─────────────┐
│   auth.py    │ │   mail.py   │ │    ai.py    │
│              │ │             │ │             │
│ - Gmail      │ │ - Search    │ │ - Init      │
│   Auth       │ │ - Parse     │ │   Model     │
│              │ │ - Extract   │ │ - Process   │
└──────┬───────┘ └──────┬──────┘ └──────┬──────┘
       │                │               │
       │                │               │
       └────────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ↓               ↓               ↓
┌──────────────┐ ┌─────────────┐ ┌─────────────┐
│  models.py   │ │  sheets.py  │ │  config/    │
│              │ │             │ │             │
│ - Transaction│ │ - Append    │ │ - app_config│
│ - Validation │ │ - Service   │ │ - logging   │
└──────────────┘ └─────────────┘ └─────────────┘
        │
        ↓
┌──────────────┐
│ exceptions.py│
│              │
│ - Custom     │
│   Errors     │
└──────────────┘
```

## Data Flow

```
1. Email Retrieval
   ┌──────────────────────────────────────────┐
   │ Gmail API ← auth.py (OAuth2)             │
   │    ↓                                      │
   │ mail.py searches for transaction emails  │
   │    ↓                                      │
   │ Parse email content with BeautifulSoup   │
   └──────────────────────────────────────────┘

2. AI Processing
   ┌──────────────────────────────────────────┐
   │ Transaction text → ai.py                 │
   │    ↓                                      │
   │ Create structured prompt                 │
   │    ↓                                      │
   │ Send to Gemini 2.5 Flash                │
   │    ↓                                      │
   │ Clean and parse JSON response            │
   └──────────────────────────────────────────┘

3. Data Validation
   ┌──────────────────────────────────────────┐
   │ Raw JSON → models.py                     │
   │    ↓                                      │
   │ Pydantic Transaction model validates:    │
   │   - Amount format (XX.XX)                │
   │   - Currency code (3 chars)              │
   │   - Date format (DD-MM-YYYY)             │
   │   - Time format (HH:MM AM/PM)            │
   │   - Category (from allowed list)         │
   │    ↓                                      │
   │ Validated Transaction object             │
   └──────────────────────────────────────────┘

4. Storage
   ┌──────────────────────────────────────────┐
   │ Transaction.to_sheet_row()               │
   │    ↓                                      │
   │ sheets.py formats data                   │
   │    ↓                                      │
   │ Google Sheets API appends row            │
   │    ↓                                      │
   │ Spreadsheet updated                      │
   └──────────────────────────────────────────┘
```

## Module Responsibilities

### Core Modules

| Module | Responsibility | Key Functions |
|--------|---------------|---------------|
| `main.py` | Application orchestration | `run_pipeline()`, `process_emails()` |
| `auth.py` | Gmail authentication | `gmail_authenticate()` |
| `mail.py` | Email retrieval and parsing | `search_messages()`, `parse_email()` |
| `ai.py` | AI model interaction | `initialize_ai_model()`, `process_transaction()` |
| `models.py` | Data validation | `Transaction` (Pydantic model) |
| `sheets.py` | Google Sheets integration | `append_to_sheet()`, `create_sheets_service()` |

### Supporting Modules

| Module | Responsibility |
|--------|---------------|
| `config/app_config.py` | Configuration management |
| `config/logging_config.py` | Logging setup |
| `security.py` | Credential management |
| `exceptions.py` | Custom exception types |

## Configuration Flow

```
.env file
   ↓
config/app_config.py (load_config)
   ↓
CONFIG singleton
   ↓
Used by all modules via get_config_value()
```

## Error Handling

```
Custom Exception Hierarchy:

AutoSpendTrackerError (base)
├── ConfigurationError
├── CredentialError
├── AIModelError
├── EmailParsingError
├── SheetsError
└── TransactionValidationError
```

## External Dependencies

- **Google APIs**: Gmail API, Sheets API, Vertex AI
- **AI Model**: Gemini 2.5 Flash (via Google Gen AI SDK)
- **Authentication**: OAuth2 (Gmail), Service Account (AI, Sheets)
- **Validation**: Pydantic v2
- **HTML Parsing**: BeautifulSoup4
- **Retry Logic**: Tenacity

## Deployment Notes

### Prerequisites
1. Python 3.11+
2. Google Cloud Project with enabled APIs
3. OAuth2 credentials (`credentials.json`)
4. Service account key (`ASTservice.json`)
5. Environment variables in `.env` file

### Environment Variables
- `PROJECT_ID`: Google Cloud project ID
- `SPREADSHEET_ID`: Target Google Sheets ID
- `MODEL_NAME`: AI model name (default: gemini-2.5-flash)
- `LOCATION`: GCP region (default: us-central1)

### Execution
```bash
source .venv/bin/activate
python run_app.py
```
