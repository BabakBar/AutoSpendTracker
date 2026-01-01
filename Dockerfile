# ==============================================================================
# AutoSpendTracker Production Dockerfile
# ==============================================================================
# Multi-stage build using UV package manager and Python 3.13-slim
# Results in ~180MB production image (vs ~1.2GB single-stage)
# ==============================================================================

# ==============================================================================
# Stage 1: Builder - Install dependencies
# ==============================================================================
FROM python:3.13-slim AS builder

# Install UV package manager from official source
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set UV environment variables for optimal Docker usage
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Set working directory
WORKDIR /app

# Copy dependency files first (better caching - these change rarely)
COPY pyproject.toml ./

# Install dependencies using UV
# This creates a virtual environment in /app/.venv
# Note: If uv.lock exists, it will be used for reproducible builds
RUN uv sync --no-dev --no-install-project

# Copy application source code
COPY src/ ./src/

# Install the project itself
RUN uv sync --no-dev

# ==============================================================================
# Stage 2: Production Runtime - Minimal image with only runtime files
# ==============================================================================
FROM python:3.13-slim

# Install runtime dependencies only
# curl: for health checks
# ca-certificates: for HTTPS connections
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# UID 1000 is standard for first non-root user
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -d /app -s /sbin/nologin appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application source code
COPY --chown=appuser:appuser src/ ./src/

# Copy entrypoint and healthcheck scripts
COPY --chmod=755 docker/entrypoint.sh /app/docker/entrypoint.sh
COPY --chmod=755 docker/healthcheck.sh /app/docker/healthcheck.sh

# Create required directories with proper permissions
RUN mkdir -p /app/logs /app/output /app/tokens /app/secrets && \
    chown -R appuser:appuser /app/logs /app/output /app/tokens

# Set Python path to include our application
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_DIR="/app/logs"

# Health check - runs every 30 seconds
# Verifies container is healthy and ready to process jobs
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["/app/docker/healthcheck.sh"]

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["/app/docker/entrypoint.sh"]

# Default command - can be overridden
CMD ["python", "-m", "autospendtracker"]

# Metadata labels
LABEL maintainer="babak.barghi@gmail.com" \
      description="AutoSpendTracker - Automated expense tracking from email" \
      version="2.1.0" \
      org.opencontainers.image.source="https://github.com/BabakBar/AutoSpendTracker"
