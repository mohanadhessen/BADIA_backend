from pydantic import BaseModel , EmailStr
from typing import Optional
from datetime import datetime
from typing import Optional, Literal
class StatusUpdate(BaseModel):
    status: str


class ReviewPublishUpdate(BaseModel):
    is_published: bool



class AdminUserUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: Optional[Literal["local", "google"]] = None
    is_email_verified: Optional[bool] = None
    current_plan_id: Optional[int] = None
    subscription_end_date: Optional[datetime] = None
    role: Optional[Literal["user", "admin"]] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True