from pydantic import BaseModel
from typing import Optional, Dict, Any


class PlanBase(BaseModel):
    name: str

    price_monthly: float
    price_yearly: float

    max_transactions: Optional[int] = None
    max_users: Optional[int] = None

    has_inventory: bool = False
    has_payroll: bool = False

    plan_details: Optional[Dict[str, Any]] = None


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None

    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None

    max_transactions: Optional[int] = None
    max_users: Optional[int] = None

    has_inventory: Optional[bool] = None
    has_payroll: Optional[bool] = None

    plan_details: Optional[Dict[str, Any]] = None


class PlanResponse(PlanBase):
    id: int

    class Config:
        from_attributes = True