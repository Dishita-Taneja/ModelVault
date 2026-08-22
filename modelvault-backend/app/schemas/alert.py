import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    event_id: str
    model_id: Optional[str] = None
    user_arn: Optional[str] = None
    risk_score: float
    severity: str = "CRITICAL"
    title: str
    description: str
    status: str = "OPEN"


class AlertCreate(AlertBase):
    alert_id: str


class AlertResponse(AlertBase):
    alert_id: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
