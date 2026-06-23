from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Password must be 8–72 characters (bcrypt limit).",
    )


class UserRead(UserBase):
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
