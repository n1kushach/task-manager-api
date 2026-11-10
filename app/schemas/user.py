from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=120)


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    hashed_password: str
