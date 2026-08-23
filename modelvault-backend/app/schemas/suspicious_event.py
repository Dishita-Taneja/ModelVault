import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SuspiciousEventResponse(BaseModel):
    event_id: str
    user_id: str | None = None
    model_id: str | None = None
    timestamp: datetime.datetime
    risk_score: float
    severity: str
    anomaly_score: float
    weight_exfiltration_suspected: bool
    exfiltration_confidence: float
    production_usage_detected: bool
    reason: str
    evidence: list[str] = Field(default_factory=list)
    related_events: list[str] = Field(default_factory=list)
    investigation_timeline: list[dict[str, Any]] = Field(default_factory=list)
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
    top_suspicious_events: list[SuspiciousEventResponse] = Field(default_factory=list)
