#!/bin/bash
# ==============================================================================
# AutoSpendTracker Health Check Script
# ==============================================================================
# Purpose: Verify container is healthy and ready to execute jobs
# Runs as: appuser
# Frequency: Every 30 seconds (configured in Dockerfile)
# ==============================================================================

set -e

# Exit codes
# 0: healthy
# 1: unhealthy

# ==============================================================================
# 1. Verify Python is Available
# ==============================================================================
if ! python3 --version > /dev/null 2>&1; then
    echo "UNHEALTHY: Python 3 is not available"
    exit 1
fi

# ==============================================================================
# 2. Verify Credential Files Exist
# ==============================================================================
CREDENTIALS_FILE="${SERVICE_ACCOUNT_FILE:-/app/secrets/ASTservice.json}"
GMAIL_CREDENTIALS="${GMAIL_CREDENTIALS_FILE:-/app/secrets/credentials.json}"

if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "UNHEALTHY: Service account file not found at $CREDENTIALS_FILE"
    exit 1
fi

if [ ! -f "$GMAIL_CREDENTIALS" ]; then
    echo "UNHEALTHY: Gmail credentials file not found at $GMAIL_CREDENTIALS"
    exit 1
fi

# ==============================================================================
# 3. Verify Required Directories are Writable
# ==============================================================================
REQUIRED_DIRS=("/app/logs" "/app/output" "/app/tokens")

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "UNHEALTHY: Required directory does not exist: $dir"
        exit 1
    fi

    if [ ! -w "$dir" ]; then
        echo "UNHEALTHY: Directory is not writable: $dir"
        exit 1
    fi
done

# ==============================================================================
# 4. Verify Sufficient Disk Space
# ==============================================================================
# Fail if less than 100MB free
AVAILABLE_KB=$(df /app | tail -1 | awk '{print $4}')
MIN_REQUIRED_KB=102400  # 100MB in KB

if [ "$AVAILABLE_KB" -lt "$MIN_REQUIRED_KB" ]; then
    AVAILABLE_MB=$((AVAILABLE_KB / 1024))
    echo "UNHEALTHY: Insufficient disk space: ${AVAILABLE_MB}MB available (minimum 100MB required)"
    exit 1
fi

# ==============================================================================
# 5. Verify Python Module is Importable
# ==============================================================================
if ! python3 -c "import autospendtracker" > /dev/null 2>&1; then
    echo "UNHEALTHY: Cannot import autospendtracker module"
    exit 1
fi

# ==============================================================================
# All checks passed
# ==============================================================================
echo "HEALTHY: All health checks passed"
exit 0
