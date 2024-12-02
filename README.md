# Smart Auto Spend Tracker

## Intro

happy to share this project that made my life in Mexico simpler and more fun. moving from europe, i found myself spending across different currencies – day-to-day costs in MXN Peso, some in EURO, and subscriptions in Dollars. It was a nice opportunity to blend some Python, Cloud, and power of AI to craft a auto-spending tracker.

## Project Overview

This is a tool i built to track, categorize, and monitor my spending from multiple accounts, starting with Wise & PayPal, which I use the most. It utilizes Google Vertex AI with Gemini Flash model to process and analyze my transaction data.

*Overall, this is how the entire project works.*

![Workflow](/images/Workflow.png)

## Features

- **Multi-Currency/Language Support:** Seamlessly handles MXN, EUR, USD / English, German
- **Automated Tracking:** Integrates with email notifications for transaction alerts
- **Intelligent Categorization:** Leverages AI to categorize & structure expenses
- **Google Sheets Integration:** Presents a neat summary of expenses with details
- **Smart Merchant Recognition:** Automatically categorizes known merchants
- **Robust Error Handling:** Retries on API failures and validates data

## Core Components

1. **Email Processing (`fetch_mails.py`)**
   - Gmail API integration for transaction emails
   - Supports both Wise and PayPal formats
   - Multi-language parsing (English/German)
   - Structured logging for debugging

2. **AI Processing (`api.py`)**
   - Vertex AI Gemini integration
   - Smart merchant categorization
   - Data validation and cleaning
   - Retry mechanism for API calls

3. **Authentication (`gmail_auth.py`)**
   - Secure OAuth2 authentication
   - Token management
   - Service account integration

4. **Google Sheets (`sheets_integration.py`)**
   - Automated spreadsheet updates
   - Custom formatting
   - Real-time sync

## Transaction Categories

The system intelligently categorizes transactions into:

- **Transport:** Rides, fuel, parking
- **Food & Dining:** Restaurants, cafes, food delivery
- **Travel:** Hotels, flights
- **Home:** Furniture, maintenance
- **Utilities:** Internet, web services, subscriptions
- **People:** Transfers, gifts
- **Shopping:** Retail stores, online shopping
- **Grocery:** Supermarkets, food stores
- **Other:** Uncategorized transactions

## Setup Instructions

1. **Prerequisites**
   - Python 3.9 or higher
   - Google Cloud Account
   - Gmail Account
   - Google Sheets Account

2. **Environment Setup**

   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   - Copy `.env.example` to `.env`
   - Set up Google Cloud Project
   - Enable required APIs:
     - Gmail API
     - Google Sheets API
     - Vertex AI API
   - Create service account and download JSON key
   - Update environment variables

4. **Running the Tracker**

   ```bash
   python api.py
   ```

## Project Structure

```
AutoSpendTracker/
├── api.py                 # Main application logic
├── fetch_mails.py         # Email processing
├── gmail_auth.py          # Authentication
├── sheets_integration.py  # Sheets integration
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── README.md             # Documentation
```

## Recent Improvements

- Added smart merchant categorization
- Improved error handling and logging
- Enhanced PayPal transaction parsing
- Added data validation
- Implemented retry mechanism
- Added type hints and documentation

## Next Steps

bunch of stuff!

## Contact

This took me 3 weekends to figure out and setup, hopefully with this code you can make it work in even less time! If you're curious about the project, want to contribute, or just say 'hola', feel free to reach out!

- **Email:** [[Email](mailto:babak.barghi@gmail.com)]
- **LinkedIn:** [[LinkedIn](https://www.linkedin.com/in/babakbarghi/)]
