import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "Analyst"
    is_active: bool = True


class UserCreate(UserBase):
    user_id: Optional[str] = None


class UserResponse(UserBase):
    user_id: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
