from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from decimal import Decimal

class PlanBase(BaseModel):
    name: str
    price_monthly: Decimal
    price_yearly: Decimal
    plan_details: Optional[Any] = None

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    plan_details: Optional[Any] = None

class PlanResponse(PlanBase):
    id: int
    model_config = ConfigDict(from_attributes=True)