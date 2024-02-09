# Smart Auto Spend Tracker!

## Introduction

Hola! I'm thrilled to share a special project that made my life in Mexico simpler and more fun. Moving from Europe, I found myself juggling expenses across different currencies – day-to-day costs in MXN Peso, some in EURO, and subscriptions in Dollars. It was the perfect opportunity to blend some Python, cloud, and power of AI to craft a auto-spending tracker.

## Project Overview

This is a tool I built to track, categorize, and monitor my spending from multiple accounts, starting with Wise & PayPal, which I use the most. It utilizes Google Vertex AI 'Gemini Pro' to process and analyze my transaction data.

![Technical Workflow](/workflow.png)
*The above diagram illustrates the technical workflow of my project.*

## Features

- **Multi-Currency Support:** Seamlessly handles MXN, EUR, and USD.
- **Automated Tracking:** Integrates with email notifications for transaction alerts.
- **Intelligent Categorization:** Leverages AI to categorize expenses.
- **Google Sheets Integration:** Presents a neat summary of expenses with details.
- **Open Source:** Shared with the community to inspire and innovate together.

## How It Works

1. **Transaction Notification:** Wise & PayPal send an email notification after each transaction.
2. **Function Trigger:** The Gmail API listens for new emails and triggers a parsing function.
3. **Data Enrichment:** Gemini Pro enriches the transaction data and categorizes the expense.
4. **Google Sheets Update:** The final data is automatically updated in Google Sheets for easy tracking and analysis.

## Contact

If you're curious about the project, want to contribute, or just say 'hola', feel free to reach out!

- **Email:** [Email](babak.barghi@gmail.com)
- **LinkedIn:** [LinkdeIn]([https://linkedin.com/in/yourusername](https://www.linkedin.com/in/babakbarghi/)https://www.linkedin.com/in/babakbarghi/)
