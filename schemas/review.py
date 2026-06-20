from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    stars: int = Field(..., ge=1, le=5)
    review_text: str


class ReviewUpdate(BaseModel):
    stars: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None
    is_published: Optional[bool] = None


class ReviewResponse(BaseModel):
    id: int
    stars: int
    review_text: str
    user_id: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class ReviewUserSchema(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        from_attributes = True


class AdminReviewResponse(BaseModel):
    id: int
    stars: int
    review_text: str
    user_id: int
    is_published: bool
    created_at: datetime
    updated_at: datetime
    user: Optional[ReviewUserSchema] = None

    class Config:
        from_attributes = True