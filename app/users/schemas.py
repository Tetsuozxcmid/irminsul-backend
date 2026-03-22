from pydantic import BaseModel, EmailStr
from typing import Optional
from app.auth.models import UserRole


class UserProfileOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr]
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    verified: bool
    is_active: bool
    balance: int

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
