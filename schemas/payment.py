from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal


BillingCycle = Literal["monthly", "yearly"]



class PaymentStatus(BaseModel):
    status: str


class PaymentBase(BaseModel):
    user_id: int
    plan_id: int
    amount: Decimal = Field(..., gt=0)
    billing_cycle: BillingCycle
    status: PaymentStatus
    start_date: datetime
    end_date: datetime



class PaymentUpdate(BaseModel):
    plan_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    billing_cycle: Optional[BillingCycle] = None
    status: PaymentStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PaymentUserSchema(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentPlanSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class AdminPaymentResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    amount: Decimal
    billing_cycle: BillingCycle
    status: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime
    user: Optional[PaymentUserSchema] = None
    plan: Optional[PaymentPlanSchema] = None

    class Config:
        from_attributes = True


