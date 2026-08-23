import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NormalizedEventBase(BaseModel):
    source: str
    event_time_raw: datetime.datetime
    event_time_reconciled: datetime.datetime
    user_id: str | None = None
    user_name: str | None = None
    ip_address: str | None = None
    event_name: str
    model_id: str | None = None
    region: str | None = "us-east-1"
    status: str = "SUCCESS"
    bytes_transferred: int = 0
    risk_score: float = 0.0
    anomaly_flag: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)


class NormalizedEventCreate(NormalizedEventBase):
    event_id: str


class NormalizedEventResponse(NormalizedEventBase):
    event_id: str

    model_config = ConfigDict(from_attributes=True)


class RawLogIngestionRequest(BaseModel):
    log_source: str  # IAM, EC2, S3, MODEL
    payload: dict[str, Any]


class IngestionReport(BaseModel):
    status: str = "COMPLETED"
    total_files_processed: int = 0
    records_processed: dict[str, int] = Field(default_factory=dict)
    records_inserted: dict[str, int] = Field(default_factory=dict)
    duplicates_skipped: dict[str, int] = Field(default_factory=dict)
    invalid_records: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
