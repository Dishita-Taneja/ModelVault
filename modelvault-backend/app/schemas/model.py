import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MLModelBase(BaseModel):
    name: str = Field(..., description="Name of the ML model")
    description: str | None = Field(default=None, description="Optional description of the ML model")
    owner_id: uuid.UUID = Field(..., description="User ID of the model owner")
    sensitivity_level: str = Field(
        default="MEDIUM",
        description="Sensitivity classification, e.g. LOW, MEDIUM, HIGH, CRITICAL",
    )


class MLModelCreate(MLModelBase):
    pass


class MLModelRead(MLModelBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
