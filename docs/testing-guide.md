# Testing Guide for AutoSpendTracker

## Overview

AutoSpendTracker has comprehensive test coverage at multiple levels:
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test interactions between modules
- **End-to-End Tests**: Test the complete pipeline from start to finish

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py            # Unit: Authentication
├── test_mail.py            # Unit: Email parsing
├── test_ai.py              # Unit: AI processing
├── test_models.py          # Unit: Data models
├── test_sheets.py          # Unit: Sheets integration
├── test_main.py            # Unit: Main orchestration
└── test_e2e.py             # E2E: Complete pipeline
```

## Running Tests

```bash
# Run all tests
source .venv/bin/activate
pytest tests/ -v

# Run specific test file
pytest tests/test_e2e.py -v

# Run specific test
pytest tests/test_e2e.py::TestEndToEnd::test_complete_pipeline_success -v

# Run with coverage
pytest tests/ --cov=autospendtracker --cov-report=html
```

## End-to-End Testing

### What is an E2E Test?

An end-to-end test validates the **complete workflow** from start to finish:

```
Email Retrieval → Parsing → AI Processing → Validation → Sheets Upload
```

### Key Principles

1. **Mock External Services**: Don't call real APIs (Gmail, AI, Sheets)
2. **Test Real Logic**: Execute actual business logic
3. **Verify Integration**: Ensure all components work together
4. **Test Edge Cases**: Handle failures gracefully

### E2E Test Anatomy

Here's how the main E2E test works:

```python
@patch('autospendtracker.main.append_to_sheet')
@patch('autospendtracker.main.save_transaction_data')
@patch('autospendtracker.main.process_transaction')
@patch('autospendtracker.main.parse_email')
@patch('autospendtracker.main.search_messages')
@patch('autospendtracker.main.gmail_authenticate')
@patch('autospendtracker.main.initialize_ai_model')
@patch('autospendtracker.main.CONFIG')
def test_complete_pipeline_success(self, ...):
    """Test the complete pipeline from email to sheets."""
```

#### Step 1: Setup Configuration
```python
mock_config.get.side_effect = lambda key, default=None: {
    'PROJECT_ID': 'test-project',
    'MODEL_NAME': 'gemini-2.5-flash',
    'SPREADSHEET_ID': 'test-spreadsheet-id'
}.get(key, default)
```

#### Step 2: Mock External Services
```python
# Mock AI client
mock_ai_client = MagicMock()
mock_init_ai.return_value = mock_ai_client

# Mock Gmail service
mock_gmail_service = MagicMock()
mock_gmail_auth.return_value = mock_gmail_service
```

#### Step 3: Provide Test Data
```python
# Mock found emails
mock_search.return_value = [
    {'id': 'msg1'},
    {'id': 'msg2'}
]

# Mock parsed transactions
mock_parse.side_effect = [
    {'info': 'You spent 45.67 EUR at Coffee Shop.', 'account': 'Wise'},
    {'info': 'You spent 120.50 USD at Store.', 'account': 'PayPal'}
]

# Mock AI responses
mock_process.side_effect = [
    ['01-05-2023', '12:34 PM', 'Coffee Shop', '45.67', 'EUR', 'Food & Dining', 'Wise'],
    ['02-05-2023', '3:45 PM', 'Store', '120.50', 'USD', 'Shopping', 'PayPal']
]
```

#### Step 4: Execute Pipeline
```python
result = run_pipeline(save_to_file=True, upload_to_sheets=True)
```

#### Step 5: Verify Results
```python
# Verify pipeline succeeded
self.assertIsNotNone(result)
self.assertEqual(len(result), 2)

# Verify all components were called
mock_init_ai.assert_called_once()
mock_gmail_auth.assert_called_once()
mock_search.assert_called_once()
self.assertEqual(mock_parse.call_count, 2)

