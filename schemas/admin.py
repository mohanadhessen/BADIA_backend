from pydantic import BaseModel , EmailStr 
from typing import Optional
from typing import Optional 
from enum import Enum
from pydantic import BaseModel


class RequestStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class StatusUpdate(BaseModel):
    status: RequestStatus

class ReviewPublishUpdate(BaseModel):
    is_published: bool

class AdminUserUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None
    is_email_verified: Optional[bool] = None
    current_plan_id: Optional[int] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


