import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict
from app.schemas.access_event import AccessEventRead


class SuspiciousAccessEventRead(BaseModel):
    id: uuid.UUID
    access_event_id: uuid.UUID
    anomaly_score: float
    reason: str | None = None
    flagged_at: datetime
    access_event: AccessEventRead

    model_config = ConfigDict(from_attributes=True)
