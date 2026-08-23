import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReconciliationDetailResponse(BaseModel):
    event_id: str
    log_source: str
    event_time_raw: datetime.datetime
    event_time_normalized: datetime.datetime
    event_time_reconciled: datetime.datetime
    timestamp_offset_seconds: float
    confidence_score: float
    reconciliation_method: str
    reason_for_change: str
    source_events_used: list[str] = Field(default_factory=list)
    reconciled_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ReconciliationRunReport(BaseModel):
    status: str = "COMPLETED"
    total_events_reconciled: int = 0
    high_confidence_count: int = 0
    offsets_applied_count: int = 0
    method_breakdown: dict = Field(default_factory=dict)
    details: list[ReconciliationDetailResponse] = Field(default_factory=list)
