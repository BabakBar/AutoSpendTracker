# Modernization Guide

This document describes the modernization improvements made to AutoSpendTracker, bringing it to Python 3.13 with modern best practices and tooling.

## Overview

The modernization effort focused on:
- **Python 3.13**: Leveraging the latest Python features and performance improvements
- **Performance Monitoring**: Comprehensive metrics tracking for API calls and costs
- **Pydantic Settings**: Type-safe configuration management
- **Rate Limiting**: API cost control and call throttling
- **Enhanced Type Checking**: Stricter mypy configuration

## Python 3.13 Upgrade

### Key Benefits

AutoSpendTracker now requires Python 3.13, which provides:

- **5-15% Performance Improvement**: General speedup across all operations
- **Experimental JIT Compiler**: Up to 30% faster for computation-heavy tasks
- **Free-threaded Mode (No-GIL)**: True multi-threading support (experimental)
- **Better Error Messages**: More helpful diagnostics with suggestions
- **Enhanced Type System**: Improved typing features (TypeIs, ReadOnly, TypeVar defaults)

### Migration

To upgrade your environment:

```bash
# Install Python 3.13
# On macOS with Homebrew:
brew install python@3.13

# On Ubuntu/Debian:
sudo apt update && sudo apt install python3.13

# Recreate your virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .  # or: pip install -e .
```

## Performance Monitoring

### Overview

The new `monitoring.py` module provides comprehensive performance tracking:

- **Function Timing**: Track execution time for all key functions
- **API Metrics**: Monitor API calls, token usage, and costs
- **Automatic Logging**: Summary reports after each pipeline run

### Features

#### Performance Metrics
- Total calls, execution time (min/avg/max)
- Error tracking
- Last call timestamp

#### API Metrics
- Total calls and tokens consumed
- Cost tracking (automatically calculated for Gemini 2.5 Flash)
- Average latency per call
- Error rates

### Usage

The monitoring is automatically integrated into key functions. You'll see a summary report at the end of each run:

```
======================================================================
PERFORMANCE METRICS SUMMARY
======================================================================

autospendtracker.main.process_emails:
  calls: 1
  total_time: 45.23s
  avg_time: 45.230s
  min_time: 45.230s
  max_time: 45.230s
  errors: 0
  last_called: 2025-11-06T15:30:45.123456

======================================================================
API METRICS SUMMARY
======================================================================

gemini-generate-content:gemini-2.5-flash:
  calls: 15
  total_tokens: 12,450
  total_cost: $0.0187
  avg_cost_per_call: $0.0012
  avg_latency: 1.234s
  errors: 0
  last_called: 2025-11-06T15:30:40.123456

----------------------------------------------------------------------
TOTALS:
  Total API Calls: 15
  Total Tokens: 12,450
  Total Cost: $0.0187
  Avg Cost/Call: $0.0012
======================================================================
```

### Decorators

Use the monitoring decorators in your code:

```python
from autospendtracker.monitoring import track_performance, track_api_call

@track_performance
def my_function():
    # Function code
    pass

@track_api_call("my-api-endpoint", model_name="gemini-2.5-flash")
def call_api():
    # API call code
    pass
```

### Manual Usage

```python
from autospendtracker.monitoring import (
    get_metrics_summary,
    log_metrics_summary,
    reset_metrics
)

# Get metrics programmatically
metrics = get_metrics_summary()

# Log summary
log_metrics_summary()

# Reset metrics
reset_metrics()
```

## Pydantic Settings

### Overview

Configuration management now uses Pydantic Settings v2 for:

- **Type Safety**: Automatic validation of configuration values
- **Environment Variables**: Seamless .env file integration
- **Documentation**: Self-documenting configuration fields
- **IDE Support**: Better autocomplete and type hints

### Configuration Class

The new `AppSettings` class in `config/settings.py` defines all configuration:

