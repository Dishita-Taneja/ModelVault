modelvault-backend/
├── app/
│   ├── main.py                  # FastAPI application with CORS and routing
│   ├── core/
│   │   ├── config.py            # Environment configuration via Pydantic BaseSettings
│   │   ├── database.py          # Async engine, sessionmaker, get_db dependency
│   │   └── utils.py             # Flexible ISO datetime query parameter parsing
│   ├── models/                  # SQLAlchemy 2.0 async ORM models
│   │   ├── base.py              # DeclarativeBase
│   │   ├── user.py              # users table
│   │   ├── model.py             # models table (tracked ML models)
│   │   ├── access_event.py      # access_events table (raw audit logs with JSONB)
│   │   └── anomaly_result.py    # anomaly_results table (flagged results)
│   ├── schemas/                 # Pydantic v2 validation and serialization schemas
│   │   ├── user.py              # UserBase, UserCreate, UserRead
│   │   ├── model.py             # MLModelBase, MLModelCreate, MLModelRead
│   │   ├── access_event.py      # AccessEventBase, AccessEventCreate, AccessEventRead
│   │   ├── anomaly_result.py    # AnomalyResultBase, AnomalyResultCreate, AnomalyResultRead
│   │   └── summary.py           # SuspiciousAccessEventRead
│   ├── crud/                    # Clean DB query layer
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
│       └── 0001_initial_schema.py # Initial migration with PostgreSQL JSONB and indexes
├── tests/                       # Pytest test suite
│   ├── conftest.py              # Async in-memory test database & client fixtures
│   ├── test_api.py              # Comprehensive REST API tests
│   └── test_seed.py             # Seed data verification test
├── alembic.ini
├── pyproject.toml
├── .env.example
├── seed.py                      # Standalone async script to seed mock security data
└── README.md