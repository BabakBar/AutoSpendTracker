# Code Audit Implementation Guide

## Quick Reference

**Total Effort**: 12 hours over 2 weeks

| Phase | Time | Priority | Files |
|-------|------|----------|-------|
| [1. Security](./phase-1-security.md) | 2 hours | Critical | auth.py, mail.py, utils.py |
| [2. Data Integrity](./phase-2-data-integrity.md) | 4 hours | High | mail.py, main.py, sheets.py |
| [3. Code Quality](./phase-3-quality.md) | 6 hours | Medium | models.py, ai.py, pyproject.toml |

---

## Verified Issues

### Phase 1 (TODAY)
- ✅ Pickle token storage (code injection risk)
- ✅ PII in logs (financial data exposed)
- ✅ Duplicate exception definitions

### Phase 2 (THIS WEEK)
- ✅ No pagination (lose emails >100)
- ✅ No retry logic (failures not handled)
- ✅ Race condition (duplicate transactions)

### Phase 3 (NEXT SPRINT)
- Time validation bug
- Config captured at import
- Unpinned dependencies
- 218 lines dead code

---

## Start Here

1. Read [00-overview.md](./00-overview.md)
2. Follow [phase-1-security.md](./phase-1-security.md)
3. Test & validate after each phase
4. Commit between phases

---

## Notes

- No secrets committed to git (already clean)
- All issues verified in current codebase
- Code examples tested
- Line numbers accurate as of commit ddcca8f
