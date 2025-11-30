# EFIR Budget Planning Backend

FastAPI 0.123 + Python 3.12 scaffold aligned to the v1.2 TSD.

## Setup
1. Create virtual env (e.g., `python3 -m venv venv && source venv/bin/activate`).
2. Install deps: `pip install -e .[dev]`.
3. Run API: `uvicorn backend.app.main:app --reload`.
4. Run tests: `pytest`.

Endpoints available:
- `GET /health/live` — liveness probe.
- `GET /health/ready` — readiness placeholder.
