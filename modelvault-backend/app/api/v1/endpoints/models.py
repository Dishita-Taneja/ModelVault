from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.model import MLModelResponse, MLModelCreate
from app.schemas.investigation import InvestigationTimelineResponse
from app.correlation.engine import CrossSourceCorrelationEngine
from app.crud import crud_model
from app.core.exceptions import ResourceNotFoundError

router = APIRouter()


@router.get("", response_model=List[MLModelResponse], tags=["Models"])
@router.get("/", response_model=List[MLModelResponse], tags=["Models"])
async def list_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    sensitivity_level: Optional[str] = Query(None, description="Filter by sensitivity: CRITICAL, HIGH, MEDIUM, LOW"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all registered ML models with optional sensitivity filtering and pagination."""
    models = await crud_model.get_all_models(db, skip=skip, limit=limit)
    if sensitivity_level:
        models = [m for m in models if m.sensitivity_level.upper() == sensitivity_level.upper()]
    return models


@router.get("/{id}/investigation", response_model=InvestigationTimelineResponse, tags=["Models"])
async def get_model_investigation_shortcut(id: str, db: AsyncSession = Depends(get_db)):
    """Reconstructs cross-source security investigation timeline for a specific ML Model ID."""
    engine = CrossSourceCorrelationEngine(db)
    return await engine.correlate_by_model(id)


@router.get("/{id}", response_model=MLModelResponse, tags=["Models"])
async def get_model(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves metadata for a specific ML model by ID."""
    model = await crud_model.get_model_by_id(db, model_id=id)
    if not model:
        raise ResourceNotFoundError(resource="MLModel", identifier=id)
    return model


@router.post("", response_model=MLModelResponse, status_code=201, tags=["Models"])
@router.post("/", response_model=MLModelResponse, status_code=201, tags=["Models"])
async def create_model(model_in: MLModelCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new ML model in ModelVault metadata repository."""
    return await crud_model.create_model(db, model_in=model_in)
