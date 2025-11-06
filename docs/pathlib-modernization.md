# Pathlib Modernization Plan

## Overview

Modernize codebase from `os.path` operations to `pathlib.Path` - Python's modern, object-oriented path handling API (Python 3.4+).

## Why Pathlib?

**Benefits:**
- Object-oriented: paths as objects, not strings
- Cleaner syntax: `/` operator instead of `os.path.join()`
- Cross-platform: automatic path separator handling
- Type-safe: Path objects vs string manipulation
- Built-in methods: `.exists()`, `.read_text()`, `.mkdir()`, etc.

**What NOT to change:**
- `os.getenv()` / `os.environ` - environment variables
- `os.name` - platform detection
- `os.chmod()` - can keep or use `Path.chmod()` (both valid)

## Current State Analysis

### Files Analyzed: 17 Python files (8 src files + 9 other files including tests)
### Total `os` usages: 36
- **Replace with pathlib: 13 usages** (path/file operations across 8 files)
- **Keep as `os`: 23 usages** (environment variables, system ops across 7 files)

---

## Priority-Ordered Migration Plan

### 🔴 HIGH PRIORITY

#### 1. `run_app.py`
Application entry point - sys.path manipulation using `__file__`.

**Current:**
```python
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
```

**Modern:**
```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))
```

**Changes:**
- `os.path.dirname(__file__)` → `Path(__file__).parent`
- `os.path.join()` → `/` operator
- `os.path.abspath()` → `.resolve()` (or keep as relative with `str()` conversion)
- **Note:** Must convert to `str()` for `sys.path` - it expects strings, not Path objects

---

#### 2. `src/autospendtracker/config/logging_config.py`
Foundational path operations for logging setup.

**Current:**
```python
import os

DEFAULT_LOG_DIR = os.path.join(os.path.expanduser("~"), ".autospendtracker", "logs")
DEFAULT_LOG_FILE = os.path.join(DEFAULT_LOG_DIR, "autospendtracker.log")

def setup_logging(...):
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
```

**Modern:**
```python
from pathlib import Path

DEFAULT_LOG_DIR = Path.home() / ".autospendtracker" / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "autospendtracker.log"

def setup_logging(...):
    if log_file:
        log_path = Path(log_file)
        log_dir = log_path.parent
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
```

**Changes:**
- `os.path.expanduser("~")` → `Path.home()`
- `os.path.join()` → `/` operator
- `os.path.dirname()` → `.parent` property
- `os.makedirs()` → `.mkdir(parents=True, exist_ok=True)`

---

### 🟡 MEDIUM PRIORITY

#### 3. Test Files (5 files)
sys.path setup and file cleanup operations.

**Test sys.path pattern (3 files):**
- `tests/conftest.py` Line 11
- `tests/test_mail.py` Line 10
- `tests/test_auth.py` Line 11

**Current:**
```python
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
```

**Modern:**
```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

**Test file cleanup pattern (2 files):**
- `tests/test_sheets.py` Line 110
- `tests/test_main.py` Line 42

**Current:**
```python
import os

os.unlink(temp_file)
```

**Modern:**
```python
from pathlib import Path

Path(temp_file).unlink()
```

**Changes:**
- Same `__file__` pattern as run_app.py but with `.parent.parent` to go up two levels
- `os.unlink()` → `Path.unlink()` for file deletion
- Must use `str()` conversion for sys.path

---

#### 4. `src/autospendtracker/security.py`
Already uses pathlib partially - make consistent.

**Current:**
```python
def secure_token_path(base_path: str = 'token.pickle') -> str:
    if 'TOKEN_PATH' in os.environ:  # KEEP - env var
        return os.environ['TOKEN_PATH']

    home_dir = Path.home()
    secure_dir = home_dir / '.autospendtracker' / 'secrets'
    secure_dir.mkdir(parents=True, exist_ok=True)

    try:
        if os.name == 'posix':  # KEEP - platform check
            os.chmod(secure_dir, 0o700)  # Can use Path.chmod() or keep
    except Exception as e:
        logger.warning(f"Could not set secure permissions: {e}")

    return str(secure_dir / base_path)
```

**Status:** Already good! Can optionally change `os.chmod()` to `secure_dir.chmod(0o700)`.

---

### 🟢 LOW PRIORITY

#### 5. `src/autospendtracker/auth.py`
Single chmod operation - optional modernization.

**Current:**
```python
os.chmod(token_path, 0o600)  # Secure file permissions
```

**Modern:**
```python
Path(token_path).chmod(0o600)
```

---

## Python 3.13+ Considerations

### Type Hints Strategy

When migrating, add type hints for path parameters. Two recommended approaches:

**Option 1: Accept both str and Path (most flexible)**
```python
from pathlib import Path
from typing import Union

def setup_logging(log_file: Union[str, Path, None] = None) -> None:
    if log_file:
        log_path = Path(log_file)  # Normalize to Path internally
        # ... rest of implementation
