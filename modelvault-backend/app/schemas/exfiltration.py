import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExfiltrationResponse(BaseModel):
    event_id: str
    weight_exfiltration_suspected: bool
    confidence: float
    risk_score: float
    evidence: List[str] = Field(default_factory=list)
    reason: str
    related_events: List[str] = Field(default_factory=list)
    assessed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
