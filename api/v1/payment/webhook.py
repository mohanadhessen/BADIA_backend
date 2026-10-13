import logging
from datetime import date, timedelta
from decimal import Decimal
import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Request , HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from config import settings
from crud.payment import get_payment_by_hash, mark_payment_as_paid
from crud.subscriptions import create_subscription
from database.session import get_db
from email_service import send_plan_update_email
from models.user import User  
from models.plan import Plan
from models.subscription import Subscription  


log = logging.getLogger(__name__)
router = APIRouter(tags=["Payment"])


class HesabeWebhook(BaseModel):
    model_config = ConfigDict(extra="ignore")
    reference_number: str
    status: str
    amount: Decimal
    token: str | None = None
    payment_type: str | None = None
    gateway_datetime: str | None = Field(default=None, alias="datetime")


@router.post("/hesabe")
async def hesabe_hook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        payload = HesabeWebhook.model_validate_json(await request.body())
    except ValidationError:
        log.warning("Ignoring malformed Hesabe webhook")
        return {"ok": True}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://sandbox.hesabe.com/api/transaction/{payload.token}",
            headers={"accessCode": settings.HESABE_ACCESS_CODE, "Accept": "application/json"},
        )
    enquiry = response.json()["data"]


# Enquiry response:
# {
#     'token': '84221717917899209868458887603',
#     'amount': '917.000',
#     'reference_number': '49325186147940cb8d7405a36e03a4c4',
#     'status': 'SUCCESSFUL',
#     'TransactionID': '628510004414039',
#     'Id': 194218,
#     'PaymentID': '100628510000004202',
#     'Terminal': '570401',
#     'TrackID': '377135',
#     'payment_type': 'KNET',
#     'service_type': 'Payment Gateway',
#     'customerName': None,
#     'customerEmail': 'mohanadhessen@gmail.com',
#     'customerMobile': None,
#     'customerCardType': '-NA-',
#     'customerCard': '-NA-',
#     'datetime': '2026-10-12 10:25:21',
# }
    
    
  
        




    payment = get_payment_by_hash(db, enquiry["reference_number"])
    if payment is None:
        raise ValueError("Payment not found")

    if enquiry["status"] != "SUCCESSFUL":
      payment.status = "failed"
      db.commit()
      raise HTTPException(
        status_code=400,
        detail=f"Payment failed: {enquiry['status']}",
    )
        
    

    user = db.get(User, payment.user_id)
    if user.current_subscription_id:
        carry = 0
        current_subscription = db.get(Subscription , user.current_subscription_id)
        carry = max(0,(current_subscription.end_date - date.today()).days)
        current_subscription.status = "canceled"



    
    mark_payment_as_paid(db, payment.id, payment.gateway_token or "")
    end_date = date.today() + timedelta(
        days=365 + carry if payment.billing_cycle == "yearly" else 30 + carry
    )
    subscription = create_subscription(
        db=db,
        user_id=payment.user_id,
        plan_id=payment.plan_id,
        payment_id=payment.id,
        end_date=end_date,
    )
    plan = db.get(Plan, subscription.plan_id)

    amount = plan.price_yearly if payment.billing_cycle == "yearly" else plan.price_monthly

    background_tasks.add_task(
    send_plan_update_email,
    user.email,
    user.first_name,
    plan.name,
    amount,
    payment.billing_cycle,
    payment.gateway_token,
)
   
    return {"ok": True}
