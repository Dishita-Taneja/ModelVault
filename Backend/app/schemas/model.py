import datetime

from pydantic import BaseModel, ConfigDict


class MLModelBase(BaseModel):
    name: str
    description: str | None = None
    framework: str = "PyTorch"
    s3_uri: str
    sensitivity_level: str = "HIGH"
    owner_id: str | None = None
    owner_email: str | None = None


class MLModelCreate(MLModelBase):
    model_id: str


class MLModelResponse(MLModelBase):
    model_id: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
