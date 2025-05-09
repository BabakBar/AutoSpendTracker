# AutoSpendTracker Roadmap

This document outlines planned improvements and features for the AutoSpendTracker project.

## Short-term Goals (Next 3 months)

### Enhancement: Additional Payment Providers

- **PayPal Integration**: Expand email parsing to handle PayPal transaction notifications
- **Credit Card Integration**: Add support for parsing credit card transaction emails
- **Venmo/CashApp Support**: Include popular peer-to-peer payment apps

### Improvement: Character Encoding Handling

- Fix Unicode character handling in transaction details
- Implement proper handling for special characters in merchant names

### Feature: Dashboard Visualization

- Create Google Apps Script for the connected spreadsheet to display:
  - Monthly spending by category
  - Currency breakdown
  - Merchant frequency visualization

### Tech Debt

- Add comprehensive unit tests for all modules
- Implement CI/CD pipeline with GitHub Actions
- Add type checking with mypy

## Medium-term Goals (6-12 months)

### Feature: Local Web Dashboard

- Create a simple Flask/FastAPI web interface
- Implement real-time spending visualization
- Add manual transaction entry capability

### Enhancement: AI Model Improvements

- Fine-tune model prompts for better categorization accuracy
- Implement feedback mechanism to improve AI classifications
- Add spending pattern anomaly detection

### Improvement: Data Security

- Add encryption for stored credentials
- Implement better token refresh mechanism
- Add user authentication for multi-user support

## Long-term Goals (Beyond 12 months)

### Feature: Mobile Application

- Develop companion mobile app (Flutter/React Native)
- Enable push notifications for transactions
- Add receipt scanning capability

### Enhancement: Advanced Analytics

- Implement ML-based spending predictions
- Add budget recommendation features
- Create scheduled reports via email

### Infrastructure: Containerization

- Docker containerization for easy deployment
- Kubernetes support for scalability
- Cloud-hosted version with subscription model

## How to Contribute

If you're interested in working on any of these features or have suggestions for new ones, please:

1. Check the [Issues](https://github.com/yourusername/AutoSpendTracker/issues) to see if someone is already working on it
2. Open a new Issue to discuss your proposed feature or improvement
3. Submit a Pull Request with your implementation

We welcome all contributions and ideas to make AutoSpendTracker better!