```

**Option 2: Use os.PathLike protocol**
```python
import os
from pathlib import Path
from typing import Union

def setup_logging(log_file: Union[str, os.PathLike, None] = None) -> None:
    if log_file:
        log_path = Path(log_file)
        # ... rest of implementation
```

### When to Convert Path → str

**Keep as Path:**
- Internal operations and method chaining
- When passing to other pathlib-aware code
- File/directory operations

**Convert to str:**
- `sys.path` manipulation (requires strings)
- Logging messages (for readability)
- APIs that explicitly require strings
- JSON serialization

**Example:**
```python
src_path = Path(__file__).parent / "src"  # Keep as Path
sys.path.insert(0, str(src_path))  # Convert for sys.path
```

### Python 3.13 Changes (Already Compatible)

- `UnsupportedOperation` instead of `NotImplementedError` on non-Windows (no impact)
- `is_reserved()` deprecated (not used in this codebase)

### Python 3.14 Forward Compatibility

- Stricter parameter validation coming
- Ensure only path components passed to Path constructor
- No extraneous kwargs: `Path('/user', name='admin')` will error
- **Status:** Current codebase already compliant

---

## Files That Should NOT Change

These files only use `os` for environment variables - keep as-is:

| File | Usage | Reason |
|------|-------|--------|
| `main.py` | `os.getenv('VERBOSE_LOGGING')` | Env var |
| `ai.py` | `os.getenv('PROJECT_ID')` etc. | Env var |
| `monitoring.py` | `os.getenv('SHOW_PERFORMANCE_METRICS')` | Env var |
| `config/app_config.py` | `os.environ['KEY']` | Env var |
| `sheets.py` | `os.getenv('SPREADSHEET_ID')` | Env var |
| `mail.py` | `os.getenv('VERBOSE_LOGGING')` | Env var |

---

## Common Patterns Cheat Sheet

### Path Operations

| Old (`os.path`) | Modern (`pathlib`) |
|----------------|-------------------|
| `os.path.join(a, b, c)` | `Path(a) / b / c` |
| `os.path.expanduser("~")` | `Path.home()` |
| `os.path.dirname(p)` | `Path(p).parent` |
| `os.path.basename(p)` | `Path(p).name` |
| `os.path.exists(p)` | `Path(p).exists()` |
| `os.path.isfile(p)` | `Path(p).is_file()` |
| `os.path.isdir(p)` | `Path(p).is_dir()` |
| `os.path.abspath(p)` | `Path(p).resolve()` |
| `os.path.splitext(p)` | `Path(p).stem`, `Path(p).suffix` |
| `os.path.dirname(__file__)` | `Path(__file__).parent` |

### Directory Operations

| Old (`os`) | Modern (`pathlib`) |
|-----------|-------------------|
| `os.makedirs(p, exist_ok=True)` | `Path(p).mkdir(parents=True, exist_ok=True)` |
| `os.listdir(p)` | `list(Path(p).iterdir())` |
| `os.remove(p)` | `Path(p).unlink()` |
| `os.unlink(p)` | `Path(p).unlink()` |
| `os.rmdir(p)` | `Path(p).rmdir()` |

### File Operations

| Old | Modern |
|-----|--------|
| `open(p, 'r').read()` | `Path(p).read_text()` |
| `open(p, 'rb').read()` | `Path(p).read_bytes()` |
| `open(p, 'w').write(data)` | `Path(p).write_text(data)` |

### Keep Using `os` For:

| Operation | Reason |
|-----------|--------|
| `os.getenv('VAR')` | Environment variables |
| `os.environ['VAR']` | Environment variables |
| `os.name` | Platform detection |
| `os.chmod(p, mode)` | Optional - can use `Path(p).chmod(mode)` |

---

## Migration Checklist

### Phase 1: Preparation
- [ ] Create feature branch: `modernize/pathlib-migration`
- [ ] Run test suite to establish baseline
- [ ] Review this plan with team

### Phase 2: Implementation

#### High Priority Files

**run_app.py:**
- [ ] Import `Path` from `pathlib`
- [ ] Replace sys.path manipulation with `Path(__file__).parent / "src"`
- [ ] Add `str()` conversion for sys.path
- [ ] Test application startup

**logging_config.py:**
- [ ] Import `Path` from `pathlib`
- [ ] Replace `DEFAULT_LOG_DIR` with `Path.home()` pattern
- [ ] Replace `DEFAULT_LOG_FILE` with `/` operator
- [ ] Replace `os.path.dirname()` with `.parent`
- [ ] Replace `os.makedirs()` with `.mkdir()`
- [ ] Add type hints: `log_file: Union[str, Path, None]`
- [ ] Test logging functionality

#### Medium Priority Files

**Test files (5 files):**
- [ ] Update `tests/conftest.py` sys.path setup
- [ ] Update `tests/test_mail.py` sys.path setup
- [ ] Update `tests/test_auth.py` sys.path setup
- [ ] Replace `os.unlink()` in `tests/test_sheets.py`
- [ ] Replace `os.unlink()` in `tests/test_main.py`
- [ ] Test suite runs successfully

**security.py:**
- [ ] Review current pathlib usage (already good)
- [ ] Optionally replace `os.chmod()` with `Path.chmod()`
- [ ] Keep env var checks unchanged
- [ ] Test credential path creation

#### Low Priority Files

**auth.py:**
- [ ] Replace `os.chmod()` with `Path.chmod()`
- [ ] Test token file permissions

### Phase 3: Validation
- [ ] Run full test suite (all tests pass)
- [ ] Verify application startup (run_app.py sys.path works)
- [ ] Verify log file creation works
- [ ] Verify secure directories created with correct permissions
- [ ] Verify token files have correct permissions
- [ ] Test functions accept both str and Path arguments
- [ ] Test on macOS (primary platform)
- [ ] Verify no regressions in env var handling
- [ ] Verify type hints work correctly with type checkers

### Phase 4: Cleanup
- [ ] Remove unused `os` imports (if any)
- [ ] Update docstrings if needed
- [ ] Commit with clear message
- [ ] Update this doc to mark as complete

---

## Testing Strategy

### Unit Tests to Add/Update
```python
from pathlib import Path
from typing import Union
import os

