# Phase 2: Data Integrity

**Time**: 4 hours | **Priority**: High

## Issues

### 1. No Pagination (mail.py:113)

**Impact**: Only processes first 100 emails

**Fix**:
```python
# mail.py:search_messages - Add pagination
def search_messages(service, user_id='me', days_back=None) -> List[Dict]:
    # ... existing query logic ...

    all_messages = []
    request = service.users().messages().list(userId=user_id, q=query, maxResults=100)

    while request:
        response = request.execute()
        all_messages.extend(response.get('messages', []))
        request = service.users().messages().list_next(request, response)

    logger.info(f"Found {len(all_messages)} emails across all pages")
    return all_messages
```

---

### 2. No Retry Logic (mail.py, sheets.py)

**Impact**: Transient failures cause complete pipeline failure

**Fix**:
```python
# utils.py - Add retry decorator
from tenacity import retry, stop_after_attempt, wait_exponential
from googleapiclient.errors import HttpError

def retry_api(func):
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=4, max=10),
        retry=lambda e: isinstance(e, HttpError) and e.resp.status >= 500
    )(func)

# mail.py - Wrap API calls
@retry_api
def search_messages(...):
    # existing code

# sheets.py - Wrap API calls
@retry_api
def append_to_sheet(...):
    # existing code
```

---

### 3. Race Condition (main.py:92)

**Impact**: Crash before labeling creates duplicates

**Current** (lines 82-92):
```python
for msg in messages:
    transaction_info = parse_email(service, 'me', msg['id'])
    result = process_transaction(client, transaction_info)
    if result:
        sheet_data.append(result)
        # Label AFTER processing - PROBLEM
        if label_id:
            labeled = add_label_to_message(service, msg['id'], label_id)
```

**Fix**:
```python
for msg in messages:
    # Label FIRST to claim email
    if label_id:
        labeled = add_label_to_message(service, msg['id'], label_id)
        if not labeled:
            logger.warning(f"Skipping {msg['id']} - can't label")
            continue

    # Now safe to process
    transaction_info = parse_email(service, 'me', msg['id'])
    result = process_transaction(client, transaction_info)
    if result:
        sheet_data.append(result)
```

---

## Checklist

- [ ] Add pagination loop (45 min)
- [ ] Test with 150+ emails
- [ ] Add retry decorator (30 min)
- [ ] Apply to mail.py, sheets.py
- [ ] Test retry with mock 503 error
- [ ] Move labeling before processing (30 min)
- [ ] Test no duplicates on crash/retry
- [ ] Run: `pytest tests/ -v`

**Validate**:
```bash
# Pagination works (send 150 test emails)
python run_app.py 2>&1 | grep "Found.*emails"
# Should show >100

# Retry active
# Temporarily break network, verify retries
tail -f ~/.autospendtracker/logs/*.log | grep -i retry

# No duplicates
# Run twice, check Sheets for duplicate rows
```
