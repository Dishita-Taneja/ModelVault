from app.core.database import get_db
from app.correlation.engine import CrossSourceCorrelationEngine
from app.schemas.investigation import InvestigationTimelineResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/model/{model_id}", response_model=InvestigationTimelineResponse, tags=["Investigations & Correlation"])
async def get_model_investigation(model_id: str, db: AsyncSession = Depends(get_db)):
    """Reconstructs an auditable cross-source security timeline for a specific ML model."""
    engine = CrossSourceCorrelationEngine(db)
    return await engine.correlate_by_model(model_id)


@router.get("/user/{user_id}", response_model=InvestigationTimelineResponse, tags=["Investigations & Correlation"])
async def get_user_investigation(user_id: str, db: AsyncSession = Depends(get_db)):
    """Reconstructs an auditable cross-source security timeline for a specific User."""
    engine = CrossSourceCorrelationEngine(db)
    return await engine.correlate_by_user(user_id)


@router.get("/event/{event_id}", response_model=InvestigationTimelineResponse, tags=["Investigations & Correlation"])
async def get_event_investigation(event_id: str, db: AsyncSession = Depends(get_db)):
    """Reconstructs an auditable cross-source security timeline centered on a specific suspicious Event."""
    engine = CrossSourceCorrelationEngine(db)
    return await engine.correlate_by_event(event_id)
