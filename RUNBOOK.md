# AutoSpendTracker Runbook

Quick reference guide for running tests and the application.

## 🚀 Quick Start

### First Time Setup

```bash
# 1. Navigate to project directory
cd AutoSpendTracker

# 2. Create virtual environment with UV
uv venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
uv pip install -e .

# 5. Install dev dependencies (for testing)
uv pip install pytest pytest-cov

# 6. Verify installation
python -c "import autospendtracker; print('✓ Installation successful')"
```

### Environment Setup

```bash
# 1. Copy example env file
cp .env.example .env

# 2. Edit .env with your values
nano .env  # or vim, code, etc.

# Required values:
# - PROJECT_ID=your-google-cloud-project-id
# - SPREADSHEET_ID=your-google-spreadsheet-id
# - MODEL_NAME=gemini-2.5-flash

# 3. Add credential files
# - credentials.json (Gmail OAuth)
# - ASTservice.json (Service Account)
```

---

## 🧪 Running Tests

### All Tests (Recommended)

```bash
# Activate environment
source .venv/bin/activate

# Run all tests (unit + E2E)
pytest tests/ -v

# Expected output: 38 passed
```

## 🏃 Running the Application

### Standard Run

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run the application
python run_app.py

# Expected output:
# - Initializing AI model
# - Authenticating with Gmail
# - Processing emails
# - Uploading to Sheets
```

### Run with Custom Config

```bash
# Use specific .env file
MODEL_NAME=gemini-2.5-flash SPREADSHEET_ID=your-id python run_app.py

# Set log level
LOG_LEVEL=DEBUG python run_app.py
```

### Dry Run (No Sheets Upload)

```bash
# Modify main.py temporarily or create a dry-run script
python -c "
from autospendtracker.main import run_pipeline
result = run_pipeline(save_to_file=True, upload_to_sheets=False)
print(f'Processed {len(result) if result else 0} transactions')
"
```

### Run as Module

```bash
# Run as Python module
python -m autospendtracker.main
```

---

## 🔧 Development Commands

### Code Quality

```bash
# Format code (if ruff installed)
ruff format .

# Lint code
ruff check .

# Type checking (if mypy installed)
mypy src/autospendtracker/
```

### Check Imports

```bash
# Verify all imports work
python -c "
from autospendtracker import ai, mail, sheets, models, main
from autospendtracker.config import app_config
from autospendtracker.exceptions import *
print('✓ All imports successful')
"
```

### Check Model Version

```bash
# Verify Gemini model configuration
python -c "
from autospendtracker.ai import MODEL_NAME
from autospendtracker.config.app_config import CONFIG
print(f'AI Model: {MODEL_NAME}')
print(f'Config Model: {CONFIG[\"MODEL_NAME\"]}')
"
```

---

## 📊 Test Commands Reference

### By Test File

```bash
# Authentication tests
pytest tests/test_auth.py -v

# Email parsing tests
pytest tests/test_mail.py -v

# AI processing tests
pytest tests/test_ai.py -v

# Data model tests
pytest tests/test_models.py -v

# Sheets integration tests
pytest tests/test_sheets.py -v

# Main orchestration tests
pytest tests/test_main.py -v

# End-to-end tests
pytest tests/test_e2e.py -v
```

### By Functionality

```bash
# Test transaction validation
pytest tests/test_models.py::TestTransaction -v

# Test AI initialization
pytest tests/test_ai.py::TestAI::test_initialize_ai_model -v

# Test complete pipeline
pytest tests/test_e2e.py::TestEndToEnd::test_complete_pipeline_success -v

# Test error handling
pytest tests/ -k "error or failure" -v
```

---

## 🐛 Debugging Commands

### Verbose Output

```bash
# Very verbose with print statements
pytest tests/test_e2e.py -vv -s

# Show local variables on failure
pytest tests/ -l

# Show full traceback
pytest tests/ --tb=long
```

### Run Specific Failed Tests

```bash
# First run to identify failures
pytest tests/ -v

# Re-run only failed tests
pytest tests/ --lf

# Run failed tests first, then others
pytest tests/ --ff
```

### Debug with PDB

```bash
# Drop into debugger on failure
pytest tests/test_e2e.py --pdb

