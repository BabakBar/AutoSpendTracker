# Smart Auto Spend Tracker

## Intro

Happy to share this project that made my life in Mexico simpler and more fun. Moving from Europe, I found myself spending across different currencies – day-to-day costs in MXN Peso, some in EURO, and subscriptions in Dollars. It was a nice opportunity to blend some Python, Cloud, and power of AI to craft an auto-spending tracker.

## Project Overview

This is a tool I built to track, categorize, and monitor my spending from multiple accounts, starting with Wise & PayPal, which I use the most. It utilizes Google Gen AI SDK with the Gemini model to process and analyze transaction data. AutoSpendTracker is a Python application that automatically extracts and categorizes expense data from your email notifications and adds them to a Google Sheets spreadsheet.

*Overall, this is how the entire project works.*

![Workflow](/images/Workflow.png)

## Installation

### Prerequisites

- Python 3.13
- Google Cloud Platform account with:
  - Google Gen AI API enabled
  - Gmail API enabled
  - Google Sheets API enabled
- Valid OAuth 2.0 credentials for Gmail and Sheets
- Service Account credentials for Gen AI

### Setup Steps

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/AutoSpendTracker.git
   cd AutoSpendTracker
   ```

2. Set up a virtual environment:

   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install using UV (recommended) or pip:

   ```bash
   # Using UV
   uv pip install -e .
   
   # Using standard pip
   pip install -e .
   ```

4. Set up your Google Cloud credentials:
   - Place your OAuth credentials in `credentials.json`
   - Place your service account key in `ASTservice.json`

5. Configure environment variables (create a `.env` file):

   ```
   PROJECT_ID=your-google-cloud-project-id
   SPREADSHEET_ID=your-google-sheets-spreadsheet-id
   MODEL_NAME=gemini-2.0-flash-lite-001
   ```

6. Run the application:

   ```bash
   python run_app.py
   ```

## Project Structure

```
AutoSpendTracker/
├── src/
│   └── autospendtracker/      # Main package
│       ├── __init__.py        # Package initialization
│       ├── ai.py              # AI model integration (Google Gen AI)
│       ├── auth.py            # Authentication logic
│       ├── mail.py            # Email processing
│       ├── main.py            # Core application logic
│       ├── models.py          # Data models
│       ├── security.py        # Security utilities
│       ├── sheets.py          # Google Sheets integration
│       └── config/            # Configuration modules
│           ├── __init__.py
│           ├── app_config.py  # Application configuration
│           └── logging_config.py  # Logging configuration
├── tests/                     # Test modules
├── docs/                      # Documentation
├── images/                    # Images for documentation
├── run_app.py                 # Application entry point
├── pyproject.toml             # Project metadata and dependencies
└── README.md                  # Documentation
```

## Features

- **Automatic Email Processing:** Scans your Gmail for transaction notifications
- **AI-Powered Categorization:** Uses Google's Gen AI (Gemini) to intelligently categorize transactions
- **Currency Support:** Handles multiple currencies (USD, EUR, MXN, etc.)
- **Google Sheets Integration:** Automatically populates a spreadsheet for tracking
- **Configurable:** Easy to customize for different email formats and accounts

## Recent Improvements

- **Google Gen AI SDK:** Updated to use the latest Gemini 2.0 Flash model
- **Modernized Project Structure:** Standard src layout and modular organization
- **Dependency Management:** Using pyproject.toml with UV for faster dependency management
- **Enhanced Logging:** Centralized logging configuration with file rotation
- **Code Quality:** Type hints, documentation strings, and consistent formatting
- **Command-line Interface:** Flexible CLI with various options
- **Error Handling:** Improved exception handling and logging
- **Documentation:** Updated and expanded documentation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Contact

This took me 3 weekends to figure out and setup, hopefully with this code you can make it work in even less time! If you're curious about the project, want to contribute, or just say 'hola', feel free to reach out!

- **Email:** [babak.barghi@gmail.com](mailto:babak.barghi@gmail.com)
- **LinkedIn:** [LinkedIn](https://www.linkedin.com/in/babakbarghi/)