def test_log_directory_creation():
    """Verify logs directory created correctly with pathlib."""
    log_dir = Path.home() / ".autospendtracker" / "logs"
    assert log_dir.exists()
    assert log_dir.is_dir()

def test_secure_directory_permissions():
    """Verify secure directory has correct permissions."""
    secure_dir = Path.home() / ".autospendtracker" / "secrets"
    if os.name == 'posix':
        stat_info = secure_dir.stat()
        assert stat_info.st_mode & 0o777 == 0o700

def test_path_operations_cross_platform():
    """Verify path operations work correctly."""
    test_path = Path.home() / ".autospendtracker" / "test"
    assert isinstance(test_path, Path)
    assert str(test_path).count(os.sep) > 0

def test_path_type_flexibility():
    """Verify functions accept both str and Path arguments."""
    from autospendtracker.config.logging_config import setup_logging

    # Test with string
    setup_logging("/tmp/test.log")

    # Test with Path object
    setup_logging(Path("/tmp/test.log"))

    # Both should work without errors

def test_sys_path_manipulation():
    """Verify sys.path setup works with pathlib."""
    import sys
    original_len = len(sys.path)

    # Simulate run_app.py pattern
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))

    assert len(sys.path) == original_len + 1
    assert str(src_path) in sys.path

    # Cleanup
    sys.path.pop(0)
```

### Manual Testing
1. Run `python run_app.py` - verify application starts without import errors
2. Run app normally - verify logs created
3. Check log directory permissions
4. Verify token directory permissions
5. Run full test suite - all tests pass
6. Check environment variable access unchanged

---

## Rollback Plan

If issues arise:
1. Revert commit(s) on feature branch
2. Return to main branch
3. Document issue in this file
4. Address root cause before retry

---

## Benefits After Migration

### Code Quality
- ✅ Modern Python 3.13+ idioms
- ✅ Type-safe path operations
- ✅ Reduced string manipulation bugs
- ✅ Better IDE autocomplete

### Maintainability
- ✅ Cleaner, more readable code
- ✅ Consistent patterns across codebase
- ✅ Easier to understand intent

### Cross-Platform
- ✅ Automatic path separator handling
- ✅ No manual platform-specific code

---

## References

- [pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [PEP 428 - The pathlib module](https://peps.python.org/pep-0428/)
- Python 3.4+ standard library

---

## Status

**Current:** ✅ COMPLETE - All pathlib migrations successfully implemented
**Last Updated:** 2025-11-06
**Owner:** Sia
**Priority:** Medium - improves code quality, no urgent functional need

### Scope Summary
- **8 files** require pathlib migration (13 operations)
- **7 files** correctly use os for env vars (23 operations)
- Includes: run_app.py, logging_config.py, security.py, auth.py, + 5 test files
- Added: Python 3.13+ type hints strategy, sys.path patterns, test enhancements

---

## Notes

- Environment variable operations (`os.getenv`, `os.environ`) intentionally kept as-is
- Platform detection (`os.name`) kept as-is
- File permissions can use either `os.chmod()` or `Path.chmod()` - both valid
- All changes are non-breaking - Path objects can be converted to strings as needed
- Type hints added for better IDE support: `Union[str, Path, None]` for path parameters
- `sys.path` requires string conversion: `str(Path(...))`
- Functions should accept both str and Path for backward compatibility
- Python 3.13 and 3.14 compatible - no deprecated features used
