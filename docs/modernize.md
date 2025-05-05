# Modernization Guide: AutoSpendTracker

This guide outlines steps to modernize the AutoSpendTracker project, enhancing its structure, security, maintainability, and leveraging modern Python tooling.

## 1. Dependency Management with UV & `pyproject.toml` [COMPLETED]

Dependencies have been migrated to `pyproject.toml` and are managed using `uv`.

Migrate from `requirements.txt` to `pyproject.toml` managed by `uv` for faster and more unified dependency management and project tooling configuration.

**Benefits:**

* **Speed:** `uv` is significantly faster than `pip` and `venv`.
* **Unified Tool:** Handles virtual environments, package installation, locking, linting, formatting, etc.
* **Standardization:** `pyproject.toml` is the modern standard for Python project configuration.

**Steps:**

1. **Install UV:** Follow instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).
2. **Create `pyproject.toml`:** Create a `pyproject.toml` file in the project root.

    ````toml
    # filepath: pyproject.toml
    [project]
    name = "autospendtracker"
    version = "1.0.0" # Or your desired starting version
    description = "Automated expense tracking using Gmail and Vertex AI."
    requires-python = ">=3.13"
    dependencies = [
        "google-auth-oauthlib>=1.0.0",
        "google-auth-httplib2>=0.1.0",
        "google-api-python-client>=2.0.0",
        "google-cloud-aiplatform>=1.64.0", # Check for latest compatible version
        "beautifulsoup4>=4.9.0",
        "python-dotenv>=0.19.0",
        "requests>=2.25.0", # Often a transitive dependency, but good to list if used directly
        "tenacity>=8.0.0",
        # Add security dependencies later:
        # "google-cloud-secret-manager>=2.0.0",
        # "cryptography>=3.4.7",
    ]

    [project.optional-dependencies]
    dev = [
        "ruff", # For linting and formatting
        "mypy", # For type checking
        "pytest", # For testing
    ]

    # Optional: Configure UV tool settings if needed
    # [tool.uv]
    # ...
    ````

3. **Remove `requirements.txt`:** Delete the old `requirements.txt` file.
4. **Create Virtual Environment with UV:**

    ````bash
    uv venv
    ````

5. **Activate Environment:**
    * Windows: `.venv\Scripts\activate`
    * Linux/macOS: `source .venv/bin/activate`
6. **Install Dependencies:**

    ````bash
    # Install main dependencies
    uv pip install -e .

    # Install development dependencies
    uv pip install -e ".[dev]"
    ````

    *(The `-e .` installs the project in editable mode, necessary if using a `src` layout)*

## 2. Project Structure Refactoring [COMPLETED]

The project has been restructured to use the `src` layout. Source code now resides in `src/autospendtracker`.

Adopt a standard `src` layout for better organization and clarity.

**Proposed Structure:**

```
AutoSpendTracker/
├── .venv/                  # Virtual environment (managed by uv)
├── docs/
│   └── technical_doc.md
├── images/
│   └── Workflow.png
├── src/
│   └── autospendtracker/     # Main package directory
│       ├── __init__.py
│       ├── api.py            # Core AI processing logic
│       ├── config.py         # Configuration loading (optional refactor)
│       ├── email_parser.py   # Refactored from fetch_mails.py
│       ├── google_auth.py    # Refactored from gmail_auth.py
│       ├── models.py         # Pydantic models for validation (new)
│       ├── sheets.py         # Refactored from sheets_integration.py
│       └── main.py           # Main execution script / entry point
├── tests/                  # Unit and integration tests
│   └── __init__.py
│   └── test_*.py
├── .env.example
├── .gitignore
├── pyproject.toml          # Replaces requirements.txt
├── README.md
├── SECURITY.md
├── sheet.gs
└── ASTservice.json         # Service account key (consider securing)
└── credentials.json        # OAuth credentials (consider securing)
└── token.pickle            # Token cache (generated)
└── transaction_data.json   # Intermediate data (consider removing/securing)
```

**Steps:**

1. Create the `src/autospendtracker/` directory.
2. **[COMPLETED]** Moved `.py` files (`api.py`, `fetch_mails.py`, `gmail_auth.py`, `sheets_integration.py`) into `src/autospendtracker/`.
3. **[COMPLETED]** Renamed files: `fetch_mails.py` -> `email_parser.py`, `gmail_auth.py` -> `google_auth.py`, `sheets_integration.py` -> `sheets.py`. (`api.py` remains `api.py` but moved).
4. Create `src/autospendtracker/__init__.py`.
5. **[COMPLETED]** Created `src/autospendtracker/main.py` as the main entry point, orchestrating calls to other modules. The `if __name__ == '__main__':` logic from the old root-level scripts was consolidated here.
6. **[COMPLETED]** Updated all relative imports within the moved Python files to use the `src/autospendtracker` package structure (e.g., `from .email_parser import parse_email`).
7. Create the `tests/` directory for future tests.

