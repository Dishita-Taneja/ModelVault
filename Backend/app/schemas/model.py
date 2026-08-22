import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MLModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    framework: str = "PyTorch"
    s3_uri: str
    sensitivity_level: str = "HIGH"
    owner_id: Optional[str] = None
    owner_email: Optional[str] = None


class MLModelCreate(MLModelBase):
    model_id: str


class MLModelResponse(MLModelBase):
    model_id: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
