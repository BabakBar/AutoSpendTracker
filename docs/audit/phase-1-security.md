# Phase 1: Security Fixes

**Time**: 2 hours | **Priority**: Critical

## Issues

### 1. Pickle Token Storage (auth.py:57, 83)

**Risk**: Arbitrary code execution if token.pickle modified

**Fix**:
```python
# auth.py - Replace pickle with JSON
from google.oauth2.credentials import Credentials

# BEFORE (line 57)
with open(token_path, 'rb') as token:
    creds = pickle.load(token)

# AFTER
if Path(token_path).exists():
    creds = Credentials.from_authorized_user_file(str(token_path), scopes)

# BEFORE (line 83)
with open(token_path, 'wb') as token:
    pickle.dump(creds, token)

# AFTER
token_path.write_text(creds.to_json(), encoding='utf-8')
os.chmod(token_path, 0o600)
```

**Migration** (one-time):
```bash
# Backup old token
cp token.pickle token.pickle.bak

# Run once to convert
python3 << 'EOF'
import pickle, json, os
from pathlib import Path
from google.oauth2.credentials import Credentials

old = Path('token.pickle')
new = Path.home() / '.autospendtracker/secrets/gmail-token.json'
new.parent.mkdir(parents=True, exist_ok=True)

if old.exists():
    with open(old, 'rb') as f:
        creds = pickle.load(f)
    new.write_text(creds.to_json())
    os.chmod(new, 0o600)
    print(f"Migrated to {new}")
    old.unlink()
EOF
```

**Update .env**:
```bash
TOKEN_PATH=~/.autospendtracker/secrets/gmail-token.json
```

---

### 2. PII in Logs (mail.py:230)

**Risk**: Financial data exposed in logs

**Fix**:
```python
# mail.py:230 - BEFORE
logger.info(f"Successfully parsed transaction: {transaction_details}")

# AFTER
logger.debug(f"Parsed transaction for {transaction_details.get('account', 'unknown')}")
# transaction_details contains: date, merchant, amount
```

---

### 3. Duplicate Exceptions (utils.py:43-60)

**Risk**: Confusing imports, inconsistent error handling

**Fix**:
```python
# utils.py - Remove lines 43-60
# Add at top:
from autospendtracker.exceptions import (
    AutoSpendTrackerError,
    ConfigurationError,
    APIError,
    DataValidationError
)
```

---

## Checklist

- [ ] Replace pickle with JSON (30 min)
- [ ] Run migration script
- [ ] Test OAuth flow works
- [ ] Change log level to DEBUG (5 min)
- [ ] Remove duplicate exceptions (10 min)
- [ ] Run tests: `pytest tests/ -v`

**Validate**:
```bash
# No pickle
rg "pickle\.(load|dump)" src/
# Expected: empty

# Token is JSON
file ~/.autospendtracker/secrets/gmail-token.json
# Expected: JSON data

# No PII in logs
rg "logger.info.*transaction.*:" src/
# Expected: empty
```
