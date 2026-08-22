from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.event import IngestionReport
from app.ingestion.service import IngestionService

router = APIRouter()


@router.post("/run", response_model=IngestionReport, status_code=200, tags=["Ingestion"])
async def trigger_ingestion(db: AsyncSession = Depends(get_db)):
    """Triggers dataset ingestion pipeline for all organizer datasets in data/."""
    service = IngestionService()
    return await service.run(db)
