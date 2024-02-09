# Smart Auto Spend Tracker!

## Introduction

Hola! I'm thrilled to share a special project that made my life in Mexico simpler and more fun. Moving from Europe, I found myself juggling expenses across different currencies – day-to-day costs in MXN Peso, some in EURO, and subscriptions in Dollars. It was the perfect opportunity to blend some Python, Cloud, and power of AI to craft a auto-spending tracker.

## Project Overview

This is a tool I built to track, categorize, and monitor my spending from multiple accounts, starting with Wise & PayPal, which I use the most. It utilizes Google Vertex AI 'Gemini Pro' to process and analyze my transaction data.

![Technical Workflow](/workflow.png)
*This is the general workflow of the project.*

## How It Works

1. **Transaction Notification:** The moment I use Wise or PayPal, they send an email notification and a new entry is added to my google sheet. This entry includes date, time, merchant, amount, currency, account and category generated by AI - all in realtime. What kicks this whole thing off is an email. 

Instead of giving up my banking credentials to other apps (which can be highly insecure), I set my banks up to send me an email for any transaction over the minimum limit! 
2. **Function Trigger:** The Gmail API listens for new emails and triggers a parsing function.
3. **Data Enrichment:** Gemini Pro enriches the transaction data and categorizes the expense.
4. **Google Sheets Update:** The final data is automatically updated in Google Sheets for easy tracking and analysis.

## Features

- **Multi-Currency Support:** Seamlessly handles MXN, EUR, and USD.
- **Automated Tracking:** Integrates with email notifications for transaction alerts.
- **Intelligent Categorization:** Leverages AI to categorize expenses.
- **Google Sheets Integration:** Presents a neat summary of expenses with details.
- **Open Source:** Shared with the community to inspire and innovate together.

## Contact

This took me 3 weekends to figure out and setup, hopefully with this code you can make it work in even less time! If you're curious about the project, want to contribute, or just say 'hola', feel free to reach out!

- **Email:** [Email](babak.barghi@gmail.com)
- **LinkedIn:** [LinkdeIn]([https://linkedin.com/in/yourusername](https://www.linkedin.com/in/babakbarghi/)https://www.linkedin.com/in/babakbarghi/)
