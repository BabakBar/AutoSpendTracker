# Phase 3: Code Quality

**Time**: 6 hours | **Priority**: Medium

## Issues

### 1. Time Validation Bug (models.py:49)

**Issue**: Accepts "0:30 AM" (invalid - should be "12:30 AM")

**Fix**:
```python
# models.py:49
# BEFORE
if not re.match(r'^(0?[1-9]|1[0-2]):[0-5][0-9] [AP]M$', v):

# AFTER - removes optional 0
if not re.match(r'^(1[0-2]|[1-9]):[0-5][0-9] [AP]M$', v):
```

---

### 2. Config Captured at Import (ai.py:32-34)

**Issue**: Runtime config changes ignored

**Fix**:
```python
# ai.py - BEFORE
PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION') or get_config_value('LOCATION', 'us-central1')

def initialize_ai_model(project_id=PROJECT_ID, ...):

# AFTER - resolve at runtime
def initialize_ai_model(project_id=None, location=None, ...):
    project_id = project_id or CONFIG.get("PROJECT_ID")
    location = location or CONFIG.get("LOCATION", "us-central1")
```

---

### 3. Unpinned Dependencies (pyproject.toml)

**Issue**: Non-reproducible builds, can pull vulnerable versions

**Fix**:
```toml
# pyproject.toml - BEFORE
dependencies = [
    "google-auth-oauthlib>=1.0.0",
    "requests>=2.25.0",
    ...
]

# AFTER - use ~= for patch updates only
dependencies = [
    "google-auth-oauthlib~=1.2.0",
    "requests~=2.31.0",
    ...
]
```

```bash
# Generate lockfile
pip freeze > requirements.txt
```

---

### 4. Unused Module (security_manager.py)

**Issue**: 218 lines of dead code

**Fix**:
```bash
# Remove if not planning to use Secret Manager
git rm src/autospendtracker/security_manager.py

# Or keep and integrate with config to use Secret Manager
```

---

## Checklist

- [ ] Fix time regex (10 min)
- [ ] Add test for 0:30 AM rejection
- [ ] Fix config loading (30 min)
- [ ] Pin dependencies (30 min)
- [ ] Generate lockfile
- [ ] Run security audit: `safety check`
- [ ] Remove or integrate security_manager (15 min)
- [ ] Run: `pytest tests/ -v && mypy src/`

**Validate**:
```bash
# Time validation fixed
python -c "from autospendtracker.models import Transaction; Transaction(time='0:30 AM', ...)"
# Should raise ValueError

# Config dynamic
python -c "
from autospendtracker.config import CONFIG
CONFIG['MODEL_NAME'] = 'test'
from autospendtracker.ai import initialize_ai_model
# Should use 'test'
"

# Deps pinned
grep '>=' pyproject.toml | wc -l
# Expected: 0
```
