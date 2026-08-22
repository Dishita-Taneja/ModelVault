import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class TimelineEvent(BaseModel):
    event_id: str
    source: str
    timestamp: datetime.datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    model_id: Optional[str] = None
    event_name: str
    ip_address: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    anomaly_score: Optional[float] = 0.0
    is_anomaly: bool = False
    reconciled_offset_seconds: float = 0.0
    exfiltration_suspected: bool = False
    exfiltration_confidence: float = 0.0
    correlation_reason: str

    model_config = ConfigDict(from_attributes=True)


class InvestigationTimelineResponse(BaseModel):
    incident_id: str
    target_type: str
    target_id: str
    severity: str
    summary: str
    total_events_count: int
    anomalous_events_count: int
    max_anomaly_score: float
    timeline: List[TimelineEvent] = Field(default_factory=list)
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
