#!/bin/bash
# ==============================================================================
# AutoSpendTracker Entrypoint Script
# ==============================================================================
# Purpose: Container initialization and environment validation
# Runs as: root (then drops to appuser)
# ==============================================================================

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==============================================================================
# 1. Environment Variable Validation
# ==============================================================================
log_info "Validating environment variables..."

REQUIRED_VARS=(
    "PROJECT_ID"
    "SPREADSHEET_ID"
    "LOCATION"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    log_error "Please set these variables in your Coolify environment configuration"
    exit 1
fi

log_info "✓ All required environment variables are set"

# ==============================================================================
# 2. Credential File Validation
# ==============================================================================
log_info "Validating credential files..."

CREDENTIALS_FILE="${SERVICE_ACCOUNT_FILE:-/app/secrets/ASTservice.json}"
GMAIL_CREDENTIALS="${GMAIL_CREDENTIALS_FILE:-/app/secrets/credentials.json}"

if [ ! -f "$CREDENTIALS_FILE" ]; then
    log_error "Service account file not found: $CREDENTIALS_FILE"
    log_error "Please upload ASTservice.json to Coolify secrets"
    exit 1
fi

if [ ! -f "$GMAIL_CREDENTIALS" ]; then
    log_error "Gmail credentials file not found: $GMAIL_CREDENTIALS"
    log_error "Please upload credentials.json to Coolify secrets"
    exit 1
fi

log_info "✓ Credential files found"

# ==============================================================================
# 3. Directory Setup and Permissions
# ==============================================================================
log_info "Setting up directories..."

# Ensure directories exist with proper permissions
mkdir -p /app/logs /app/output /app/tokens

# Set ownership to appuser (these might be mounted volumes)
chown -R appuser:appuser /app/logs /app/output /app/tokens 2>/dev/null || true

log_info "✓ Directories configured"

# ==============================================================================
# 4. Disk Space Check
# ==============================================================================
log_info "Checking disk space..."

AVAILABLE_KB=$(df /app | tail -1 | awk '{print $4}')
AVAILABLE_MB=$((AVAILABLE_KB / 1024))

if [ "$AVAILABLE_MB" -lt 100 ]; then
    log_warn "Low disk space: ${AVAILABLE_MB}MB available"
    log_warn "Consider cleaning up old logs or increasing disk allocation"
else
    log_info "✓ Sufficient disk space: ${AVAILABLE_MB}MB available"
fi

# ==============================================================================
# 5. Python Environment Verification
# ==============================================================================
log_info "Verifying Python environment..."

if ! python3 --version > /dev/null 2>&1; then
    log_error "Python 3 is not available"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
log_info "✓ Python $PYTHON_VERSION is available"

# ==============================================================================
# 6. Configuration Summary
# ==============================================================================
log_info "Configuration Summary:"
echo "  Project ID: ${PROJECT_ID}"
echo "  Spreadsheet ID: ${SPREADSHEET_ID:0:20}..."
echo "  Location: ${LOCATION}"
echo "  Email Days Back: ${EMAIL_DAYS_BACK:-7}"
echo "  Model: ${MODEL_NAME:-gemini-3-flash-preview}"
echo "  Timezone: ${TZ:-UTC}"
echo "  Notifications: ${NOTIFICATION_ENABLED:-false}"

# ==============================================================================
# 7. Execute Application
# ==============================================================================
log_info "Starting AutoSpendTracker..."
echo "========================================"

# Drop privileges and execute the application as appuser
# (User is already set to appuser in Dockerfile)
exec "$@"
