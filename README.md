# 01 - Workday RaaS & REST Ingestion Engine

Multi-source Workday Report-as-a-Service (RaaS) and REST API ingestion engine with OAuth2/ISU token lifecycle management, offset/cursor pagination, exponential backoff retry logic, and a Node.js webhook event normalizer.

## Modules
- `src/raas_ingestion/auth.py`: Thread-safe token cache with proactive expiry buffer.
- `src/raas_ingestion/retry_policy.py`: Exponential backoff with jitter and HTTP 429 `Retry-After` support.
- `src/raas_ingestion/paginator.py`: Offset and cursor-based pagination iterator.
- `src/raas_ingestion/client.py`: Unified ingestion client combining auth, retry, and pagination.
- `src/js/webhook_normalizer.js`: HMAC-SHA256 webhook signature verifier and event normalizer.

## Run Verifiers
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
node --test tests/test_webhook.mjs
```
