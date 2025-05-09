# AutoSpendTracker Technical Documentation

## System Architecture

AutoSpendTracker is structured as a modern Python package with the following components:

```
AutoSpendTracker/
├── src/
│   └── autospendtracker/      # Main package directory
│       ├── __init__.py        # Package initialization
│       ├── __main__.py        # Entry point for module execution
│       ├── ai.py              # Google Gen AI integration
│       ├── auth.py            # Google authentication
│       ├── mail.py            # Email processing
│       ├── main.py            # Application orchestration
│       ├── models.py          # Pydantic data models
│       ├── security.py        # Credential security
│       ├── sheets.py          # Google Sheets integration
│       └── config/            # Configuration module
│           ├── __init__.py
│           ├── app_config.py  # Application config
│           └── logging_config.py  # Logging configuration
├── tests/                     # Unit and integration tests
├── docs/                      # Documentation
├── images/                    # Workflow diagrams
├── run_app.py                 # Command-line entry point
└── pyproject.toml             # Project metadata and dependencies
```

## Dependency Management

The project uses UV (from Astral) for dependency management:

- **pyproject.toml**: Defines project metadata and dependencies
- **uv.lock**: Dependency lock file for reproducible builds

To install dependencies:
```
uv pip install -e .
```

## Module Descriptions

### Core Modules

- **main.py**: Orchestrates the application workflow
- **mail.py**: Processes Gmail emails containing transaction data
- **ai.py**: Handles interaction with Google Gen AI for transaction categorization
- **sheets.py**: Manages Google Sheets integration for storing transactions
- **models.py**: Defines Pydantic models for data validation

### Supporting Modules

- **auth.py**: Handles Google authentication for Gmail and Sheets
- **security.py**: Manages credential security and token storage
- **config/**: Configuration management modules

## Data Flow

1. **Authentication**: The application authenticates with Google using OAuth 2.0
2. **Email Retrieval**: Transaction emails are fetched from Gmail
3. **Data Extraction**: Transaction data is extracted from emails
4. **AI Processing**: Google Gen AI analyzes and categorizes transaction data
5. **Data Validation**: Pydantic models validate the structured data
6. **Data Storage**: Validated transactions are appended to Google Sheets

## Authentication

Two types of authentication are used:

1. **OAuth 2.0 (credentials.json)**: For Gmail and Sheets APIs
2. **Service Account (ASTservice.json)**: For Google Gen AI

## Google Gen AI Integration

The application uses the Google Gen AI Python SDK to interact with the Gemini models:

1. **Client Initialization**: Creates a Gen AI client with service account credentials
2. **Model Selection**: Uses the Gemini 2.0 Flash Lite model for efficient processing
3. **Prompt Engineering**: Sends structured prompts for consistent transaction categorization
4. **Response Processing**: Parses and validates the model's JSON responses

## Configuration

Configuration is managed via:

1. **Environment Variables**: Runtime configuration via `.env` file:
   ```
   PROJECT_ID=your-google-cloud-project-id
   SPREADSHEET_ID=your-google-sheets-spreadsheet-id
   MODEL_NAME=gemini-2.0-flash-lite-001
   ```
2. **Configuration Module**: `config/app_config.py` loads and validates configuration

## Execution Flow

When running `run_app.py`:

1. The script initializes logging
2. Authenticates with Gmail API
3. Retrieves transaction emails
4. Initializes Google Gen AI client
5. Processes each transaction email
6. Appends valid transactions to Google Sheets

## Testing

Tests are located in the `tests/` directory:

- **test_auth.py**: Tests authentication functionality
- **test_mail.py**: Tests email processing

Run tests using UV:
```
uv run pytest
```

## Common Issues

### Model Not Found Error

If Gen AI returns a "Model not found" error, check:
1. Google Cloud project has the required APIs enabled (Google Gen AI)
2. The model name is correct and available in your region (currently using `gemini-2.0-flash-lite-001`)
3. Your service account has the necessary permissions

### Authentication Issues

If OAuth authentication fails:
1. Ensure `credentials.json` contains valid OAuth 2.0 credentials
2. Delete `token.pickle` to force re-authentication
3. Verify required API scopes are being requested

### Character Encoding Issues

If you encounter character encoding issues in the logs (UnicodeEncodeError):
1. Set console to UTF-8 mode: `chcp 65001` on Windows
2. Update logging configuration to handle Unicode characters

## Dependency Updates

To update dependencies:
```
uv add <package_name>
```

To update all dependencies:
```
uv lock
uv sync
```