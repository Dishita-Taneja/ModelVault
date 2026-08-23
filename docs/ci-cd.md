# ModelVault - Automated Production CI/CD Pipeline Documentation

**Workflow File**: `.github/workflows/ci-cd.yml`  
**Authentication**: GitHub OIDC Role Assumption (`AWS_ROLE_ARN`) or GitHub Secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).  
**Triggers**: Automatic execution on `push` or `pull_request` to `main` / `master` branches.

---

## 1. Pipeline Stages & Execution Flow

```
                      GitHub Commit / Push (main)
                                 │
         ┌───────────────────────┴───────────────────────┐
         │                                               │
┌────────▼────────┐                             ┌────────▼────────┐
│ 1. Backend Test │                             │ 2. Frontend     │
│   & Code Lint   │                             │   Test & Build  │
└────────┬────────┘                             └────────┬────────┘
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 │
                       ┌─────────▼─────────┐
                       │ 3. Terraform      │
                       │   Validation      │
                       └─────────┬─────────┘
                                 │
                       ┌─────────▼─────────┐
                       │ 4. Docker Build   │
                       │   & ECR Push      │
                       └─────────┬─────────┘
                                 │
                       ┌─────────▼─────────┐
                       │ 5. ECS Deployment │
                       │   & Frontend S3   │
                       │   & Health Check  │
                       └───────────────────┘
```

### Complete 13-Step Production Deployment Sequence:

1. **Backend Dependency Installation**: Executes `pip install -r backend/requirements.txt`.
2. **Backend Test Suite**: Executes `python -m pytest tests -v` in `backend/` (37 unit/integration tests).
3. **Backend Code Quality Check**: Executes `python -m ruff check backend/app backend/tests`.
4. **Frontend Dependency Installation**: Executes `npm ci` in `frontend/`.
5. **Frontend Production Build**: Executes `npm run build` in `frontend/`.
6. **Terraform Formatting Check**: Executes `terraform fmt -check` in `terraform/`.
7. **Terraform Syntax & Spec Validation**: Executes `terraform init -backend=false && terraform validate` in `terraform/`.
8. **Docker Multi-Stage Build**: Builds `backend/Dockerfile` with non-root security context.
9. **Amazon ECR Push**: Tags image with Git commit SHA and `:latest`, pushing to Amazon ECR.
10. **AWS ECS Fargate Deployment**: Forces rolling zero-downtime container update (`aws ecs update-service --force-new-deployment`).
11. **Frontend Asset Sync**: Syncs `frontend/dist/` assets to `s3://${FRONTEND_S3_BUCKET}` with `--delete`.
12. **CloudFront CDN Cache Invalidation**: Invalidates CloudFront edge cache (`aws cloudfront create-invalidation --paths "/*"`).
13. **Endpoint Health Check**: Verifies endpoint response `GET ${ALB_URL}/health` returning HTTP 200 `{"status":"ok"}`.

---

## 2. Fail-Fast Security Criteria

The pipeline enforces strict zero-tolerance failure criteria:
- **Backend Test Failure**: Stops pipeline if any pytest assertion fails.
- **Frontend Compilation Error**: Stops pipeline if Vite build fails.
- **Lint / Code Quality Violation**: Fails job if unhandled Ruff errors occur.
- **Terraform Validation Error**: Prevents container build if HCL configuration is invalid.
- **Deployment Instability**: Fails job if ECS service fails to achieve stable state within timeout.

---

## 3. Required GitHub Secrets

Configure the following secrets in GitHub Repository Settings $\rightarrow$ Secrets and Variables $\rightarrow$ Actions:

| Secret Name | Purpose | Required |
| :--- | :--- | :-: |
| `AWS_ROLE_ARN` | GitHub OIDC IAM Role ARN for keyless AWS authentication | Recommended |
| `AWS_ACCESS_KEY_ID` | AWS IAM Deployer Access Key | Optional (if OIDC not used) |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM Deployer Secret Key | Optional (if OIDC not used) |
| `AWS_REGION` | Target AWS Region (default: `us-east-1`) | Yes |
| `FRONTEND_S3_BUCKET` | Production S3 Frontend Asset Bucket Name | Yes |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront CDN Distribution ID for Cache Invalidation | Yes |
| `ALB_URL` | Public Application Load Balancer HTTPS Endpoint URL | Yes |
