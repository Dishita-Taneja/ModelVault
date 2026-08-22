import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class AnomalyResultBase(BaseModel):
    access_event_id: uuid.UUID = Field(..., description="ID of the flagged access event")
    anomaly_score: float = Field(..., ge=0.0, description="Calculated anomaly score (e.g. 0.0 to 1.0 or unbounded float)")
    reason: str | None = Field(default=None, description="Explanation or classification for the anomaly")
    flagged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the event was flagged as anomalous",
    )


class AnomalyResultCreate(AnomalyResultBase):
    pass


class AnomalyResultRead(AnomalyResultBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
