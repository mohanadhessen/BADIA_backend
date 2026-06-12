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


