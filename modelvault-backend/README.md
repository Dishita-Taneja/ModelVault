# ModelVault Backend & API Layer

ModelVault is a security incident-response system that monitors and flags anomalous ML model access.
This repository contains the backend persistence layer, database migrations, and REST APIs built with FastAPI, PostgreSQL, SQLAlchemy 2.0 (async), and Alembic.

---

## Tech Stack
- **Python 3.11+**
- **FastAPI** — high-performance async web framework
- **PostgreSQL** — relational database with JSONB support
- **SQLAlchemy 2.0 (async)** — ORM with `postgresql+asyncpg://`
- **Alembic** — async database migrations
- **Pydantic v2** — validation and serialization schemas
- **uv** — Python package and project manager

---

## Project Structure
```
modelvault-backend/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── core/
│   │   ├── config.py            # Environment settings (Pydantic BaseSettings)
│   │   └── database.py          # Async engine, sessionmaker & DB dependency
│   ├── models/                  # SQLAlchemy 2.0 ORM models
│   │   ├── base.py              # Declarative base
│   │   ├── user.py              # User entity
│   │   ├── model.py             # MLModel tracked entity
│   │   ├── access_event.py      # AccessEvent audit log with JSONB
│   │   └── anomaly_result.py    # Flagged AnomalyResult entity
│   ├── schemas/                 # Pydantic v2 schemas
│   │   ├── user.py
│   │   ├── model.py
│   │   ├── access_event.py
│   │   ├── anomaly_result.py
│   │   └── summary.py
│   ├── crud/                    # Clean DB query functions
│   │   ├── user.py
│   │   ├── model.py
│   │   ├── access_event.py
│   │   ├── anomaly_result.py
│   │   └── summary.py
│   └── api/                     # REST API routers
│       ├── users.py             # GET /users, GET /users/{id}, POST /users
│       ├── models.py            # GET /models, GET /models/{id}, POST /models
│       ├── access_events.py     # GET /access-events, POST /access-events
│       ├── anomaly_results.py   # GET /anomaly-results, POST /anomaly-results
│       └── summary.py           # GET /summary/top-suspicious
├── alembic/                     # Database migrations
│   ├── env.py                   # Async migration engine setup
│   └── versions/
│       └── 0001_initial_schema.py
├── tests/                       # Pytest test suite
│   ├── conftest.py
│   └── test_api.py
├── alembic.ini
├── pyproject.toml
├── seed.py                      # Async mock data seeder
└── .env.example
```

---

## Setup & Quickstart

### 1. Environment & Dependencies
Using `uv`:
```bash
uv venv
uv pip install -e ".[dev]"
```

### 2. Configuration
Copy the environment template:
```bash
cp .env.example .env
```
Update `DATABASE_URL` with your PostgreSQL credentials, for example:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/modelvault
```

### 3. Database Migrations
Run the initial Alembic migration to create all tables and indexes:
```bash
alembic upgrade head
```

### 4. Seed Mock / Demo Data
Populate realistic users, ML models, access events, and flagged anomaly results:
```bash
python seed.py
```

### 5. Start the API Server
Run FastAPI via `uvicorn`:
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger UI will be available at: [http://localhost:8000/docs](http://localhost:8000/docs).

---

## API Endpoints Reference

### Users
- `GET /users` — List users (`skip`, `limit`)
- `GET /users/{id}` — Get user details by UUID
- `POST /users` — Create user

### ML Models
- `GET /models` — List tracked ML models
- `GET /models/{id}` — Get model details by UUID
- `POST /models` — Register a tracked model (`owner_id`, `sensitivity_level`: LOW, MEDIUM, HIGH, CRITICAL)

### Access Events
- `GET /access-events` — List access logs with optional query filters:
  - `user_id` (UUID)
  - `model_id` (UUID)
  - `start_time` (ISO 8601 timestamp)
  - `end_time` (ISO 8601 timestamp)
  - `skip`, `limit`
- `POST /access-events` — Ingest single access event (supports arbitrary JSONB `raw_metadata`)

### Anomaly Results
- `GET /anomaly-results` — List flagged anomaly results with query filters (`user_id`, `model_id`, `start_time`, `end_time`, `skip`, `limit`)
- `POST /anomaly-results` — Ingest flagged anomaly result (integration stub writing payload directly to DB)

### Summary
- `GET /summary/top-suspicious` — Returns the top 3 suspicious access events sorted by `anomaly_score` descending.

---

## Example `curl` Requests

### List Top Suspicious Events
```bash
curl -X GET "http://localhost:8000/summary/top-suspicious"
```

### Ingest an Access Event
```bash
curl -X POST "http://localhost:8000/access-events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "model_id": "00000000-0000-0000-0000-000000000002",
    "action": "download",
    "source": "S3",
    "raw_metadata": {
      "ip_address": "198.51.100.42",
      "bytes_transferred": 14500000000
    }
  }'
```

### Ingest Anomaly Result
```bash
curl -X POST "http://localhost:8000/anomaly-results" \
  -H "Content-Type: application/json" \
  -d '{
    "access_event_id": "<EVENT_UUID>",
    "anomaly_score": 0.98,
    "reason": "Massive unauthorized model weight download via direct S3 API outside business hours."
  }'
```

---

## Running Tests
Run the automated test suite with pytest:
```bash
pytest -v
```
