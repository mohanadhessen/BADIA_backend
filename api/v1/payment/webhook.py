import logging
from datetime import date, timedelta
from decimal import Decimal
import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Request , HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session
from config import settings
from crud.payment import get_payment_by_hash, mark_payment_as_failed, mark_payment_as_paid
from crud.dashboard_metrics import refresh_payment_metrics
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
        try:
            payload = HesabeWebhook.model_validate_json(await request.body())
        except ValidationError:
            db.rollback()
            log.warning("Ignoring malformed Hesabe webhook")
            return {"ok": True}

        RETRYABLE_STATUS_CODES = {429, 502, 503, 504}
    
        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(3):
                try:
                    response = await client.get(
                        f"{settings.HESABE_BASE_URL}/api/transaction/{payload.token}",
                        headers={"accessCode": settings.HESABE_ACCESS_CODE, "Accept": "application/json"},
                    )
                except (httpx.TimeoutException, httpx.NetworkError):
                    continue
                if response.status_code in RETRYABLE_STATUS_CODES:
                    continue
                if not response.is_success:
                    raise HTTPException(status_code=502, detail=f"Hesabe returned {response.status_code}")
                break
            else:
                raise HTTPException(status_code=503, detail="Hesabe enquiry unavailable after retries")
    
        enquiry = response.json()["data"]


        payment = get_payment_by_hash(db, enquiry["reference_number"])
        if payment is None:
            raise ValueError("Payment not found")

        if enquiry.get("reference_number") != payment.payment_hash:
            raise HTTPException(status_code=400, detail="Hesabe payment reference does not match")
        if enquiry.get("token") != payment.gateway_token:
            raise HTTPException(status_code=400, detail="Hesabe transaction token does not match")
        if Decimal(str(enquiry.get("amount"))) != payment.amount:
            raise HTTPException(status_code=400, detail="Hesabe transaction amount does not match")

        if payment.status == "paid":
            log.info("Ignoring duplicate successful webhook for payment %s", payment.payment_hash)
            return {"ok": True}

        if enquiry["status"] != "SUCCESSFUL":
            if enquiry["status"] in {"FAILED", "DECLINED"}:
                mark_payment_as_failed(db, payment.gateway_token)  # type: ignore
            else:
                log.info("Hesabe payment %s is not final: %s", payment.payment_hash, enquiry["status"])
            return {"ok": True}


        carry = 0

        user = db.get(User, payment.user_id)
        if user.current_subscription_id :  # type: ignore
            current_subscription = db.get(Subscription, user.current_subscription_id)  # type: ignore
            current_subscription.status = "canceled"  # type: ignore
            if current_subscription.plan_id == payment.plan_id:# type: ignore
                carry = max(0, (current_subscription.end_date - date.today()).days)  # type: ignore




        end_date = date.today() + timedelta(
            days=365 + carry if payment.billing_cycle == "yearly" else 30 + carry  # type: ignore
        )


        subscription = create_subscription(
            db=db,
            user_id=payment.user_id,  # type: ignore
            plan_id=payment.plan_id,  # type: ignore
            payment_id=payment.id,  # type: ignore
            end_date=end_date,
            commit=False,
        )
        plan = db.get(Plan, subscription.plan_id)

        amount = plan.price_yearly if payment.billing_cycle == "yearly" else plan.price_monthly  # type: ignore

        mark_payment_as_paid(db, payment.gateway_token, commit=False)  # type: ignore
        db.flush()
        refresh_payment_metrics(db)

        background_tasks.add_task(
            send_plan_update_email,
            user.email,  # type: ignore
            user.first_name,  # type: ignore
            plan.name,  # type: ignore
            amount,
            payment.billing_cycle,  # type: ignore
            payment.gateway_token,  # type: ignore
        )


        return {"ok": True}
    except Exception:
        db.rollback()
        raise
