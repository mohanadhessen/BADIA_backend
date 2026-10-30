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
from crud.payment import create_payment
from config import settings 
from models.payment import Payment
from sqlalchemy.ext.asyncio import AsyncSession




PAYMENT_PAGE_URL = settings.HESABE_BASE_URL + "/payment"


 



async def create_checkout(merchant_code: str, amount: Decimal, access_code: str, secret_key: str,iv: str,paymentType: int, customer_email: str, orderReferenceNumber: str,retry_attempts: int = 3) -> dict:
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
            response = httpx.post(settings.HESABE_BASE_URL + "/checkout",data={"data": encrypted},headers={"accessCode": access_code, "Accept": "application/json"}, timeout=30, )
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
async def checkout(data: PaymentCheckoutRequest,db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user)):
    payment = None
    try:
        payment = await create_payment( db,  data, data.billing_cycle, current_user.id)           
        result = await create_checkout(
            merchant_code=settings.HESABE_MERCHANT_CODE,
            amount=payment.amount,  
            access_code=settings.HESABE_ACCESS_CODE,
            secret_key=settings.HESABE_SECRET_KEY,
            iv=settings.HESABE_IV,
            paymentType=data.payment_type,
            customer_email=current_user.email,  
            orderReferenceNumber=payment.payment_hash, 
        )

        if ( result.get("status") is not True):
            payment.status = "failed" 
            await db.commit()
            raise HTTPException( status_code=502,detail=f"Hesabe authentication failed: {result.get('message', 'Unknown error')}",)

        session_token = result["response"]["data"]
        payment.gateway_token = result["token"] 
        await db.commit()

        payment_url = f"{PAYMENT_PAGE_URL}?data={session_token}"
        return {"payment_url": payment_url}
    
    except HTTPException:

        raise
    
    except Exception as exc:
        logging.exception("Unexpected error creating payment checkout")
        sentry_sdk.capture_exception(exc)
        raise HTTPException(status_code=500,detail="An unexpected error occurred while creating the payment checkout.") from exc

