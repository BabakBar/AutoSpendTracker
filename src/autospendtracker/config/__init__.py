"""Configuration package for AutoSpendTracker."""

from autospendtracker.config.logging_config import setup_logging
from autospendtracker.config.app_config import (
    get_config,
    get_config_value,
    reload_config,
    CONFIG
)
from autospendtracker.config.settings import (
    AppSettings,
    get_settings,
    reload_settings,
)

__all__ = [
    'setup_logging',
    'get_config',
    'get_config_value',
    'reload_config',
    'CONFIG',
    # New Pydantic Settings
    'AppSettings',
    'get_settings',
    'reload_settings',
]