## 4. Modernizing AI Interaction

Improve the robustness and reliability of the interaction with the Vertex AI Gemini model.

**Steps:**

1. **Refine Prompt Engineering (`src/autospendtracker/api.py` -> `create_prompt`):**
    * **Clarity & Specificity:** Ensure instructions are unambiguous.
    * **Few-Shot Examples (Optional):** Include 1-2 examples of input text and desired JSON output directly within the prompt to guide the model better.
    * **JSON Schema Definition:** Consider providing a JSON schema definition within the prompt to reinforce the structure.
2. **Robust Output Validation (Pydantic):**
    * Define a Pydantic model representing the expected transaction JSON structure.
    * Parse the cleaned AI JSON response into this Pydantic model. This provides much stronger validation than manual checks.
    * Create `src/autospendtracker/models.py`.

    ````python
    # filepath: src/autospendtracker/models.py
    from pydantic import BaseModel, Field, field_validator
    from typing import Literal
    import re
    from datetime import datetime

    ALLOWED_CATEGORIES = Literal[
        "Transport", "Food & Dining", "Travel", "Home",
        "Utilities", "People", "Shopping", "Grocery", "Other"
    ]

    class Transaction(BaseModel):
        amount: str = Field(pattern=r'^\d+\.\d{2}$')
        currency: str = Field(min_length=3, max_length=3) # Basic check, could add pattern
        merchant: str
        category: ALLOWED_CATEGORIES
        date: str # DD-MM-YYYY
        time: str # HH:MM AM/PM
        account: Literal["Wise", "PayPal"] # Or make more flexible if needed

        @field_validator('date')
        def validate_date_format(cls, v):
            try:
                datetime.strptime(v, '%d-%m-%Y')
            except ValueError:
                raise ValueError('Invalid date format, expected DD-MM-YYYY')
            return v

        @field_validator('time')
        def validate_time_format(cls, v):
            if not re.match(r'^(0?[1-9]|1[0-2]):[0-5][0-9] [AP]M$', v):
                 raise ValueError('Invalid time format, expected HH:MM AM/PM')
            return v

        @field_validator('currency')
        def uppercase_currency(cls, v):
            return v.upper()
    ````

    * Update `process_transaction` in `src/autospendtracker/api.py` to use this model:

    ````python
    # filepath: src/autospendtracker/api.py (Updated Usage)
    # ... other imports ...
    from .models import Transaction # Assuming models.py is in the same directory

    def process_transaction(...) -> Optional[List[str]]:
        # ... (get model_response, clean it) ...
        try:
            cleaned_response = clean_json_response(model_response)
            raw_data = json.loads(cleaned_response)

            # Apply category hints BEFORE validation if they might affect the category field
            merchant = raw_data.get('merchant', '')
            for key, category in CATEGORY_HINTS.items():
                 if key.lower() in merchant.lower():
                     raw_data['category'] = category
                     break

            # Validate using Pydantic
            transaction_data = Transaction(**raw_data)

            # Convert Pydantic model back to list for Sheets
            return [
                transaction_data.date,
                transaction_data.time,
                transaction_data.merchant,
                transaction_data.amount,
                transaction_data.currency,
                transaction_data.category,
                transaction_data.account,
            ]
        except (json.JSONDecodeError, ValidationError) as e: # ValidationError from Pydantic
            logger.error(f"Data processing/validation error: {str(e)}")
            logger.debug(f"Raw response: {model_response}")
            logger.debug(f"Cleaned response: {cleaned_response}")
            return None
        # ...
    ````

3. **Improved Error Handling:**
    * When `process_transaction` fails validation, consider logging the raw input and output to a separate file/location for later analysis or reprocessing.

## 5. Improving Code Quality & Maintainability

Integrate standard Python development tools.

**Steps:**

1. **Linting & Formatting (Ruff):**
    * Add `ruff` to `[project.optional-dependencies].dev` in `pyproject.toml`.
    * Configure `ruff` in `pyproject.toml`:

        ````toml
        # filepath: pyproject.toml
        # ... other sections ...

        [tool.ruff]
        line-length = 88 # Or your preferred length
        select = ["E", "W", "F", "I", "UP", "PL", "TID"] # Select rule sets (Error, Warning, Pyflakes, Isort, Pyupgrade, Pylint, Pytest-Style)
        ignore = [] # Add specific rules to ignore if necessary

        [tool.ruff.format]
        quote-style = "double" # Or "single"

        [tool.ruff.lint.isort]
        known-first-party = ["autospendtracker"] # Help isort identify your code
        ````

    * Run formatting: `uv run ruff format .`
    * Run linting: `uv run ruff check . --fix`
