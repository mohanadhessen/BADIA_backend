from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal


BillingCycle = Literal["monthly", "yearly"]
PaymentStatus = Literal["pending", "paid", "failed", "canceled"]
PaymentSource = Literal["manual", "paymentgateway"]


class PaymentCheckoutRequest(BaseModel):
    plan_id: int = Field(..., gt=0, description="ID of the plan to purchase")
    billing_cycle: BillingCycle = Field(
        ..., description="Billing period for the selected plan"
    )
    payment_type: Literal[1, 16] = Field(
        1, alias="paymentType", description="Hesabe payment method type"
    )

    model_config = ConfigDict(populate_by_name=True)


class PaymentCheckoutResponse(BaseModel):
    payment_url: str = Field(..., description="URL to redirect the customer to")


class PaymentBase(BaseModel):
    user_id: int
    plan_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    billing_cycle: BillingCycle
    status: PaymentStatus = "pending"
class PaymentUpdate(BaseModel):
    plan_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    billing_cycle: Optional[BillingCycle] = None
    status: Optional[PaymentStatus] = None


class PaymentUserSchema(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentPlanSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentResponse(BaseModel):
    id: int
    payment_hash: str
    user_id: int
    plan_id: Optional[int] = None
    amount: Decimal
    billing_cycle: BillingCycle
    status: PaymentStatus
    source: PaymentSource
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[PaymentUserSchema] = None
    plan: Optional[PaymentPlanSchema] = None

    model_config = ConfigDict(from_attributes=True)
