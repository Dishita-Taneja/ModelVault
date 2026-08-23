import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExfiltrationResponse(BaseModel):
    event_id: str
    weight_exfiltration_suspected: bool
    confidence: float
    risk_score: float
    evidence: list[str] = Field(default_factory=list)
    reason: str
    related_events: list[str] = Field(default_factory=list)
    assessed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
