import json
from decimal import Decimal
import httpx
from api.v1.payment.HesabeCrypt import HesabeCrypt


from sqlalchemy.orm import Session





from config import settings


PAYMENT_PAGE_URL = "https://sandbox.hesabe.com/payment"




import json
from typing import Any
import httpx


def create_checkout(
    merchant_code: str,
    amount: Decimal,
    access_code: str,
    secret_key: str,
    iv: str,
    paymentType: int,
    customer_email: str,
    orderReferenceNumber: str,
) -> str:

    

    payload = {
        "merchantCode": merchant_code,
        "amount": str(amount),
        "currency": "KWD",
        "responseUrl": "http://127.0.0.1:8765/api/v1/payment/success",
        "failureUrl": "http://127.0.0.1:8765/api/v1/payment/failure",
        "version": "2.0",
        "orderReferenceNumber": orderReferenceNumber,
        "paymentType": paymentType,
        "webhookUrl": "https://investigations-grades-detective-ranges.trycloudflare.com/api/v1/webhook/hesabe",
        "email": customer_email,
    }

    encrypted = HesabeCrypt.encrypt(
        json.dumps(payload),
        secret_key,
        iv,
    )

    response = httpx.post(
        "https://sandbox.hesabe.com/checkout",
        data={"data": encrypted},
        headers={
            "accessCode": access_code,
            "Accept": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()

    encrypted_response = response.text.strip()

    decrypted_text = HesabeCrypt.decrypt(
        encrypted_response,
        secret_key,
        iv,
    )

    result = json.loads(decrypted_text)
    return result







from fastapi import APIRouter, Depends, HTTPException
from database.session import get_db
from api.dependencies import get_current_user
from models.user import User
from schemas.payment import PaymentCheckoutRequest, PaymentCheckoutResponse
from crud.payment import create_payment_gateaway
from config import settings

router = APIRouter(tags=["Payment"])


@router.post(
    "/checkout",
    response_model=PaymentCheckoutResponse,
    summary="Create a payment checkout",
    description=(
        "Creates a pending payment for the authenticated user and returns "
        "the payment gateway URL."
    ),
    response_description="The URL to redirect the customer to",
)
def checkout(
    data: PaymentCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = create_payment_gateaway(
        db=db,
        data=data,
        billing_cycle=data.billing_cycle,
        user_id=current_user.id, # type: ignore
    )

    

    result = create_checkout(
        merchant_code=settings.HESABE_MERCHANT_CODE,
        amount=payment.amount, # type: ignore
        access_code=settings.HESABE_ACCESS_CODE,
        secret_key=settings.HESABE_SECRET_KEY,
        iv=settings.HESABE_IV,
        paymentType=data.payment_type,
        customer_email=current_user.email, # type: ignore
        orderReferenceNumber=payment.payment_hash, # type: ignore
    )
    
    payment.gateway_token = result["token"] # type: ignore
    db.commit()



    if result["status"] != True or result["message"] != "Authentication success!": # type: ignore
        payment.status = "failed" # type: ignore
        db.commit()
    session_token = result["response"]["data"] # type: ignore

    payment_url = f"{PAYMENT_PAGE_URL}?data={(session_token)}"
    return {"payment_url": payment_url}



# todo add the telemty and retire logic