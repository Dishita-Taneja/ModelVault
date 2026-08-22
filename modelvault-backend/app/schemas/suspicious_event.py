import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class SuspiciousEventResponse(BaseModel):
    event_id: str
    user_id: Optional[str] = None
    model_id: Optional[str] = None
    timestamp: datetime.datetime
    risk_score: float
    severity: str
    anomaly_score: float
    weight_exfiltration_suspected: bool
    exfiltration_confidence: float
    production_usage_detected: bool
    reason: str
    evidence: List[str] = Field(default_factory=list)
    related_events: List[str] = Field(default_factory=list)
    investigation_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    detected_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineExecutionReport(BaseModel):
    status: str = "COMPLETED"
    execution_time_ms: float
    total_events_processed: int
    reconciled_count: int
    anomalous_count: int
    exfiltration_suspected_count: int
    suspicious_events_generated: int
    top_suspicious_events: List[SuspiciousEventResponse] = Field(default_factory=list)
