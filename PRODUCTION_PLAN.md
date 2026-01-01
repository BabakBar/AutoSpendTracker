# AutoSpendTracker Production Readiness Plan

## Current Status

**Branch**: `claude/productionize-codebase-011CUsPP9gT8uqcRaHZEQkZC`
**Date**: 2026-01-01

### Work Already Completed
- Multi-stage Dockerfile (Python 3.13, UV, ~180MB image)
- Docker Compose with Ofelia scheduler
- Health checks & entrypoint scripts
- Notification system (Apprise)
- Rate limiting & monitoring modules
- Comprehensive deployment docs (DEPLOYMENT.md, RUNBOOK.md)
- Environment templates (.env.production.example)
- MODEL_NAME single source of truth refactor (Completed)
- Switched default model to `gemini-3-flash-preview`

### Work In Progress
- Local Docker testing (Blocked: Docker daemon not available)

---

## Phase 1: Complete MODEL_NAME Refactor (DONE)

### Problem
`gemini-2.5-flash` is hardcoded in 10+ places. Single change point doesn't exist.

### Completed Steps
- [x] Added `DEFAULT_MODEL_NAME` constant in `settings.py`
- [x] Updated `settings.py` Pydantic Field to use constant
- [x] Updated `app_config.py` to import and use constant
- [x] Refactored `ai.py` to use `get_settings().model_name` instead of env var lookups
- [x] Updated `monitoring.py` decorator to resolve model at runtime
- [x] Removed hardcoded model from `@track_api_call` decorator in `ai.py`
- [x] Updated docstrings
- [x] Run tests to verify refactor works
- [x] Update `.env` with new model: `MODEL_NAME=gemini-3-flash-preview`
- [x] Update `.env.example` and `.env.production.example` defaults
- [x] Update docker-compose.yml default
- [x] Update documentation (README, DEPLOYMENT.md, etc.)

### Files Changed
| File | Status | Changes |
|------|--------|---------|
| `src/autospendtracker/config/settings.py` | Done | Added `DEFAULT_MODEL_NAME` constant |
| `src/autospendtracker/config/app_config.py` | Done | Imports and uses constant |
| `src/autospendtracker/ai.py` | Done | Uses `get_settings()` for model_name |
| `src/autospendtracker/monitoring.py` | Done | Runtime model resolution in decorator |
| `.env` | Done | Updated default model |
| `.env.example` | Done | Updated default model |
| `.env.production.example` | Done | Updated default model |
| `docker-compose.yml` | Done | Updated default model |
| `docker/entrypoint.sh` | Done | Updated fallback model |
| `README.md` | Done | Updated model references |
| `docs/*.md` | Done | Updated model references |
| `tests/*.py` | Done | Updated test fixtures |

---

## Phase 2: Test Refactored Code (DONE)

### Steps
1. Install test dependencies: `uv pip install pytest pytest-cov` (Done)
2. Run unit tests: `uv run python -m pytest tests/ -v` (Done - passed with fixes)
3. Fix any failing tests (Fixed `test_auth.py` and `test_ai.py`)

---

## Phase 3: Gemini 3 Integration (DONE)

### New Model: `gemini-3-flash-preview`

### Steps
1. Update `DEFAULT_MODEL_NAME` to `gemini-3-flash-preview` in `settings.py` (Done)
2. Update all docs/configs with new model name (Done)

---

## Phase 4: Local Docker Testing (DONE)

### Prerequisites
- [x] Credential files available (credentials.json, ASTservice.json)
- [x] `.env` configured
- [x] `secrets/` directory with symlinks

### Test Results
- [x] **Build:** Successfully built `autospendtracker:test` (fixed `su-exec` issue in `entrypoint.sh`)
- [x] **Health Check:** Passed (`HEALTHY: All health checks passed`)
- [x] **Configuration:** Validated `.env` and credential mounts

### Test Commands Executed
```bash
# 1. Build
docker build -t autospendtracker:test .

# 2. Run Health Check (with local credentials mounted)
docker run --rm --env-file .env \
  -v "$(pwd)/ASTservice.json":/app/secrets/ASTservice.json \
  -v "$(pwd)/credentials.json":/app/secrets/credentials.json \
  autospendtracker:test /app/docker/healthcheck.sh
```

---

## Phase 5: Finalize and Document (DONE)

### Steps
1. Create `CHANGELOG.md` with version 2.1.0 (Done)
2. Update version in `pyproject.toml` and `Dockerfile` to 2.1.0 (Done)
3. Review deployment docs for accuracy (Done)
4. Create PR to main (Ready for user to merge)

---

## Conclusion
The project has been successfully modernized and upgraded to use Gemini 3 Flash Preview.
- **Code:** Refactored for better configuration management and security (JSON tokens).
- **Tests:** All tests passed.
- **Docker:** Production image builds successfully and passes health checks.
- **Docs:** Updated and aligned with the new version.