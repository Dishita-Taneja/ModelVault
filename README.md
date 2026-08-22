# ModelVault

Security incident-response platform for monitoring and triaging anomalous access to ML models. FastAPI backend + PostgreSQL audit store + React SOC dashboard.

---

## Project Structure

```
ModelVault/
├── .venv/                  # Single shared Python virtualenv (uv-managed, project root only)
├── modelvault-backend/     # FastAPI REST API, Alembic migrations, seed scripts
├── modelvault-frontend/    # React + Vite SOC dashboard
├── data/                   # Local datasets, exports, and seed assets (optional)
├── pyproject.toml          # Root Python project config
├── uv.lock
└── README.md
```

The frontend uses `node_modules/` (npm) and does **not** need a Python virtualenv.

---

## Prerequisites

- **Python 3.11+** with [uv](https://docs.astral.sh/uv/)
- **Node.js 18+** and npm
- **PostgreSQL** (default database name: `modelvault`)

---

## Python Environment (single `.venv` at root)

Use **one** virtualenv at the project root. Do not create nested `.venv` directories inside `modelvault-backend/` or elsewhere.

If a nested venv already exists, remove it and recreate at the root:

```bash
# From ModelVault/ root
rm -rf modelvault-backend/.venv   # remove nested venv if present
uv venv                           # creates ModelVault/.venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
uv sync --all-groups              # installs backend + dev deps into root .venv
```

This repo uses a **uv workspace**: `modelvault-backend` is a workspace member and shares the root `.venv` and `uv.lock`. Do not create a `.venv` inside `modelvault-backend/`.

Use `uv run` from the project root or from `modelvault-backend/` — both use the shared root environment.

---

## Backend Setup & Run

```bash
# From ModelVault/ root
cd modelvault-backend
cp .env.example .env
uv run alembic upgrade head
uv run python seed.py

# Start API (either command works)
uv run uvicorn app.main:app --reload --port 8000          # from modelvault-backend/
# or from project root:
# uv run uvicorn app.main:app --reload --app-dir modelvault-backend --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Backend `.env` variables

Create `modelvault-backend/.env` from `.env.example`:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/modelvault` |
| `PROJECT_NAME` | Display name for the API | `ModelVault Backend` |
| `API_V1_STR` | API prefix (empty = routes at root) | `""` |
| `DEBUG` | Enable debug mode | `True` |

---

## Frontend Setup & Run

```bash
cd modelvault-frontend
npm install
cp .env.example .env
npm run dev
```

Dashboard: [http://localhost:5173](http://localhost:5173)  
Sign-up page: [http://localhost:5173/signup](http://localhost:5173/signup)

Production build:

```bash
npm run build
npm run preview
```

### Frontend `.env` variables

Create `modelvault-frontend/.env` from `.env.example`:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | FastAPI backend base URL | `http://localhost:8000` |
| `VITE_USE_MOCK_FALLBACK` | Use local mock data when API is unreachable | `true` |

---

## Running Tests

From the project root with the root `.venv` active:

```bash
cd modelvault-backend
pytest -v
```

---

## Quick Reference

| Service | Command | URL |
|---------|---------|-----|
| Backend API | `cd modelvault-backend && uv run uvicorn app.main:app --reload --port 8000` | http://localhost:8000 |
| Frontend | `cd modelvault-frontend && npm run dev` | http://localhost:5173 |
