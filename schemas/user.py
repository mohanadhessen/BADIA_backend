from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    first_name: str
    last_name: str
    company_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


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
