import json
from decimal import Decimal
import logging
import httpx
import sentry_sdk
from api.v1.payment.HesabeCrypt import HesabeCrypt
from fastapi import APIRouter, Depends, HTTPException
from database.session import get_db
from api.dependencies import get_current_user
from models.user import User
from schemas.payment import PaymentCheckoutRequest, PaymentCheckoutResponse
from crud.payment import create_payment_gateaway
from crud.dashboard_metrics import refresh_payment_metrics
from config import settings  # type: ignore[reportGeneralTypeIssues]  # pyright: ignore[reportGeneralTypeIssues]
from models.payment import Payment
from sqlalchemy.orm import Session




PAYMENT_PAGE_URL = "https://sandbox.hesabe.com/payment"
log = logging.getLogger(__name__)


def _fail_checkout_without_gateway_token(db: Session, payment: Payment | None) -> None:
    if payment is None:
        db.rollback()
        return

    payment_id = payment.id
    try:
        db.rollback()
        saved_payment = db.get(Payment, payment_id)
        if saved_payment and saved_payment.status == "pending" and not saved_payment.gateway_token:
            saved_payment.status = "failed"
            db.commit()
            refresh_payment_metrics(db)
    except Exception as exc:
        db.rollback()
        log.exception("Could not mark checkout payment %s as failed", payment_id)
        sentry_sdk.capture_exception(exc)



def create_checkout(merchant_code: str, amount: Decimal, access_code: str, secret_key: str,iv: str,paymentType: int, customer_email: str, orderReferenceNumber: str,retry_attempts: int = 3) -> dict:
    RETRYABLE_STATUS_CODES = {429, 502, 503, 504}

    payload = {
        "merchantCode": merchant_code,
        "amount": str(amount),
        "currency": "KWD",
        "responseUrl": "https://api.badiaprojectmanagement.com/api/v1/payment/success",
        "failureUrl": "https://api.badiaprojectmanagement.com/api/v1/payment/failure",
        "version": "2.0",
        "orderReferenceNumber": orderReferenceNumber,
        "paymentType": paymentType,
        "webhookUrl": settings.HESABE_WEBHOOKURL,
        "email": customer_email,
    }


    encrypted = HesabeCrypt.encrypt(json.dumps(payload),secret_key,iv,)

    for _ in range(retry_attempts):
        try:
            response = httpx.post(settings.HESABE_CHECKOUT_URL,data={"data": encrypted},headers={"accessCode": access_code, "Accept": "application/json"}, timeout=30, )
        except (httpx.TimeoutException, httpx.NetworkError):
            continue
        if response.status_code in RETRYABLE_STATUS_CODES:
            continue
        if not response.is_success:
            raise HTTPException(status_code=502, detail=f"Hesabe returned {response.status_code}")
        decrypted_text = HesabeCrypt.decrypt(response.text.strip(), secret_key, iv)
        return json.loads(decrypted_text)
    raise HTTPException(status_code=503, detail="Hesabe checkout unavailable after retries")




router = APIRouter(tags=["Payment"])
@router.post("/checkout", response_model=PaymentCheckoutResponse,summary="Create a payment checkout", description=( "Creates a pending payment for the authenticated user and returns ""the payment gateway URL."),
    response_description="The URL to redirect the customer to",
)
def checkout(
    data: PaymentCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = None
    try:
        payment = create_payment_gateaway(  db=db,  data=data, billing_cycle=data.billing_cycle, user_id=current_user.id,)   # type: ignore

        result = create_checkout(
            merchant_code=settings.HESABE_MERCHANT_CODE,
            amount=payment.amount,  # type: ignore
            access_code=settings.HESABE_ACCESS_CODE,
            secret_key=settings.HESABE_SECRET_KEY,
            iv=settings.HESABE_IV,
            paymentType=data.payment_type,
            customer_email=current_user.email,  # type: ignore
            orderReferenceNumber=payment.payment_hash,  # type: ignore
        )

        if ( result.get("status") is not True):
            payment.status = "failed"  # type: ignore
            db.commit()
            raise HTTPException( status_code=502,detail=f"Hesabe authentication failed: {result.get('message', 'Unknown error')}",)

        session_token = result["response"]["data"]
        payment.gateway_token = result["token"]  # type: ignore
        db.commit()

        payment_url = f"{PAYMENT_PAGE_URL}?data={session_token}"
        return {"payment_url": payment_url}
    
    except HTTPException:
        _fail_checkout_without_gateway_token(db, payment)
        raise
    
    except Exception as exc:
        _fail_checkout_without_gateway_token(db, payment)
        sentry_sdk.capture_exception(exc)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the payment checkout.",
        ) from exc

