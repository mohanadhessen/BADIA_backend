from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal


BillingCycle = Literal["monthly", "yearly"]


class PaymentBase(BaseModel):
    user_id: int
    plan_id: int
    amount: Decimal = Field(..., gt=0)
    billing_cycle: BillingCycle
    start_date: datetime
    end_date: datetime



class PaymentUpdate(BaseModel):
    user_id: Optional[int] = None
    plan_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    billing_cycle: Optional[BillingCycle] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


