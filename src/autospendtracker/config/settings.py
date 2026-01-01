"""Pydantic Settings-based configuration module.

This module provides type-safe configuration management using Pydantic Settings v2.
Supports environment variables, .env files, and validation.
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Single source of truth for default model
DEFAULT_MODEL_NAME = "gemini-3-flash-preview"


class AppSettings(BaseSettings):
    """Application settings with type validation and environment variable support."""

    # Google Cloud settings
    project_id: str = Field(
        ...,
        description="Google Cloud project ID",
        validation_alias="PROJECT_ID"
    )
    location: str = Field(
        default="us-central1",
        description="Google Cloud location/region",
        validation_alias="LOCATION"
    )
    service_account_file: str = Field(
        default="ASTservice.json",
        description="Path to service account JSON file",
        validation_alias="SERVICE_ACCOUNT_FILE"
    )

    # Google Sheets settings
    spreadsheet_id: str = Field(
        ...,
        description="Google Sheets spreadsheet ID",
        validation_alias="SPREADSHEET_ID"
    )
    sheet_range: str = Field(
        default="Sheet1!A2:G",
        description="Range in the spreadsheet to write data",
        validation_alias="SHEET_RANGE"
    )

    # Application settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="LOG_LEVEL"
    )
    output_file: str = Field(
        default="transaction_data.json",
        description="Path to output JSON file",
        validation_alias="OUTPUT_FILE"
    )
    token_dir: Path = Field(
        default_factory=lambda: Path.home() / ".autospendtracker" / "secrets",
        description="Directory for storing OAuth tokens",
        validation_alias="TOKEN_DIR"
    )

    # Email filtering settings
    email_days_back: int = Field(
        default=7,
        description="Number of days to look back for emails (for weekly analysis)",
        validation_alias="EMAIL_DAYS_BACK",
        gt=0  # Must be greater than 0
    )
    gmail_label_name: str = Field(
        default="AutoSpendTracker/Processed",
        description="Gmail label for marking processed emails",
        validation_alias="GMAIL_LABEL_NAME"
    )

    # AI Model settings
    model_name: str = Field(
        default=DEFAULT_MODEL_NAME,
        description="Google Gen AI model name",
        validation_alias="MODEL_NAME"
    )
    model_temperature: float = Field(
        default=0.1,
        description="Model temperature for generation",
        validation_alias="MODEL_TEMPERATURE",
        ge=0.0,
        le=2.0  # Temperature must be between 0 and 2
    )

    # API Rate Limiting settings (new in modernization)
    api_rate_limit_calls: int = Field(
        default=60,
        description="Maximum API calls per minute",
        validation_alias="API_RATE_LIMIT_CALLS",
        gt=0
    )
    api_rate_limit_period: int = Field(
        default=60,
        description="Rate limit period in seconds",
        validation_alias="API_RATE_LIMIT_PERIOD",
        gt=0
    )

    # Performance Monitoring settings (new in modernization)
    enable_performance_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring and metrics collection",
        validation_alias="ENABLE_PERFORMANCE_MONITORING"
    )
    metrics_log_level: str = Field(
        default="INFO",
        description="Log level for metrics output",
        validation_alias="METRICS_LOG_LEVEL"
    )

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
        validate_default=True,
    )

    @field_validator("log_level", "metrics_log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {', '.join(valid_levels)}"
            )
        return v_upper

    @field_validator("token_dir")
    @classmethod
    def ensure_token_dir_exists(cls, v: Path) -> Path:
        """Ensure token directory exists."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    def get_token_dir_str(self) -> str:
        """Get token directory as string."""
        return str(self.token_dir)

    def validate_required_files(self) -> list[str]:
        """
        Validate that required files exist.

        Returns:
            List of missing files (empty if all present)
        """
        missing = []

        # Check service account file
        service_account_path = Path(self.service_account_file)
        if not service_account_path.exists():
            missing.append(f"Service account file: {self.service_account_file}")

        return missing

    def log_configuration(self) -> None:
        """Log the current configuration (excluding sensitive data)."""
        logger.info("=" * 70)
        logger.info("APPLICATION CONFIGURATION")
        logger.info("=" * 70)
        logger.info(f"Project ID: {self.project_id}")
        logger.info(f"Location: {self.location}")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"Log Level: {self.log_level}")
        logger.info(f"Email Days Back: {self.email_days_back}")
        logger.info(f"Rate Limit: {self.api_rate_limit_calls} calls per {self.api_rate_limit_period}s")
        logger.info(f"Performance Monitoring: {'Enabled' if self.enable_performance_monitoring else 'Disabled'}")
        logger.info("=" * 70)


# Global settings instance - lazy loaded
_settings: Optional[AppSettings] = None


def get_settings(reload: bool = False) -> AppSettings:
    """
    Get application settings (singleton pattern).

    Args:
        reload: Force reload settings from environment

    Returns:
        AppSettings instance
    """
    global _settings

    if _settings is None or reload:
        try:
            _settings = AppSettings()
            logger.debug("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise

    return _settings


def reload_settings() -> AppSettings:
    """
    Reload settings from environment.

    Returns:
        Updated AppSettings instance
    """
    return get_settings(reload=True)