# Verify data format
first_transaction = result[0]
self.assertEqual(first_transaction[2], 'Coffee Shop')
self.assertEqual(first_transaction[3], '45.67')
```

## E2E Test Scenarios

### 1. Happy Path: Complete Success
**Test**: `test_complete_pipeline_success`

Tests that everything works when all components succeed:
- ✓ AI model initializes
- ✓ Gmail authenticates
- ✓ Emails are found and parsed
- ✓ Transactions are processed
- ✓ Data is saved and uploaded

### 2. No Data Scenario
**Test**: `test_pipeline_with_no_emails_found`

Tests behavior when no transaction emails exist:
- ✓ Services initialize
- ✓ Search returns empty
- ✓ Pipeline returns None (not error)

### 3. Partial Failures
**Test**: `test_pipeline_with_partial_failures`

Tests resilience when some transactions fail:
- ✓ Some emails parse successfully
- ✓ Some AI processing fails
- ✓ Pipeline continues and returns successful ones

### 4. Initialization Failure
**Test**: `test_pipeline_initialization_failure`

Tests graceful handling of setup failures:
- ✓ AI initialization fails
- ✓ Pipeline catches error
- ✓ Returns None instead of crashing

### 5. Data Transformation
**Test**: `test_data_transformation_through_pipeline`

Tests data flows correctly through the system:
- ✓ Raw data → Transaction model
- ✓ Validation rules applied
- ✓ Format conversions (uppercase currency)
- ✓ Sheet row generation

## Writing Your Own E2E Test

### Template

```python
@patch('autospendtracker.main.YOUR_DEPENDENCY')
@patch('autospendtracker.main.CONFIG')
def test_your_scenario(self, mock_config, mock_dependency):
    """Test description."""

    # 1. Setup: Configure mocks
    mock_config.get.side_effect = lambda k, d=None: {...}.get(k, d)
    mock_dependency.return_value = MagicMock()

    # 2. Execute: Run the pipeline
    result = run_pipeline()

    # 3. Verify: Check results
    self.assertIsNotNone(result)
    mock_dependency.assert_called_once()
```

### Best Practices

1. **Mock at the Entry Point**
   - Mock at `autospendtracker.main.*` level
   - This tests integration between modules

2. **Use Realistic Data**
   - Use actual transaction formats
   - Test with real category names
   - Include edge cases (special characters, etc.)

3. **Test Both Success and Failure**
   - Happy path (everything works)
   - Partial failures (some items fail)
   - Complete failures (system down)

4. **Verify Side Effects**
   - Check data was saved to file
   - Check data was uploaded to sheets
   - Check all expected calls were made

5. **Keep Tests Independent**
   - Each test should run standalone
   - Don't rely on test execution order
   - Clean up temporary files

## Common Patterns

### Pattern 1: Mock Multiple Return Values
```python
# When a function is called multiple times with different results
mock_parse.side_effect = [
    {'info': 'Transaction 1'},  # First call
    {'info': 'Transaction 2'},  # Second call
    {'info': 'Transaction 3'}   # Third call
]
```

### Pattern 2: Conditional Config
```python
# Dynamic config based on key
mock_config.get.side_effect = lambda key, default=None: {
    'KEY1': 'value1',
    'KEY2': 'value2'
}.get(key, default)
```

### Pattern 3: Verify Call Arguments
```python
# Check function was called with specific arguments
mock_function.assert_called_once_with(
    param1='expected_value',
    param2=123
)

# Check data in call arguments
actual_data = mock_function.call_args[0][0]
self.assertEqual(actual_data, expected_data)
```

## Debugging Failed Tests

### 1. Print Mock Calls
```python
print(mock_function.call_args_list)  # All calls
print(mock_function.call_count)       # Number of times called
```

### 2. Check Mock Return Values
```python
print(mock_function.return_value)
print(mock_function.side_effect)
```

### 3. Run Single Test with Verbose Output
```bash
pytest tests/test_e2e.py::TestEndToEnd::test_complete_pipeline_success -vv -s
```

## Test Coverage

Current test coverage:

| Module | Unit Tests | E2E Tests | Coverage |
|--------|-----------|-----------|----------|
| ai.py | 9 tests | ✓ | High |
| mail.py | 3 tests | ✓ | High |
| sheets.py | 5 tests | ✓ | High |
| models.py | 9 tests | ✓ | High |
| main.py | 6 tests | ✓ | High |
| auth.py | 1 test | ✓ | Medium |

**Total**: 38 tests (33 unit + 5 E2E)

## Adding Tests to CI/CD

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e .
          uv pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/ -v --cov=autospendtracker

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Next Steps

1. **Increase Coverage**: Add tests for `auth.py`, `security.py`
2. **Performance Tests**: Measure pipeline execution time
3. **Load Tests**: Test with hundreds of transactions
4. **Integration Tests**: Test with real (sandboxed) APIs
5. **Snapshot Tests**: Compare output against known good results
