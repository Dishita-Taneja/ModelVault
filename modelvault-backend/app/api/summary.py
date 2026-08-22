from collections.abc import Sequence
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import summary as crud_summary
from app.schemas.summary import SuspiciousAccessEventRead

router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get("/top-suspicious", response_model=list[SuspiciousAccessEventRead], summary="Get top suspicious access events")
async def get_top_suspicious(
    limit: int = Query(3, ge=1, le=50, description="Number of top suspicious records to return"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[SuspiciousAccessEventRead]:
    top_events = await crud_summary.get_top_suspicious_events(db, limit=limit)
    return top_events
