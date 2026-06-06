from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PlanBase(BaseModel):
    name: str
    price_monthly: float
    price_yearly: float
    plan_details: Optional[List[Dict[str, Any]]] = None


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    plan_details: Optional[List[Dict[str, Any]]] = None


class PlanResponse(PlanBase):
    id: int

    class Config:
        from_attributes = True