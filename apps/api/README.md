# Apps — API (FastAPI Monolith)

The core backend service handling authentication, job lifecycle, billing, integrations, gallery, and real-time WebSocket streaming.

## Structure

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application factory
│   ├── config.py             # Settings / environment configuration
│   ├── database.py           # Database session management
│   ├── dependencies.py       # Shared FastAPI dependencies
│   │
│   ├── auth/                 # Authentication & authorization module
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── jobs/                 # Job lifecycle module
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── billing/              # Usage metering & payments
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── integrations/         # GitHub App, BYO API keys
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── gallery/              # Public gallery
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── notifications/        # Email/webhook dispatch
│   │   ├── __init__.py
│   │   └── service.py
│   │
│   └── websocket/            # Real-time job streaming
│       ├── __init__.py
│       └── handler.py
│
├── migrations/               # Alembic database migrations
│   └── versions/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth/
│   ├── test_jobs/
│   └── test_billing/
│
├── Dockerfile
├── requirements.txt
├── alembic.ini
└── pyproject.toml
```

## Running Locally

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
