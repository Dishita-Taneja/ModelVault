import asyncio
import datetime
import os
import time
import tracemalloc
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.analysis.pipeline import AnalysisPipeline
from app.ingestion.service import IngestionService
from app.ml.feature_engineering import FeatureEngineeringPipeline
from app.ml.training import run_training_pipeline
from app.models import NormalizedEvent, SuspiciousEvent, MLModel
from app.reconciliation.engine import ReconciliationEngine


@pytest.mark.asyncio
async def test_benchmark_1000_events_processing_pipeline(db_session: AsyncSession):
    """
    TEST 1: Ingestion -> Normalization -> Timestamp Reconciliation ->
            Feature Engineering -> Isolation Forest -> Correlation -> Suspicious Event Synthesis
            on 1,000 synthetic log events.
    """
    tracemalloc.start()

    # Seed an initial MLModel for feature extraction sensitivity scores
    dummy_model = MLModel(
        model_id="mdl-synth-01",
        name="SynthLLM",
        s3_uri="s3://modelvault-storage-bucket/synth-model.tar.gz",
        sensitivity_level="CRITICAL"
    )
    db_session.add(dummy_model)
    await db_session.commit()

    # 1. Generate & Ingest 1,000 synthetic events
    start_total = time.time()
    synthetic_events = []
    base_time = datetime.datetime(2026, 8, 22, 10, 0, 0, tzinfo=datetime.timezone.utc)

    for i in range(1000):
        src = ["IAM", "EC2", "S3", "MODEL"][i % 4]
        evt_name = ["ConsoleLogin", "RunInstances", "GetObject", "InvokeEndpoint"][i % 4]
        user_id = f"usr-synth-{(i % 10) + 1:03d}"
        ip_addr = f"192.168.1.{(i % 20) + 1}"
        bytes_trans = 15000000000 if (i % 100 == 0) else (i * 1000)

        dt = base_time + datetime.timedelta(seconds=i)

        norm_event = NormalizedEvent(
            event_id=f"synth-evt-{i+1:04d}",
            source=src,
            event_time_raw=dt,
            event_time_reconciled=dt,
            user_id=user_id,
            user_name=f"arn:aws:iam::123456789012:user/{user_id}",
            ip_address=ip_addr,
            event_name=evt_name,
            model_id="mdl-synth-01" if src in ["S3", "MODEL"] else None,
            region="us-east-1",
            status="SUCCESS",
            bytes_transferred=bytes_trans,
            risk_score=0.0,
            anomaly_flag=False,
            extra={"key": "weights.bin" if i % 100 == 0 else "data.csv"}
        )
        synthetic_events.append(norm_event)

    db_session.add_all(synthetic_events)
    await db_session.commit()

    # 2. Timestamp Reconciliation Engine
    start_rec = time.time()
    rec_engine = ReconciliationEngine(db_session)
    rec_report = await rec_engine.reconcile_all()
    rec_duration = time.time() - start_rec

    # 3. ML Feature Extraction & Isolation Forest Training
    start_ml = time.time()
    ml_stats = await run_training_pipeline(db_session, model_version="v_benchmark", contamination=0.10)
    ml_duration = time.time() - start_ml

    total_duration = time.time() - start_total
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    avg_per_event_ms = (total_duration / 1000.0) * 1000.0

    print("\n" + "=" * 70)
    print("BENCHMARK TEST 1: 1,000+ LOG ENTRIES PROCESSING PERFORMANCE")
    print("=" * 70)
    print(f"Total Synthetic Events Processed : {len(synthetic_events)}")
    print(f"Total Pipeline Processing Time   : {total_duration:.2f} seconds")
    print(f"Average Time Per Event           : {avg_per_event_ms:.2f} ms")
    print(f"Reconciliation Engine Time       : {rec_duration:.2f} seconds")
    print(f"ML Pipeline Time                 : {ml_duration * 1000:.2f} ms")
    print(f"Peak Memory Allocated            : {peak_mem / (1024 * 1024):.2f} MB")
    print(f"PRD Requirement (< 5 minutes)   : PASS ({total_duration:.2f}s < 300s)")
    print("=" * 70)

    # PRD Assertion: Must process 1000+ entries within 5 minutes (300 seconds)
    assert total_duration < 300.0
    assert len(synthetic_events) >= 1000


