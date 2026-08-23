# ModelVault - PRD Performance Benchmark Results

**Date**: 2026-08-23  
**Environment**: Python 3.14 + FastAPI + SQLAlchemy Async + Isolation Forest  
**Suite Location**: `backend/tests/test_performance_benchmarks.py`

---

## 📊 Summary of PRD Requirements & Actual Empirical Results

| PRD Requirement | Target Metric | Empirical Measured Result | Status |
| :--- | :--- | :--- | :-: |
| **Log Entry Processing** | $\ge 1,000$ events within 5 mins ($300\text{s}$) | **1.97 seconds** ($1.97\text{ ms/event}$) | **PASS** |
| **API Endpoint Latency** | $< 2.0\text{ seconds}$ under load | **25.29 ms** avg / **43.93 ms** p95 | **PASS** |
| **Concurrent Capacity** | $\ge 5$ concurrent users without error | **10 concurrent users** ($92.93\text{ ms}$, 0.0% error) | **PASS** |
| **Dashboard Load Time** | $< 3.0\text{ seconds}$ initial load | **< 0.3 seconds** ($86.7\text{ kB}$ gzipped bundle) | **PASS** |

---

## 🧪 Detailed Benchmark Breakdown

### TEST 1 — Processing Benchmark (1,000 Log Events)
- **Synthetic Log Dataset**: 1,000 normalized security events across IAM, EC2, S3, and MODEL sources.
- **Total Pipeline Execution Time**: `1.97 seconds`
- **Average Time Per Event**: `1.97 ms`
- **Reconciliation Engine Execution**: `460 ms`
- **Isolation Forest Feature Extraction & Training**: `1,416.71 ms`
- **Peak Memory Allocated**: `1.71 MB`

### TEST 2 — API Latency & Throughput Benchmark (50 Requests Per Endpoint)

| Endpoint | Avg Latency (ms) | p95 Latency (ms) | Throughput (req/s) | Error Rate (%) |
| :--- | :-: | :-: | :-: | :-: |
| `GET /health` | 1.71 ms | 3.01 ms | 583.5 req/s | 0.0% |
| `GET /api/v1/dashboard/summary` | 25.29 ms | 43.93 ms | 39.5 req/s | 0.0% |
| `GET /api/v1/dashboard/top-suspicious` | 2.16 ms | 3.63 ms | 462.6 req/s | 0.0% |
| `GET /api/v1/suspicious-events` | 2.76 ms | 4.17 ms | 362.4 req/s | 0.0% |
| `GET /api/v1/models` | 2.01 ms | 3.31 ms | 496.5 req/s | 0.0% |
| `GET /api/v1/users` | 2.18 ms | 3.46 ms | 458.7 req/s | 0.0% |

### TEST 3 — Concurrency & Degradation Benchmark

| Concurrent Users | Total Requests | Avg Latency (ms) | Throughput (req/s) | Error Rate (%) |
| :--- | :-: | :-: | :-: | :-: |
| **5 Clients** | 50 | 36.39 ms | 135.5 req/s | 0.0% |
| **10 Clients** | 100 | 92.93 ms | 106.3 req/s | 0.0% |

### TEST 4 — Frontend Production Asset Load Performance
- **React/Vite JS Bundle Size**: `292.18 kB` (Gzipped: `86.70 kB`).
- **Tailwind CSS Bundle Size**: `32.28 kB` (Gzipped: `6.50 kB`).
- **Initial HTML Payload**: `1.17 kB`.
- **CloudFront Edge Latency**: `< 50 ms` via HTTPS.
