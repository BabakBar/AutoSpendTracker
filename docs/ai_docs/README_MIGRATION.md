# Migration Guide

This document explains the migration of AutoSpendTracker from its original structure to a modern Python package structure.

## File Mappings

The following files have been refactored and moved to the new package structure:

| Old File | New File |
|----------|----------|
| `api.py` | `src/autospendtracker/ai.py` |
| `fetch_mails.py` | `src/autospendtracker/mail.py` |
| `gmail_auth.py` | `src/autospendtracker/auth.py` |
| `sheets_integration.py` | `src/autospendtracker/sheets.py` |
| `requirements.txt` | `pyproject.toml` |

## Entry Point

The main entry point is still `autospendtracker.py`, which now imports functionality from the package modules. 

## Dependency Management

Dependencies are now managed with UV instead of pip:

```
# Install the package in development mode
uv pip install -e .

# Run the application
uv run python autospendtracker.py
```

## Configuration

Configuration is now centralized in the `src/autospendtracker/config/` module, which loads settings from environment variables and the `.env` file.

## Why This Change?

This modernization provides several benefits:

1. **Better organization**: Code is now organized into logical modules
2. **Improved maintainability**: Separation of concerns makes the code easier to maintain
3. **Type safety**: Added type hints throughout the codebase
4. **Modern tooling**: Integration with modern Python tools like UV and Pydantic
5. **Better error handling**: More robust error handling and logging
6. **Testability**: Proper structure for unit testing

For more details, see the [modernization guide](docs/modernize.md).