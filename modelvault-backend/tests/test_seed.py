import pytest
from seed import seed_data
from tests.conftest import TestSessionLocal, test_engine
from app.models.user import User
from app.models.model import MLModel
from app.models.access_event import AccessEvent
from app.models.anomaly_result import AnomalyResult
from sqlalchemy import select


@pytest.mark.asyncio
async def test_seed_script_execution():
    # Execute seed_data against test SQLite DB
    await seed_data(custom_engine=test_engine, custom_session_factory=TestSessionLocal)

    async with TestSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
        assert len(users) == 3
        usernames = [u.username for u in users]
        assert "alice.chen" in usernames
        assert "bob.martinez" in usernames
        assert "eve.thorne" in usernames

        models = (await session.execute(select(MLModel))).scalars().all()
        assert len(models) == 4

        events = (await session.execute(select(AccessEvent))).scalars().all()
        assert len(events) == 6

        anomalies = (await session.execute(select(AnomalyResult).order_by(AnomalyResult.anomaly_score.desc()))).scalars().all()
        assert len(anomalies) == 3
        assert anomalies[0].anomaly_score == 0.98

    # Running seed a second time should skip without error
    await seed_data(custom_engine=test_engine, custom_session_factory=TestSessionLocal)