```python
from autospendtracker.config import get_settings

# Get settings (singleton)
settings = get_settings()

# Access configuration
project_id = settings.project_id
model_name = settings.model_name
rate_limit = settings.api_rate_limit_calls
```

### Available Settings

#### Google Cloud Settings
- `project_id` (required): Google Cloud project ID
- `location`: GCP location/region (default: "us-central1")
- `service_account_file`: Service account JSON path (default: "ASTservice.json")

#### Google Sheets Settings
- `spreadsheet_id` (required): Google Sheets ID
- `sheet_range`: Sheet range for writing (default: "Sheet1!A2:G")

#### Application Settings
- `log_level`: Logging level (default: "INFO")
- `output_file`: Output JSON file path (default: "transaction_data.json")
- `token_dir`: OAuth token directory (default: "~/.autospendtracker/secrets")

#### Email Filtering Settings
- `email_days_back`: Days to look back for emails (default: 7)
- `gmail_label_name`: Label for processed emails (default: "AutoSpendTracker/Processed")

#### AI Model Settings
- `model_name`: Gen AI model name (default: "gemini-2.5-flash")
- `model_temperature`: Generation temperature (default: 0.1, range: 0.0-2.0)

#### Rate Limiting Settings (New)
- `api_rate_limit_calls`: Max API calls per period (default: 60)
- `api_rate_limit_period`: Rate limit period in seconds (default: 60)

#### Monitoring Settings (New)
- `enable_performance_monitoring`: Enable monitoring (default: true)
- `metrics_log_level`: Metrics log level (default: "INFO")

### Environment Variables

All settings can be configured via .env file:

```bash
# .env file
PROJECT_ID=your-project-id
SPREADSHEET_ID=your-sheet-id
MODEL_NAME=gemini-2.5-flash
API_RATE_LIMIT_CALLS=60
ENABLE_PERFORMANCE_MONITORING=true
```

### Validation

Pydantic automatically validates:
- Required fields are present
- Values are correct types
- Numeric values are within valid ranges
- Log levels are valid
- Directories are created if missing

## Rate Limiting

### Overview

The new `rate_limiter.py` module provides API cost control:

- **Adaptive Rate Limiting**: Sliding window algorithm
- **Cost Budget Tracking**: Daily spending limits
- **Automatic Throttling**: Prevents exceeding rate limits
- **Statistics Logging**: Track throttling events

### Features

#### Adaptive Rate Limiter
- Sliding window algorithm for precise control
- Automatic waiting when limit reached
- Thread-safe implementation
- Per-endpoint rate limiting

#### Cost Budget Tracking
- Set daily spending budgets
- Alert at configurable thresholds (default: 80%)
- Automatic budget exceeded detection

### Usage

Rate limiting is automatically applied to API calls. The default is 60 calls per minute.

#### Custom Rate Limits

```python
from autospendtracker.rate_limiter import rate_limit

@rate_limit(max_calls=30, period=60, name="my-api")
def my_api_call():
    # API call code
    pass
```

#### Budget Tracking

```python
from autospendtracker.rate_limiter import set_daily_budget, check_budget

# Set daily budget
set_daily_budget(budget=5.00, alert_threshold=0.8)

# Check budget before expensive operation
if check_budget(estimated_cost):
    # Proceed with operation
    pass
else:
    # Budget exceeded
    pass
```

#### Statistics

```python
from autospendtracker.rate_limiter import (
    get_all_rate_limiter_stats,
    log_rate_limiter_stats,
    reset_all_rate_limiters
)

# Get stats
stats = get_all_rate_limiter_stats()

# Log stats
log_rate_limiter_stats()

# Reset all limiters
reset_all_rate_limiters()
```

### Configuration

Configure rate limits in .env:

```bash
API_RATE_LIMIT_CALLS=60
API_RATE_LIMIT_PERIOD=60
```

## Enhanced Type Checking

### mypy Configuration

The mypy configuration has been enhanced for stricter type checking:

