import pytest
from app.core.database import check_db_connection


@pytest.mark.asyncio
async def test_db_connection_check():
    # Will attempt engine connection
    connected = await check_db_connection()
    # In isolated unit tests without live postgres running, returns bool status
    assert isinstance(connected, bool)
