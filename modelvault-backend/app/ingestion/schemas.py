import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class IAMLogItem(BaseModel):
    event_id: str
    timestamp: str
    user_arn: str
    action: str
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "SUCCESS"


class EC2LogItem(BaseModel):
    event_id: str
    timestamp: str
    instance_id: str
    source_ip: Optional[str] = None
    action: str
    bytes_transferred: int = 0
    status: str = "SUCCESS"


class S3LogItem(BaseModel):
    event_id: str
    timestamp: str
    bucket: str
    key: str
    requester_arn: str
    source_ip: Optional[str] = None
    bytes_sent: int = 0
    http_status: int = 200


class ModelAccessLogItem(BaseModel):
    event_id: str
    timestamp: str
    model_id: str
    requester_arn: str
    input_tokens: Optional[int] = 0
    execution_time_ms: Optional[int] = 0
    status: str = "SUCCESS"


class UserItem(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    role: str = "Analyst"
    is_active: bool = True
    created_at: str


class ModelItem(BaseModel):
    model_id: str
    name: str
    description: Optional[str] = None
    framework: str = "PyTorch"
    s3_uri: str
    sensitivity_level: str = "HIGH"
    owner_email: Optional[str] = None
    created_at: str
