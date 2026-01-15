"""AutoSpendTracker - Automated expense tracking using Gmail and Vertex AI.

This package provides tools to automatically extract expense information
from emails and process it using AI capabilities.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("autospendtracker")
except PackageNotFoundError:
    __version__ = "2.1.0"
