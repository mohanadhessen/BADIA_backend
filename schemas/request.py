from pydantic import BaseModel, Field
from typing import List, Optional 
from decimal import Decimal
from enum import Enum
from datetime import datetime

class FeasibilityRequest(BaseModel):
    project_description: str = Field(..., min_length=5)
    estimated_cost: Decimal
    funding_source: str


class OperationalPartnership(BaseModel):
    pdf_files: List[str] = Field(
        ...,
        min_length=1,
        max_length=8,
        description="List of uploaded PDF file paths or URLs"
    )


class RequestFileResponse(BaseModel):
    id: int
    file_id: str
    filename: str
    file_key: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RequestUserSchema(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class AdminRequestResponse(BaseModel):
    id: int
    request_id: str
    user_id: int
    service_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    files: List[RequestFileResponse] = []
    user: Optional[RequestUserSchema] = None

    class Config:
        from_attributes = True

    