```toml
[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true
strict_equality = true
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Running Type Checks

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run mypy
mypy src/autospendtracker
```

## Dependencies

### New Dependencies

The following packages were added:

- `pydantic~=2.10.0`: Core Pydantic library (already in use)
- `pydantic-settings~=2.11.0`: Configuration management
- `ratelimit~=2.2.0`: Rate limiting
- `perfmetrics~=3.1.0`: Performance metrics (optional, for advanced use)

### Installation

```bash
# Using UV (recommended)
uv pip install -e .

# Using pip
pip install -e .

# With dev dependencies
uv pip install -e ".[dev]"
```

## Best Practices

### Performance Monitoring

1. **Review Metrics Regularly**: Check the metrics summary after each run
2. **Monitor Costs**: Track API costs to optimize usage
3. **Identify Bottlenecks**: Use performance metrics to find slow functions
4. **Set Alerts**: Configure cost budgets to prevent overspending

### Configuration Management

1. **Use .env Files**: Keep configuration separate from code
2. **Validate Settings**: Let Pydantic catch configuration errors early
3. **Document Settings**: Add comments to your .env file
4. **Use Type Hints**: Leverage IDE support with proper types

### Rate Limiting

1. **Set Conservative Limits**: Start with lower limits and adjust
2. **Monitor Throttling**: Check rate limiter stats to tune limits
3. **Use Budgets**: Set daily budgets to control costs
4. **Test Limits**: Verify rate limiting works before production use

## Migration Guide

### For Existing Users

1. **Update Python**: Install Python 3.13
2. **Update Dependencies**: Run `uv pip install -e .` or `pip install -e .`
3. **Review Configuration**: Check your .env file for new settings
4. **Test Thoroughly**: Run a test execution to verify everything works
5. **Monitor Metrics**: Review the new metrics output

### Breaking Changes

- **Python Version**: Now requires Python 3.13+ (was 3.11+)
- **None**: All changes are backward compatible at the API level

### Optional Migration

While the old configuration system (`CONFIG`) still works, we recommend migrating to Pydantic Settings:

```python
# Old way (still supported)
from autospendtracker.config import CONFIG
project_id = CONFIG.get("PROJECT_ID")

# New way (recommended)
from autospendtracker.config import get_settings
settings = get_settings()
project_id = settings.project_id
```

## Troubleshooting

### Common Issues

**Issue**: Import errors after upgrade
**Solution**: Reinstall dependencies: `uv pip install -e .`

**Issue**: Configuration validation errors
**Solution**: Check required fields in .env (PROJECT_ID, SPREADSHEET_ID)

**Issue**: Rate limiting too aggressive
**Solution**: Adjust limits in .env: `API_RATE_LIMIT_CALLS=100`

**Issue**: Type checking errors
**Solution**: Run `mypy src/autospendtracker` to see specific issues

## Performance Tips

1. **JIT Compiler**: Python 3.13's JIT is experimental but can provide speedups
2. **Async Operations**: Consider async for I/O-bound operations
3. **Batch Processing**: Process multiple transactions in batches
4. **Caching**: Cache repeated API responses when appropriate
5. **Rate Limiting**: Balance between speed and API limits

## Future Enhancements

Potential future improvements:

- **OpenTelemetry Integration**: For distributed tracing
- **Prometheus Metrics**: For time-series monitoring
- **Async Rate Limiting**: For high-throughput scenarios
- **Auto-scaling Limits**: Dynamically adjust based on quota
- **Cost Optimization**: Automatic model selection based on budget

## Support

For issues or questions about the modernization:

1. Check the [main README](../README.md)
2. Review this documentation
3. Open an issue on GitHub
4. Check the logs for detailed error messages

## References

- [Python 3.13 Release Notes](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Rate Limiting Best Practices](https://zuplo.com/blog/2025/01/06/10-best-practices-for-api-rate-limiting-in-2025)
- [Python Type Checking with mypy](https://mypy.readthedocs.io/)
