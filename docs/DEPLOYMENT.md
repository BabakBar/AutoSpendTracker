# AutoSpendTracker - Coolify Deployment Guide

Complete guide for deploying AutoSpendTracker to your VPS using Coolify with Docker Compose, Ofelia scheduler, and email notifications.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Pre-Deployment Setup](#pre-deployment-setup)
- [Coolify Configuration](#coolify-configuration)
- [Deployment Steps](#deployment-steps)
- [Verification & Testing](#verification--testing)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### Required Services

1. **Coolify VPS**
   - Minimum: 2GB RAM, 1 CPU, 20GB storage
   - Docker and Docker Compose installed
   - Coolify installed and accessible

2. **Google Cloud Platform**
   - Project created with billing enabled
   - Gmail API enabled
   - Google Sheets API enabled
   - Google Generative AI API (Gemini) enabled
   - Service Account created with appropriate permissions

3. **Gmail Account**
   - App Password generated (for notifications)
   - OAuth 2.0 credentials (for reading emails)

4. **Google Sheets**
   - Spreadsheet created for transaction data
   - Appropriate permissions granted to Service Account

### Required Files

Before deployment, ensure you have these files ready:

- `credentials.json` - Gmail OAuth 2.0 credentials
- `ASTservice.json` - Google Cloud Service Account key
- `.env.production` - Production environment variables (copy from `.env.production.example`)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Coolify VPS                          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │           Docker Compose Stack                    │ │
│  │                                                   │ │
│  │  ┌──────────────┐      ┌──────────────────────┐ │ │
│  │  │   Ofelia     │─────▶│  AutoSpendTracker    │ │ │
│  │  │  Scheduler   │      │  Application         │ │ │
│  │  │              │      │                      │ │ │
│  │  │ • Cron: Daily│      │ • Python 3.13        │ │ │
│  │  │ • Docker API │      │ • UV package mgr     │ │ │
│  │  └──────────────┘      │ • Apprise notifier   │ │ │
│  │                        └──────────┬───────────┘ │ │
│  │                                   │             │ │
│  │  ┌────────────────────────────────┼─────────┐  │ │
│  │  │         Persistent Volumes     │         │  │ │
│  │  │  • tokens/  (OAuth cache)      │         │  │ │
│  │  │  • logs/    (20-day retention) │         │  │ │
│  │  │  • output/  (transaction data) │         │  │ │
│  │  │  • secrets/ (credentials)      │         │  │ │
│  │  └────────────────────────────────┘         │  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │    External Services         │
          │  • Gmail API                 │
          │  • Google Sheets API         │
          │  • Google Gemini AI          │
          │  • Email SMTP                │
          └──────────────────────────────┘
```

**Key Components:**

- **Ofelia Scheduler**: Docker-native cron scheduler that triggers the application daily
- **AutoSpendTracker App**: Python application that processes emails and updates Google Sheets
- **Persistent Volumes**: Store OAuth tokens, logs, and output data across container restarts
- **Apprise Notifier**: Sends email/webhook notifications on success or failure

---

## Pre-Deployment Setup

### 1. Google Cloud Setup

#### Create Service Account

```bash
# 1. Go to Google Cloud Console
https://console.cloud.google.com/

# 2. Navigate to IAM & Admin > Service Accounts
# 3. Click "Create Service Account"
# 4. Fill in details:
#    Name: autospendtracker
#    Description: Service account for AutoSpendTracker application

# 5. Grant permissions:
#    - Vertex AI User
#    - Service Account User

# 6. Create key:
#    - Click on the service account
#    - Keys tab > Add Key > Create New Key
#    - Choose JSON format
#    - Save as ASTservice.json
```

#### Enable APIs

```bash
# Enable required APIs in your Google Cloud project
gcloud services enable gmail.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

### 2. Gmail OAuth Credentials

#### Create OAuth Client

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Click **Create Credentials > OAuth client ID**
4. Choose **Desktop app** as application type
5. Name it **AutoSpendTracker**
6. Download the JSON file and save as `credentials.json`

#### Generate App Password for Notifications

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** and **Other (Custom name)**
3. Enter **AutoSpendTracker** as the name
4. Click **Generate**
5. Copy the 16-character password (no spaces)
6. Use this for `NOTIFICATION_SMTP_PASSWORD` environment variable

**Important:** Never use your regular Gmail password!

### 3. Google Sheets Setup

#### Create Spreadsheet

1. Create a new Google Sheets spreadsheet
2. Add headers in row 1:
   ```
   Amount | Currency | Merchant | Category | Date | Time | Account
   ```
3. Note the Spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
   ```

#### Grant Service Account Access

1. Open your spreadsheet
2. Click **Share** button
3. Add your service account email: `autospendtracker@your-project.iam.gserviceaccount.com`
4. Grant **Editor** permissions

---

## Coolify Configuration

### 1. Create Application in Coolify

1. Log in to your Coolify dashboard
2. Navigate to **Projects** and select your project (or create new)
3. Click **+ Add New Resource**
4. Select **Docker Compose**
5. Fill in application details:
   - **Name**: AutoSpendTracker
   - **Source**: GitHub
   - **Repository**: `https://github.com/BabakBar/AutoSpendTracker`
   - **Branch**: `claude/productionize-codebase-xxx` (or your deployment branch)
   - **Build Path**: `/`
   - **Docker Compose File**: `docker-compose.yml`

### 2. Configure Environment Variables

Navigate to **Application → Environment Variables** and add all variables from `.env.production.example`:

#### Required Variables

```bash
# Google Cloud
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
SERVICE_ACCOUNT_FILE=/app/secrets/ASTservice.json

# Google Sheets
SPREADSHEET_ID=your-spreadsheet-id
SHEET_RANGE=Sheet1!A2:G

# Application
LOG_LEVEL=INFO
EMAIL_DAYS_BACK=7
GMAIL_LABEL_NAME=AutoSpendTracker/Processed
GMAIL_CREDENTIALS_FILE=/app/secrets/credentials.json

# AI Model
MODEL_NAME=gemini-2.5-flash
MODEL_TEMPERATURE=0.1

# Notifications
NOTIFICATION_ENABLED=true
NOTIFICATION_ON_SUCCESS=true
NOTIFICATION_ON_FAILURE=true
NOTIFICATION_EMAIL=your@email.com
NOTIFICATION_SMTP_HOST=smtp.gmail.com
NOTIFICATION_SMTP_PORT=587
NOTIFICATION_SMTP_USER=your@gmail.com
NOTIFICATION_SMTP_PASSWORD=your-gmail-app-password

# Timezone
TZ=America/Mexico_City
```

**Important:** Mark sensitive values as **Secret** in Coolify:
- `NOTIFICATION_SMTP_PASSWORD`
- Service account file path (if needed)

### 3. Upload Credential Files

#### Method 1: Via Coolify UI (Recommended)

1. Navigate to **Application → Files**
2. Create directory: `/secrets`
3. Upload files:
   - `credentials.json` → `/secrets/credentials.json`
   - `ASTservice.json` → `/secrets/ASTservice.json`
4. Set permissions: **400** (read-only for owner)

#### Method 2: Via SSH/SCP

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Create secrets directory
mkdir -p /path/to/autospendtracker/secrets

# Copy files via SCP (from your local machine)
scp credentials.json user@your-vps-ip:/path/to/autospendtracker/secrets/
scp ASTservice.json user@your-vps-ip:/path/to/autospendtracker/secrets/

# Set permissions
chmod 400 /path/to/autospendtracker/secrets/*.json
```

### 4. Configure Persistent Volumes

Coolify automatically creates named volumes defined in `docker-compose.yml`:

- `autospendtracker_tokens` - OAuth token cache
- `autospendtracker_logs` - Application logs (20-day retention)
- `autospendtracker_output` - Transaction JSON files

No additional configuration needed!

---

## Deployment Steps

### Step 1: Push Code to GitHub

```bash
# Ensure you're on the correct branch
git checkout claude/productionize-codebase-xxx

# Add all changes
git add .

# Commit
git commit -m "feat: Production-ready deployment with Coolify support"

# Push to GitHub
git push origin claude/productionize-codebase-xxx
```

### Step 2: Deploy in Coolify

1. Go to your AutoSpendTracker application in Coolify
2. Click **Deploy** button
3. Coolify will:
   - Clone the repository
   - Build the Docker image (multi-stage build with UV)
   - Start the Docker Compose stack (Ofelia + App)
   - Create persistent volumes
   - Set up networking

### Step 3: Monitor Deployment

Watch the deployment logs in Coolify:

```
Building autospendtracker:latest...
[+] Building 120.5s
 => [builder 1/5] FROM docker.io/library/python:3.13-slim
 => [builder 2/5] COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
 => [builder 3/5] COPY pyproject.toml ./
 => [builder 4/5] RUN uv sync --frozen --no-dev --no-install-project
 => [builder 5/5] COPY src/ ./src/
 => [stage-1 1/4] COPY --from=builder /app/.venv /app/.venv
 => [stage-1 2/4] COPY src/ ./src/
 => [stage-1 3/4] COPY docker/entrypoint.sh docker/healthcheck.sh
 => [stage-1 4/4] RUN mkdir -p /app/logs /app/output /app/tokens
 => exporting to image
 => => naming to autospendtracker:latest

Starting services...
[+] Running 2/2
 ✔ Container autospendtracker-scheduler  Started
 ✔ Container autospendtracker-app        Started

Deployment successful!
```

---

## Verification & Testing

### 1. Check Container Status

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Check running containers
docker ps | grep autospendtracker

# Expected output:
# autospendtracker-scheduler   mcuadros/ofelia:latest    Up 2 minutes
# autospendtracker-app         autospendtracker:latest   Up 2 minutes (healthy)
```

### 2. View Logs

```bash
# Application logs
docker logs autospendtracker-app

# Scheduler logs
docker logs autospendtracker-scheduler

# Follow logs in real-time
docker logs -f autospendtracker-app
```

### 3. Test Manual Run

```bash
# Execute the application manually
docker exec autospendtracker-app python -m autospendtracker

# Expected output:
# [INFO] Starting transaction processing pipeline
# [INFO] Step 1: Processing emails from Gmail...
# Processing emails: 100%|██████████| 15/15 [00:45<00:00]
# [INFO] Successfully processed 15 transactions
# [INFO] Step 2: ✓ Data saved to local file
# [INFO] Step 3: ✓ Data uploaded to Google Sheets
# [INFO] ✓ Pipeline completed: 15 transactions processed
```

### 4. Test Notification System

```bash
# Run the notification test script
docker exec autospendtracker-app python -m autospendtracker.notifier

# Expected output:
# AutoSpendTracker Notification Test
# ==================================================
# ✓ Loaded .env file
#
# ✅ Test notification sent successfully!
#    Check your email/webhook to confirm receipt.
```

Check your email for the test notification!

### 5. Verify Health Check

```bash
# Check container health status
docker inspect autospendtracker-app | grep -A 5 '"Health"'

# Manual health check
docker exec autospendtracker-app /app/docker/healthcheck.sh
echo $?  # Should output: 0 (success)
```

### 6. Verify Cron Schedule

```bash
# Check Ofelia scheduler logs
docker logs autospendtracker-scheduler

# Should show scheduled job:
# [ofelia] Scheduling job: autospendtracker-daily
# [ofelia] Next run: 2025-11-07 00:00:00
```

---

## Monitoring & Maintenance

### Daily Operations

**Automated:**
- ✅ Application runs daily at midnight (via Ofelia)
- ✅ Email notifications sent on success/failure
- ✅ Logs rotated automatically (20-day retention)
- ✅ OAuth tokens refreshed automatically

**Manual (Weekly Review):**
- 📧 Review notification emails for any warnings
- 📊 Verify Google Sheets data accuracy
- 💰 Check API costs are within budget
- 📝 Review logs for unusual patterns

### Accessing Logs

```bash
# View recent logs
docker logs --tail 100 autospendtracker-app

# View logs from specific time
docker logs --since 24h autospendtracker-app

# View persistent logs (inside container)
docker exec autospendtracker-app cat /app/logs/autospendtracker.log

# Copy logs to host
docker cp autospendtracker-app:/app/logs ./logs-backup
```

### Viewing Metrics

Metrics are logged after each run:

```
Performance Metrics:
  Total Runtime: 45.3s
  Emails Processed: 15
  Transactions Extracted: 15
  Gmail API Calls: 18
  Sheets API Calls: 1
  Gemini API Calls: 15
  Total Tokens Used: 2,450
  Estimated Cost: $0.003
```

### Updating the Application

```bash
# 1. Make changes locally
git add .
git commit -m "Update: description"
git push origin your-branch

# 2. Redeploy in Coolify
# Click "Redeploy" button in Coolify UI
# Or wait for auto-deployment if configured

# 3. Monitor deployment
# Watch logs in Coolify dashboard

# 4. Verify new version
docker exec autospendtracker-app python -c "import autospendtracker; print('Version OK')"
```

---

## Troubleshooting

### Common Issues

#### Issue: Container won't start

**Symptoms:**
```
Container autospendtracker-app exits immediately
```

**Diagnosis:**
```bash
# Check container logs
docker logs autospendtracker-app

# Common causes:
# - Missing environment variables
# - Invalid credential files
# - Insufficient permissions
```

**Solution:**
```bash
# 1. Verify environment variables in Coolify
#    Ensure all REQUIRED variables are set

# 2. Check credential files exist
docker exec autospendtracker-app ls -la /app/secrets/

# 3. Verify file permissions
docker exec autospendtracker-app ls -l /app/secrets/*.json
# Should show: -r-------- appuser appuser

# 4. Re-upload credentials if needed
# Via Coolify UI: Application → Files
```

#### Issue: Scheduled job doesn't run

**Symptoms:**
```
No emails received at scheduled time
No logs showing execution
```

**Diagnosis:**
```bash
# Check Ofelia scheduler logs
docker logs autospendtracker-scheduler

# Check if schedule is configured
docker inspect autospendtracker-app | grep ofelia
```

**Solution:**
```bash
# 1. Verify cron expression in docker-compose.yml
# Format: minute hour day month weekday
# Example: 0 0 * * * = Daily at midnight

# 2. Check timezone
docker exec autospendtracker-app date
# Should match your TZ environment variable

# 3. Restart scheduler
docker restart autospendtracker-scheduler

# 4. Manually trigger job to test
docker exec autospendtracker-app python -m autospendtracker
```

#### Issue: Notifications not received

**Symptoms:**
```
Application runs successfully
No email notifications received
```

**Diagnosis:**
```bash
# Test notification system
docker exec autospendtracker-app python -m autospendtracker.notifier

# Check notification configuration
docker exec autospendtracker-app env | grep NOTIFICATION
```

**Solution:**
```bash
# 1. Verify SMTP credentials
#    Ensure NOTIFICATION_SMTP_PASSWORD is correct Gmail App Password

# 2. Check spam folder
#    Notifications might be filtered as spam

# 3. Test SMTP connection manually
docker exec autospendtracker-app python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your@gmail.com', 'your-app-password')
print('SMTP connection successful')
server.quit()
"

# 4. Whitelist sender email
#    Add automation@your-domain.com to contacts

# 5. Check Apprise logs
docker logs autospendtracker-app | grep -i apprise
```

#### Issue: High API costs

**Symptoms:**
```
API costs exceeding budget
Performance metrics show high token usage
```

**Diagnosis:**
```bash
# Check performance logs
docker exec autospendtracker-app cat /app/logs/performance.log

# Look for:
# - Number of API calls
# - Tokens used per call
# - Total estimated cost
```

**Solution:**
```bash
# 1. Reduce EMAIL_DAYS_BACK
#    Process fewer days (e.g., 7 → 3)

# 2. Adjust rate limiting
export API_RATE_LIMIT_CALLS=30
export API_RATE_LIMIT_PERIOD=60

# 3. Enable budget tracking
export DAILY_BUDGET=1.00
export BUDGET_ALERT_THRESHOLD=0.8

# 4. Update environment variables in Coolify
#    Application → Environment Variables

# 5. Redeploy to apply changes
```

#### Issue: OAuth token expired

**Symptoms:**
```
Error: invalid_grant
Authentication failed
```

**Diagnosis:**
```bash
# Check token file exists
docker exec autospendtracker-app ls -la /app/tokens/

# Check token expiration
docker logs autospendtracker-app | grep -i "token"
```

**Solution:**
```bash
# 1. Delete old token
docker exec autospendtracker-app rm -f /app/tokens/gmail-token.json

# 2. Re-run application
#    It will trigger OAuth flow and generate new token
docker exec -it autospendtracker-app python -m autospendtracker

# 3. Follow OAuth URL in logs
#    Visit the URL and authorize the application

# 4. Token will be saved for future runs
```

#### Issue: Disk space full

**Symptoms:**
```
No space left on device
Logs not being written
```

**Diagnosis:**
```bash
# Check disk usage
docker exec autospendtracker-app df -h

# Check log directory size
docker exec autospendtracker-app du -sh /app/logs
```

**Solution:**
```bash
# 1. Clean old logs manually
docker exec autospendtracker-app find /app/logs -name "*.log" -mtime +20 -delete

# 2. Adjust log retention
export LOG_RETENTION_DAYS=10

# 3. Enable log rotation (should be automatic)
docker exec autospendtracker-app cat /app/docker/logrotate.conf

# 4. Clean Docker system
docker system prune -a
```

---

## Advanced Configuration

### Changing Schedule

To change the execution schedule, edit `docker-compose.yml`:

```yaml
labels:
  - "ofelia.job-exec.autospendtracker-daily.schedule=0 0 * * *"
```

**Schedule Examples:**

| Schedule | Description |
|----------|-------------|
| `0 0 * * *` | Daily at midnight |
| `0 */6 * * *` | Every 6 hours |
| `0 9 * * 1` | Every Monday at 9 AM |
| `0 0 1 * *` | First day of each month |
| `*/30 * * * *` | Every 30 minutes |

After changing, redeploy in Coolify.

### Multiple Notification Channels

Add multiple notification channels to the notifier:

```python
# In notifier.py, add additional services:
apobj.add('discord://webhook_id/webhook_token')
apobj.add('slack://token_a/token_b/token_c')
apobj.add('https://your-custom-webhook.com/alert')
```

Supported services: https://github.com/caronc/apprise#supported-notifications

### Custom Email Template

Modify notification body in `src/autospendtracker/notifier.py`:

```python
body = f"""
🎉 Custom Template

Transactions: {transaction_count}
Amount: ${total_amount:.2f}

Your custom message here!
"""
```

### Backup Strategy

#### Automated Backup with Rclone

Add a backup job to `docker-compose.yml`:

```yaml
backup:
  image: rclone/rclone:latest
  volumes:
    - logs:/data/logs:ro
    - tokens:/data/tokens:ro
    - output:/data/output:ro
  environment:
    - RCLONE_CONFIG=/config/rclone.conf
  labels:
    - "ofelia.enabled=true"
    - "ofelia.job-exec.backup-weekly.schedule=0 0 * * 0"
    - "ofelia.job-exec.backup-weekly.command=rclone sync /data remote:autospendtracker-backup"
```

#### Manual Backup

```bash
# Backup volumes
docker run --rm -v autospendtracker_tokens:/data -v $(pwd):/backup ubuntu tar czf /backup/tokens-backup.tar.gz /data
docker run --rm -v autospendtracker_logs:/data -v $(pwd):/backup ubuntu tar czf /backup/logs-backup.tar.gz /data
docker run --rm -v autospendtracker_output:/data -v $(pwd):/backup ubuntu tar czf /backup/output-backup.tar.gz /data

# Backup to cloud storage (example with SCP)
scp *-backup.tar.gz user@backup-server:/backups/autospendtracker/
```

---

## Security Best Practices

### 1. Credentials Management

✅ **DO:**
- Store credentials in Coolify encrypted secrets
- Use read-only mounts for credential files (`/app/secrets:ro`)
- Rotate service account keys every 90 days
- Use Gmail App Passwords (never regular password)

❌ **DON'T:**
- Commit credentials to git repository
- Share `.env` files publicly
- Use root user for application execution
- Expose ports unnecessarily

### 2. Container Security

✅ **Implemented:**
- Non-root user execution (`appuser` UID 1000)
- Minimal base image (Python 3.13-slim)
- Health checks for monitoring
- Read-only filesystem where possible
- Resource limits (CPU, memory)

### 3. Network Security

✅ **Configured:**
- No exposed ports (batch job, not web service)
- Custom Docker network for isolation
- Outbound-only connections (Gmail, Sheets, Gemini)
- No ingress traffic required

### 4. Monitoring & Alerting

✅ **Enabled:**
- Email notifications on failures
- Performance metrics logging
- API cost tracking
- Budget alerts (optional)

---

## Cost Analysis

### Infrastructure Costs

| Component | Cost |
|-----------|------|
| **VPS (Coolify)** | $5-10/month |
| **Gmail API** | Free (1B requests/day quota) |
| **Sheets API** | Free (300 requests/min quota) |
| **Gemini API** | ~$0.003/day (15 transactions) |
| **Gemini API** | ~$0.09/month |

**Total Monthly Cost:** ~$6-11/month

### Optimizing Costs

1. **Reduce API calls**
   - Decrease `EMAIL_DAYS_BACK` (7 → 3 days)
   - Batch process less frequently (daily → weekly)

2. **Use smaller VPS**
   - 1GB RAM sufficient for this workload
   - Can share with other services

3. **Monitor API usage**
   - Enable `DAILY_BUDGET` alerts
   - Review performance metrics weekly

---

## Support & Resources

### Documentation

- [Main README](../README.md)
- [Architecture Documentation](./architecture.md)
- [Technical Documentation](./technical_doc.md)
- [Testing Guide](./testing-guide.md)

### External Resources

- [Coolify Documentation](https://coolify.io/docs)
- [Ofelia Scheduler](https://github.com/mcuadros/ofelia)
- [Apprise Notifications](https://github.com/caronc/apprise)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [Google Cloud AI Platform](https://cloud.google.com/ai-platform)

### Getting Help

If you encounter issues:

1. Check [Troubleshooting](#troubleshooting) section above
2. Review container logs: `docker logs autospendtracker-app`
3. Test components individually (auth, API calls, notifications)
4. Open an issue on GitHub with:
   - Error messages from logs
   - Environment configuration (sanitized)
   - Steps to reproduce

---

## Changelog

### Version 2.0.0 (November 2025)

- ✅ Production-ready Docker deployment
- ✅ Multi-stage build with UV package manager
- ✅ Ofelia scheduler for cron jobs
- ✅ Apprise notification system
- ✅ Comprehensive health checks
- ✅ 20-day log rotation
- ✅ Coolify optimization

### Version 1.0.0 (October 2025)

- Initial release with local development support

---

**Deployment successful? Enjoy automated expense tracking! 🎉**

For questions or feedback, contact: babak.barghi@gmail.com
