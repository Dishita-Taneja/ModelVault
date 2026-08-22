import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, engine
from app.models.base import Base
from app.models.user import User
from app.models.model import MLModel
from app.models.access_event import AccessEvent
from app.models.anomaly_result import AnomalyResult


async def seed_data(
    custom_engine=None,
    custom_session_factory=None,
) -> None:
    db_engine = custom_engine or engine
    db_session_factory = custom_session_factory or async_session_factory

    print("Connecting to database and creating tables if not present...")
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with db_session_factory() as session:
        print("Checking existing data...")
        # Check if already seeded
        from sqlalchemy import select
        existing_users = await session.execute(select(User))
        if existing_users.scalars().first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding users...")
        user_alice = User(
            id=uuid.uuid4(),
            username="alice.chen",
            email="alice.chen@modelvault.io",
            role="Principal ML Scientist",
            department="Research & AI Safety",
        )
        user_bob = User(
            id=uuid.uuid4(),
            username="bob.martinez",
            email="bob.martinez@modelvault.io",
            role="MLOps Platform Lead",
            department="Infrastructure",
        )
        user_eve = User(
            id=uuid.uuid4(),
            username="eve.thorne",
            email="eve.thorne@external-vendor.com",
            role="Data Annotator",
            department="External Contracting",
        )
        session.add_all([user_alice, user_bob, user_eve])
        await session.flush()

        print("Seeding ML models...")
        model_fraud = MLModel(
            id=uuid.uuid4(),
            name="fraud-detection-transformer-v3",
            description="Core real-time credit transaction fraud classification engine",
            owner_id=user_alice.id,
            sensitivity_level="CRITICAL",
        )
        model_credit = MLModel(
            id=uuid.uuid4(),
            name="credit-risk-scoring-v2",
            description="Underwriting credit risk scoring and limit evaluation model",
            owner_id=user_alice.id,
            sensitivity_level="HIGH",
        )
        model_churn = MLModel(
            id=uuid.uuid4(),
            name="customer-churn-xgb",
            description="Customer retention probability scoring model",
            owner_id=user_bob.id,
            sensitivity_level="LOW",
        )
        model_copilot = MLModel(
            id=uuid.uuid4(),
            name="internal-enterprise-llm-weights",
            description="Proprietary fine-tuned weights for internal enterprise copilot",
            owner_id=user_bob.id,
            sensitivity_level="CRITICAL",
        )
        session.add_all([model_fraud, model_credit, model_churn, model_copilot])
        await session.flush()

        print("Seeding access events and anomaly results...")
        now = datetime.now(timezone.utc)

        # 1. Normal inference event
        event_1 = AccessEvent(
            id=uuid.uuid4(),
            user_id=user_alice.id,
            model_id=model_fraud.id,
            action="inference",
            timestamp=now - timedelta(hours=5),
            source="API_GATEWAY",
            raw_metadata={
                "ip_address": "10.0.4.12",
                "request_id": "req-9912a",
                "payload_size_kb": 12,
                "latency_ms": 45,
            },
        )

        # 2. Normal model weights download during deploy
        event_2 = AccessEvent(
            id=uuid.uuid4(),
            user_id=user_bob.id,
            model_id=model_churn.id,
            action="download",
            timestamp=now - timedelta(hours=4),
            source="EC2",
            raw_metadata={
                "ip_address": "10.0.12.80",
                "instance_id": "i-098234857234",
                "cluster": "prod-us-east-1",
            },
        )

        # 3. Suspicious mass export #1 (Top 1)
        event_3_suspicious = AccessEvent(
            id=uuid.uuid4(),
            user_id=user_eve.id,
            model_id=model_copilot.id,
            action="download",
            timestamp=now - timedelta(hours=3, minutes=15),
            source="S3",
            raw_metadata={
                "ip_address": "198.51.100.42",
                "bytes_transferred": 14500000000,
                "user_agent": "aws-sdk-go/v1.44.0 (custom-cli)",
                "bucket": "s3://modelvault-weights-private",
                "geo_location": "Unknown/Proxy",
                "warning": "Bulk object retrieval detected",
            },
        )

        # 4. Suspicious direct export #2 (Top 2)
        event_4_suspicious = AccessEvent(
            id=uuid.uuid4(),
            user_id=user_eve.id,
            model_id=model_fraud.id,
            action="export",
            timestamp=now - timedelta(hours=2, minutes=45),
            source="IAM",
            raw_metadata={
                "ip_address": "203.0.113.19",
                "policy_overridden": True,
                "role_assumed": "arn:aws:iam::123456789012:role/EmergencyAccess",
                "reason_provided": "Ad-hoc debugging",
            },
        )

        # 5. Suspicious abnormal inference rate #3 (Top 3)
        event_5_suspicious = AccessEvent(
            id=uuid.uuid4(),
            user_id=user_eve.id,
            model_id=model_credit.id,
            action="inference",
            timestamp=now - timedelta(hours=1, minutes=10),
            source="API_GATEWAY",
            raw_metadata={
                "ip_address": "198.51.100.42",
                "requests_per_second": 450,
                "token_count": 1200000,
                "flag": "High volume extraction probe",
            },
        )

        # 6. Routine read event
        event_6 = AccessEvent(
            id=uuid.uuid4(),
            user_id=user_alice.id,
            model_id=model_credit.id,
            action="read",
            timestamp=now - timedelta(minutes=20),
            source="API_GATEWAY",
            raw_metadata={
                "ip_address": "10.0.4.12",
                "user_agent": "Mozilla/5.0 (Macintosh)",
            },
        )

        session.add_all([
            event_1, event_2, event_3_suspicious,
            event_4_suspicious, event_5_suspicious, event_6
        ])
        await session.flush()

        # Flagged anomaly results for the suspicious events
        anomaly_1 = AnomalyResult(
            id=uuid.uuid4(),
            access_event_id=event_3_suspicious.id,
            anomaly_score=0.98,
            reason="Massive unauthorized model weight download (14.5GB) via direct S3 API from untrusted proxy IP outside business hours.",
            flagged_at=now - timedelta(hours=3, minutes=14),
        )
        anomaly_2 = AnomalyResult(
            id=uuid.uuid4(),
            access_event_id=event_4_suspicious.id,
            anomaly_score=0.91,
            reason="Unauthorized elevation of privilege assuming EmergencyAccess role to export critical fraud detection model.",
            flagged_at=now - timedelta(hours=2, minutes=44),
        )
        anomaly_3 = AnomalyResult(
            id=uuid.uuid4(),
            access_event_id=event_5_suspicious.id,
            anomaly_score=0.84,
            reason="Extreme query rate anomaly (450 req/sec) consistent with model extraction / model inversion attack pattern.",
            flagged_at=now - timedelta(hours=1, minutes=9),
        )

        session.add_all([anomaly_1, anomaly_2, anomaly_3])
        await session.commit()

        print("Seed data successfully inserted into the database!")


if __name__ == "__main__":
    asyncio.run(seed_data())
