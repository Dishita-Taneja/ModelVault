import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "Data Scientist"
    department: str = "ML Engineering"


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
