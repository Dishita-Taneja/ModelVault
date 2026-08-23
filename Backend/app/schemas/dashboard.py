
from app.schemas.suspicious_event import SuspiciousEventResponse
from pydantic import BaseModel, ConfigDict, Field


class DashboardSummaryResponse(BaseModel):
    total_models: int
    total_users: int
    total_events: int
    anomalous_events: int
    suspicious_events: int
    critical_events: int
    models_at_risk: int
    exfiltration_suspected_events: int
    production_usage_events: int
    top_suspicious_events: list[SuspiciousEventResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