2. **Type Checking (Mypy):**
    * Add `mypy` to `[project.optional-dependencies].dev`.
    * Ensure type hints are present and accurate throughout the codebase (`src/autospendtracker/api.py`, `src/autospendtracker/email_parser.py`, `src/autospendtracker/main.py`, etc.).
    * Configure `mypy` in `pyproject.toml`:

        ````toml
        # filepath: pyproject.toml
        # ... other sections ...

        [tool.mypy]
        python_version = "3.9" # Match your requires-python
        warn_return_any = true
        warn_unused_configs = true
        ignore_missing_imports = true # Start with this, gradually reduce by adding stubs
        # Add specific module ignores if needed
        # [[tool.mypy.overrides]]
        # module = "google.*"
        # ignore_missing_imports = true
        ````

    * Run type checking: `uv run mypy src`
3. **Unit Testing (Pytest):**
    * Add `pytest` to `[project.optional-dependencies].dev`.
    * Create test files in the `tests/` directory (e.g., `tests/test_email_parser.py`, `tests/test_api.py`).
    * Write tests for key functions, mocking external dependencies like API calls (using `unittest.mock` or `pytest-mock`).
    * Run tests: `uv run pytest`

## 6. Workflow Integration

Combine the email processing and Sheets upload into a single, streamlined workflow within `main.py`.

**Steps:**

1. **Refactor `src/autospendtracker/sheets.py`:** Remove the `if __name__ == '__main__':` block and ensure `append_to_sheet` is easily importable and callable. (Note: Sheets integration is currently commented out in `main.py`).
2. **Modify `src/autospendtracker/main.py`:**
    * Import `append_to_sheet` from `.sheets` (if uncommenting Sheets integration).
    * After the loop processing emails and collecting `sheet_data`, directly call `append_to_sheet` if `sheet_data` is not empty.
    * The code in `main.py` currently saves data to `transaction_data.json` in the project root. The step to append directly to Sheets and remove this file is **not yet completed**.

    ````python
    # filepath: src/autospendtracker/main.py (Conceptual - Reflects Integrated Workflow)
    import logging
    # ... other necessary imports ...
    from .google_auth import gmail_authenticate # Example import
    from .email_parser import search_messages, parse_email # Example import
    from .api import process_transaction, initialize_vertexai # Example import
    from .sheets import append_to_sheet # Example import
    # from .config import load_config # Example import

    logger = logging.getLogger(__name__)

    def run_tracker():
        try:
            # config = load_config() # Load secure config
            # Initialize services (Vertex AI, Gmail, Sheets) using config
            # vertex_model = initialize_vertexai(...)
            # gmail_service = gmail_authenticate(...)
            # spreadsheet_id = config.SPREADSHEET_ID
            # range_name = config.RANGE_NAME

            sheet_data = []
            messages = search_messages(gmail_service)

            if messages:
                for msg in messages:
                    transaction_info = parse_email(gmail_service, 'me', msg['id'])
                    logger.info(f"Processing transaction: {transaction_info.get('info', 'N/A')}")

                    result = process_transaction(vertex_model, transaction_info)
                    if result:
                        sheet_data.append(result)
            else:
                logger.info("No new transaction messages found")

            # Append data directly to sheets if any was processed
            if sheet_data:
                logger.info(f"Appending {len(sheet_data)} transactions to Google Sheet.")
                # append_to_sheet(spreadsheet_id, range_name, sheet_data) # Pass necessary args
                logger.info("Successfully appended data to Google Sheet.")
            else:
                logger.info("No transactions processed successfully to append.")

        except Exception as e:
            logger.error(f"Critical error during tracker execution: {str(e)}", exc_info=True)

    if __name__ == '__main__':
        # Setup logging configuration (consider moving to a dedicated function)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        run_tracker()

    ````

3. **Update `.gitignore`:** Ensure `transaction_data.json` is still ignored, even though it might not be generated anymore.

## 7. Documentation Update

Update [`README.md`](d:\Tools\GitHub\AutoSpendTracker\README.md) and [`docs/technical_doc.md`](docs/technical_doc.md) to reflect:

* The new project structure.
* The use of `uv` and `pyproject.toml`.
* The integrated workflow in `src/autospendtracker/main.py` (no separate script execution, though Sheets integration is currently optional/commented out).
* The security enhancements (especially the use of Secret Manager).
* Instructions for running the code using the new entry point: `python -m autospendtracker.main` (from the project root).

## Conclusion

By implementing these changes, AutoSpendTracker will become a more robust, secure, maintainable, and modern Python application, easier to manage and extend in the future. Remember to implement these changes incrementally and test thoroughly at each stage.