# Drop into debugger at start of test
pytest tests/test_e2e.py --trace
```

---

## 📋 Pre-Deployment Checklist

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run all tests
pytest tests/ -v
# ✓ Expected: 38 passed

# 3. Check imports
python -c "import autospendtracker; print('✓ OK')"

# 4. Verify configuration
python -c "
from autospendtracker.config.app_config import CONFIG
print(f'Model: {CONFIG[\"MODEL_NAME\"]}')
print(f'Location: {CONFIG[\"LOCATION\"]}')
"

# 5. Test with dry run (if implemented)
# python run_app.py --dry-run

# 6. Check credentials exist
ls -la credentials.json ASTservice.json

# 7. Run actual application
python run_app.py
```

---

## 🔄 Daily Development Workflow

```bash
# Morning: Pull latest and setup
git pull
source .venv/bin/activate
uv pip install -e .

# During development: Run related tests
pytest tests/test_ai.py -v  # if working on AI module

# Before commit: Run all tests
pytest tests/ -v

# Commit
git add .
git commit -m "feat: your changes"
git push
```

---

## 🚨 Troubleshooting

### Tests Failing

```bash
# Clear pytest cache
rm -rf .pytest_cache
rm -rf **/__pycache__

# Reinstall dependencies
uv pip install -e . --force-reinstall

# Run tests with full output
pytest tests/ -vv -s --tb=long
```

### Import Errors

```bash
# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check if package is installed
pip list | grep autospendtracker

# Reinstall in editable mode
uv pip install -e .
```

### Missing Dependencies

```bash
# Install all dependencies
uv pip install -e .

# Install dev dependencies
uv pip install pytest pytest-cov

# Verify installation
pip list
```

### Environment Issues

```bash
# Deactivate and recreate venv
deactivate
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e .
```

---

## 📈 Performance Testing

```bash
# Time the tests
time pytest tests/ -v

# Profile test execution
pytest tests/ --durations=10

# Run tests in parallel (if pytest-xdist installed)
pytest tests/ -n auto
```

---

## 🎯 Common Scenarios

### Scenario 1: Fresh Setup

```bash
git clone https://github.com/yourusername/AutoSpendTracker.git
cd AutoSpendTracker
uv venv
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
# Edit .env with your values
pytest tests/ -v
python run_app.py
```

### Scenario 2: After Pulling Changes

```bash
source .venv/bin/activate
uv pip install -e .  # Update dependencies
pytest tests/ -v      # Verify tests pass
python run_app.py     # Run application
```

### Scenario 3: Testing a Feature

```bash
source .venv/bin/activate

# Run related tests
pytest tests/test_ai.py -v

# Run E2E to verify integration
pytest tests/test_e2e.py -v

# Run all tests before commit
pytest tests/ -v
```

### Scenario 4: Debugging an Issue

```bash
source .venv/bin/activate

# Run with verbose output
pytest tests/test_e2e.py -vv -s

# Run with debugger
pytest tests/test_e2e.py::TestEndToEnd::test_complete_pipeline_success --pdb

# Check specific component
python -c "
from autospendtracker.ai import initialize_ai_model
# Test code here
"
```

---

## 📝 Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest tests/ -v` | Run all tests with verbose output |
| `pytest tests/test_e2e.py -v` | Run E2E tests only |
| `pytest tests/ -k "pipeline"` | Run tests matching "pipeline" |
| `pytest tests/ --cov` | Run with coverage report |
| `python run_app.py` | Run the application |
| `source .venv/bin/activate` | Activate virtual environment |
| `uv pip install -e .` | Install/update dependencies |

---

## 💡 Tips

1. **Always activate venv first**: `source .venv/bin/activate`
2. **Run tests before pushing**: `pytest tests/ -v`
3. **Use `-k` for quick testing**: `pytest tests/ -k "test_name"`
4. **Check coverage**: `pytest tests/ --cov --cov-report=term-missing`
5. **Use `-x` to stop on first failure**: `pytest tests/ -x`
6. **Add `-s` to see print statements**: `pytest tests/ -s`

---

## 🆘 Getting Help

```bash
# Pytest help
pytest --help

# List all tests without running
pytest tests/ --collect-only

# Show available fixtures
pytest --fixtures

# Show test coverage paths
pytest tests/ --cov=autospendtracker --cov-report=term
```

---

**Last Updated**: 2025-11-05
**Test Count**: 38 (33 unit + 5 E2E)
**Python Version**: 3.11+
**Model**: gemini-2.5-flash