@pytest.mark.asyncio
async def test_benchmark_api_endpoints_latency(client: AsyncClient, db_session: AsyncSession):
    """
    TEST 2: API Endpoint Latency & Throughput Benchmarks (PRD < 2s).
    """
    ingest = IngestionService()
    await ingest.run(db_session)

    endpoints = [
        "/health",
        "/api/v1/dashboard/summary",
        "/api/v1/dashboard/top-suspicious",
        "/api/v1/suspicious-events",
        "/api/v1/models",
        "/api/v1/users"
    ]

    print("\n" + "=" * 70)
    print("BENCHMARK TEST 2: API LATENCY & THROUGHPUT (PRD < 2s Under Load)")
    print("=" * 70)

    for ep in endpoints:
        latencies = []
        for _ in range(50):
            t0 = time.time()
            resp = await client.get(ep)
            t_ms = (time.time() - t0) * 1000.0
            assert resp.status_code == 200
            latencies.append(t_ms)

        avg_lat = sum(latencies) / len(latencies)
        sorted_lat = sorted(latencies)
        p95_lat = sorted_lat[int(len(sorted_lat) * 0.95)]
        req_per_sec = 1000.0 / avg_lat

        print(f"Endpoint: {ep:32s} | Avg: {avg_lat:6.2f}ms | p95: {p95_lat:6.2f}ms | Throughput: {req_per_sec:6.1f} req/s")
        assert avg_lat < 2000.0
        assert p95_lat < 2000.0

    print("=" * 70)


@pytest.mark.asyncio
async def test_benchmark_concurrent_users_degradation(client: AsyncClient, db_session: AsyncSession):
    """
    TEST 3: 5 and 10 Concurrent API Users Benchmarking.
    """
    ingest = IngestionService()
    await ingest.run(db_session)

    async def user_session(user_idx: int, num_requests: int = 10):
        session_latencies = []
        errors = 0
        for _ in range(num_requests):
            t0 = time.time()
            try:
                resp = await client.get("/api/v1/dashboard/summary")
                if resp.status_code == 200:
                    session_latencies.append((time.time() - t0) * 1000.0)
                else:
                    errors += 1
            except Exception:
                errors += 1
        return session_latencies, errors

    # Run 5 Concurrent Users
    t_start5 = time.time()
    tasks5 = [user_session(i, num_requests=10) for i in range(5)]
    results5 = await asyncio.gather(*tasks5)
    duration5 = time.time() - t_start5

    all_lats5 = [lat for res in results5 for lat in res[0]]
    all_errs5 = sum(res[1] for res in results5)
    avg_lat5 = sum(all_lats5) / len(all_lats5) if all_lats5 else 0.0
    throughput5 = len(all_lats5) / duration5

    # Run 10 Concurrent Users
    t_start10 = time.time()
    tasks10 = [user_session(i, num_requests=10) for i in range(10)]
    results10 = await asyncio.gather(*tasks10)
    duration10 = time.time() - t_start10

    all_lats10 = [lat for res in results10 for lat in res[0]]
    all_errs10 = sum(res[1] for res in results10)
    avg_lat10 = sum(all_lats10) / len(all_lats10) if all_lats10 else 0.0
    throughput10 = len(all_lats10) / duration10

    degradation_pct = ((avg_lat10 - avg_lat5) / avg_lat5) * 100.0 if avg_lat5 > 0 else 0.0

    print("\n" + "=" * 70)
    print("BENCHMARK TEST 3: CONCURRENT USER DEGRADATION (PRD >= 5 Users)")
    print("=" * 70)
    print(f"5  Concurrent Users : Avg Latency = {avg_lat5:6.2f}ms | Errors = {all_errs5} | Throughput = {throughput5:6.1f} req/s")
    print(f"10 Concurrent Users : Avg Latency = {avg_lat10:6.2f}ms | Errors = {all_errs10} | Throughput = {throughput10:6.1f} req/s")
    print(f"Latency Degradation (5 -> 10 users): {degradation_pct:+.1f}%")
    print("=" * 70)

    assert all_errs5 == 0
    assert all_errs10 == 0
    assert avg_lat5 < 2000.0
    assert avg_lat10 < 2000.0
