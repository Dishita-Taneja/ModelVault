from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.reconciliation import ReconciliationResult
from app.schemas.reconciliation import ReconciliationRunReport, ReconciliationDetailResponse
from app.reconciliation.engine import ReconciliationEngine
from app.core.exceptions import ResourceNotFoundError

router = APIRouter()


@router.post("/run", response_model=ReconciliationRunReport, status_code=200, tags=["Reconciliation"])
async def run_reconciliation(db: AsyncSession = Depends(get_db)):
    """Triggers deterministic timestamp reconciliation across multi-source events."""
    engine = ReconciliationEngine(db)
    return await engine.reconcile_all()


@router.get("/", response_model=List[ReconciliationDetailResponse], tags=["Reconciliation"])
async def list_reconciliations(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Retrieves all timestamp reconciliation audit details."""
    res = await db.execute(select(ReconciliationResult).offset(skip).limit(limit))
    return list(res.scalars().all())


@router.get("/{event_id}", response_model=ReconciliationDetailResponse, tags=["Reconciliation"])
async def get_reconciliation_detail(event_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves auditable timestamp reconciliation details for a specific event_id."""
    res = await db.execute(select(ReconciliationResult).where(ReconciliationResult.event_id == event_id))
    detail = res.scalars().first()
    if not detail:
        raise ResourceNotFoundError(resource="ReconciliationDetail", identifier=event_id)
    return detail
