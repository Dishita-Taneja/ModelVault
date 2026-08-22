import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import Base
from app.ingestion.service import IngestionService
from app.core.logging import logger


async def seed_data():
    db_url = settings.async_database_url
    try:
        engine = create_async_engine(db_url, echo=False, future=True)
        async with engine.connect() as conn:
            pass
    except Exception as e:
        logger.warning(f"PostgreSQL connection check ({e}). Using local SQLite database 'modelvault_dev.db'...")
        db_url = "sqlite+aiosqlite:///./modelvault_dev.db"
        engine = create_async_engine(db_url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from sqlalchemy.ext.asyncio import async_sessionmaker
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    service = IngestionService()
    async with SessionLocal() as session:
        report = await service.run(session)
        logger.info(f"Seed ingestion report: {report}")

    await engine.dispose()
    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_data())
