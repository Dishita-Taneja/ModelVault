# ModelVault - Cybersecurity Platform & ML Threat Detection Engine

ModelVault helps security analysts identify suspicious access to ML models after an identity compromise by ingesting cloud/model logs, reconciling cross-source timestamps, executing unsupervised Isolation Forest anomaly detection, correlating identity timelines, and detecting model weight exfiltration attempts.

---

## 🏗️ Architecture & Component Overview

```
ModelVault/
├── backend/                # FastAPI Backend & ML Analytics Service
│   ├── app/
│   │   ├── api/            # API v1 REST Endpoints
│   │   ├── core/           # Database, Logging, Configuration
│   │   ├── crud/           # Async SQLAlchemy CRUD operations
│   │   ├── models/         # SQLAlchemy ORM Data Models
│   │   ├── schemas/        # Pydantic Schemas & Contracts
│   │   ├── ingestion/      # Multi-Source Ingestion & Evidence Preservation
│   │   ├── reconciliation/ # Deterministic Timestamp Reconciliation Engine
│   │   ├── ml/             # Feature Engineering & Isolation Forest Detector
│   │   ├── correlation/    # Cross-Source Incident Correlation Engine
│   │   ├── exfiltration/   # Model-Weight Exfiltration Assessment
│   │   ├── analysis/       # Complete End-to-End Analysis Pipeline Service
│   │   └── main.py         # Application Entrypoint
│   ├── alembic/            # Database Migrations
│   ├── tests/              # Full Test Suite (pytest-asyncio)
│   ├── Dockerfile          # Production Multi-Stage Dockerfile (Non-Root User)
│   ├── docker-compose.yml  # Local Container Orchestration with PostgreSQL
│   └── docker-entrypoint.sh # Container Bootstrap (Migrations & Startup)
├── frontend/               # React SOC Security Dashboard (Tailwind, Lucide, Vite)
├── data/                   # Organizer-Provided Actual Security Log Datasets
├── terraform/              # Reusable AWS IaC Configuration (ECS Fargate, RDS, S3, ALB, ECR)
├── .github/workflows/      # Production CI/CD Deployment Pipeline (GitHub Actions)
└── docs/                   # Technical Documentation & Pipeline Diagrams
```

---

## 🚀 Quickstart: Local Docker Deployment

Start PostgreSQL and the ModelVault API backend container in a single step:

```bash
cd backend
docker-compose up --build -d
```

### Automatic Bootstrap Sequence
When the container starts:
1. Waits for PostgreSQL database readiness (`pg_isready`).
2. Applies database migrations automatically (`alembic upgrade head`).
3. Loads all actual organizer logs from `data/` and runs initial analysis.
4. Starts Uvicorn production ASGI server at `http://localhost:8000`.

### Verification Endpoints
- **Service Health**: `GET http://localhost:8000/health`
- **Dashboard Metrics**: `GET http://localhost:8000/api/v1/dashboard/summary`
- **Run Full Pipeline**: `POST http://localhost:8000/api/v1/analysis/run`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Frontend Dashboard**: `http://localhost:5173/`

---

## ☁️ AWS Infrastructure & Production Deployment

ModelVault utilizes an enterprise-grade, non-public AWS architecture managed entirely via Terraform.

```
                    Internet
                       │
             ┌─────────▼─────────┐
             │ Application Load  │
             │  Balancer (ALB)   │
             └─────────┬─────────┘
                       │ (Port 8000)
             ┌─────────▼─────────┐
             │    ECS Fargate    │ ──(IAM)──> S3 Storage Bucket
             │  Container Task   │ ──(Logs)─> CloudWatch Log Group
             └─────────┬─────────┘
                       │ (Port 5432 - Non-Public Subnet)
             ┌─────────▼─────────┐
             │  RDS PostgreSQL   │
             │ Database Instance │
             └───────────────────┘
```

### 1. Reusable Terraform Infrastructure (`terraform/`)

The infrastructure is defined under `terraform/`:

```bash
cd terraform

# 1. Initialize Terraform Providers
terraform init

# 2. Review Execution Plan (Non-Destructive)
terraform plan -var="db_password=YourSecurePassword123!"

# 3. Apply AWS Infrastructure
terraform apply -var="db_password=YourSecurePassword123!" -auto-approve
```

#### Provisioned AWS Resources:
- **VPC & Subnets**: Multi-AZ public subnets for ALB/ECS and private subnets for RDS.
- **Security Groups**: ALB ingress (port 80); ECS task ingress (port 8000 from ALB only); RDS PostgreSQL ingress (port 5432 from ECS only).
- **RDS PostgreSQL**: Non-public `db.t3.micro` instance in private subnet.
- **ECS Fargate**: Managed cluster with container auto-healing and task health checking.
- **S3 Bucket**: Versioned & encrypted bucket for ML models and raw log evidence.
- **CloudWatch**: Log group `/ecs/modelvault-backend` with 30-day retention.

---

## 2. Automated GitHub Actions CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

The CI/CD pipeline triggers automatically on pushes to `main`/`master`:

1. **Test & Lint**: Executes `pytest` test suite and `ruff` linting.
2. **Terraform Validation**: Validates syntax (`terraform validate` and `terraform fmt`).
3. **Docker Build & ECR Push**: Builds production Docker image, tags with Git commit SHA and `:latest`, and pushes to Amazon ECR.
4. **ECS Deployment**: Performs rolling zero-downtime update on ECS Fargate service and executes database migrations.

#### Required GitHub Secrets:
Configure the following secrets in GitHub Repository Settings $\rightarrow$ Secrets and Variables $\rightarrow$ Actions:
- `AWS_ACCESS_KEY_ID`: AWS IAM deployer access key.
- `AWS_SECRET_ACCESS_KEY`: AWS IAM deployer secret key.
- `AWS_REGION`: Target AWS region (e.g. `us-east-1`).

---

## 🧪 Local Testing & Verification

Run the full async test suite locally:

```bash
cd backend
python -m pytest tests -v
```

All 26 unit and integration tests execute against an isolated database environment.
