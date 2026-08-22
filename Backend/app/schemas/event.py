import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class NormalizedEventBase(BaseModel):
    source: str
    event_time_raw: datetime.datetime
    event_time_reconciled: datetime.datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    ip_address: Optional[str] = None
    event_name: str
    model_id: Optional[str] = None
    region: Optional[str] = "us-east-1"
    status: str = "SUCCESS"
    bytes_transferred: int = 0
    risk_score: float = 0.0
    anomaly_flag: bool = False
    extra: Dict[str, Any] = Field(default_factory=dict)


class NormalizedEventCreate(NormalizedEventBase):
    event_id: str


class NormalizedEventResponse(NormalizedEventBase):
    event_id: str

    model_config = ConfigDict(from_attributes=True)


class RawLogIngestionRequest(BaseModel):
    log_source: str  # IAM, EC2, S3, MODEL
    payload: Dict[str, Any]


class IngestionReport(BaseModel):
    status: str = "COMPLETED"
    total_files_processed: int = 0
    records_processed: Dict[str, int] = Field(default_factory=dict)
    records_inserted: Dict[str, int] = Field(default_factory=dict)
    duplicates_skipped: Dict[str, int] = Field(default_factory=dict)
    invalid_records: Dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
