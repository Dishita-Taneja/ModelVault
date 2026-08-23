from app.core.database import get_db
from app.exfiltration.detector import ExfiltrationDetector
from app.schemas.exfiltration import ExfiltrationResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/{event_id}", response_model=ExfiltrationResponse, tags=["Exfiltration Detection"])
async def get_exfiltration_assessment(event_id: str, db: AsyncSession = Depends(get_db)):
    """Evaluates and retrieves auditable model-weight exfiltration assessment for a specific event."""
    detector = ExfiltrationDetector(db)
    return await detector.assess_event(event_id)
