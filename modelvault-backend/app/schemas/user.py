import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "Analyst"
    is_active: bool = True


class UserCreate(UserBase):
    user_id: str | None = None


class UserResponse(UserBase):
    user_id: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
