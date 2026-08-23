import datetime

from pydantic import BaseModel, ConfigDict, Field


class TrainRequest(BaseModel):
    contamination: float = Field(default=0.33, ge=0.01, le=0.5)
    model_version: str = "v1.0.0"


class TrainResponse(BaseModel):
    status: str = "SUCCESS"
    model_version: str = "v1.0.0"
    training_time_ms: float
    total_events: int
    flagged_anomalous_count: int
    threshold: float
    anomaly_score_distribution: dict[str, float]


class AnomalyResultResponse(BaseModel):
    event_id: str
    user_id: str | None = None
    model_id: str | None = None
    source: str
    anomaly_score: float
    is_anomaly: bool
    feature_values: dict[str, float] = Field(default_factory=dict)
    model_version: str
    detected_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DetectionReportResponse(BaseModel):
    status: str = "COMPLETED"
    detection_time_ms: float
    total_events_evaluated: int
    anomalies_detected_count: int
    results: list[AnomalyResultResponse] = Field(default_factory=list)
