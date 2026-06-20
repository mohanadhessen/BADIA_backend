from pydantic import BaseModel, EmailStr, field_validator

from datetime import datetime
from typing import Optional
import re

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    company_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not re.fullmatch(r"\+?[0-9\s\-]{7,20}", v):
            raise ValueError("Invalid phone number")
        return v  

class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfileResponse(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]

    company_name: str
    email: str
    phone: Optional[str]
    avatar_url: Optional[str]

    role: str
    auth_provider: str
    is_email_verified: bool
    is_active: bool

    current_plan_id: int | None = None
    subscription_end_date: datetime | None = None
    created_at: Optional[datetime]


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPasswordReset(BaseModel):
    current_password: str
    new_password: str


class AdminUserSearchResponse(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: str
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    auth_provider: str
    is_email_verified: bool
    is_active: bool
    current_plan_id: Optional[int] = None
    subscription_end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
