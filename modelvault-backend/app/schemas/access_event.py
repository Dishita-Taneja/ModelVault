import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AccessEventBase(BaseModel):
    user_id: uuid.UUID | None = Field(default=None, description="User ID performing the action, nullable if system/unauthenticated")
    model_id: uuid.UUID = Field(..., description="Target ML model ID")
    action: str = Field(..., description="Action performed, e.g. read, download, inference, export")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the access event",
    )
    source: str = Field(
        default="API_GATEWAY",
        description="Origin source of the event, e.g. S3, IAM, EC2, API_GATEWAY",
    )
    raw_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary raw metadata payload stored as JSONB",
    )


class AccessEventCreate(AccessEventBase):
    pass


class AccessEventRead(AccessEventBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
