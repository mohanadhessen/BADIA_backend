import logging
from decimal import Decimal
import json
import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from config import settings


log = logging.getLogger(__name__)
router = APIRouter(tags=["Payment"])


class HesabeWebhook(BaseModel):
    model_config = ConfigDict(extra="ignore")
    reference_number: str
    status: str
    amount: Decimal
    token: str | None = None
    payment_type: str | None = None
    gateway_datetime: str | None = Field( default=None, alias="datetime",)


@router.post("/hesabe")
async def hesabe_hook(request: Request):
    try:
        payload = HesabeWebhook.model_validate_json( await request.body())
        if not payload.token:
            log.warning("Hesabe webhook missing transaction token: %s", payload.reference_number,)
            return {"ok": True}

        url = (f"https://sandbox.hesabe.com/api/transaction/" f"{payload.token}")

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={"accessCode": settings.HESABE_ACCESS_CODE,"Accept": "application/json", },)


        enquiry = response.json()["data"]
        print("Enquiry:", enquiry)
        
        print("MATCH:", payload.token == enquiry["token"] and payload.reference_number == enquiry["reference_number"] and payload.amount == Decimal(enquiry["amount"]) and payload.status == enquiry["status"] and payload.payment_type == enquiry["payment_type"])


        return {"ok": True}

    except ValidationError:
        log.warning("Ignoring malformed Hesabe webhook")
        return {"ok": True}