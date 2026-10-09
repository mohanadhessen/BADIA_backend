import json
import secrets
from typing import Any 
from decimal import Decimal
from urllib.parse import urlencode
from datetime import date
import httpx
from api.v1.payment.HesabeCrypt import HesabeCrypt
import uuid


from config import settings


PAYMENT_PAGE_URL = "https://sandbox.hesabe.com/payment"
orderReferenceNumber = str(uuid.uuid4())

print("Order Reference Number:", orderReferenceNumber)


def create_checkout(merchant_code: str ,amount:Decimal ,access_code: str,secret_key: str,iv: str ,paymentType: int) -> Any:



# the payload the data are defined in the Hesabe API documentation the only varibale are the orderReferenceNumber and the amount  that you can set yourself the rest of the data are fixed and you can use them as they are in the documentation
    payload = {
        "merchantCode": merchant_code,
        "amount": str(amount),
        "currency": "KWD",
        "responseUrl": "http://127.0.0.1:8765/api/v1/payment/success",
        "failureUrl": "http://127.0.0.1:8765/api/v1/payment/failure",
        "version": "2.0",
        "orderReferenceNumber": orderReferenceNumber,
        "paymentType": paymentType,
        "webhookUrl": "https://bullet-license-foot-hart.trycloudflare.com/api/v1/webhook/hesabe",
               

    
        
    }
# the endpoint requires the payload to be encrypted using the HesabeCrypt before sending it
    encrypted = HesabeCrypt.encrypt(json.dumps(payload),secret_key,iv, )
    response = httpx.post("https://sandbox.hesabe.com/checkout", data={"data": encrypted},
        headers={
            "accessCode": access_code,
            "Accept": "application/json",
        },
        timeout=30,
    )
    encrypted_response = response.text.strip()
    
# decrypted_the response message using the same secret key and iv
    
    decrypted_text = HesabeCrypt.decrypt(encrypted_response,secret_key, iv, )
    
    print("Decrypted response:", decrypted_text)
    
    decrypted = json.loads(decrypted_text)
    
    return decrypted



#  get the session token to redirect the user to the payment page

result = create_checkout(
    merchant_code=settings.HESABE_MERCHANT_CODE,
    amount=Decimal("5.0"),
    access_code=settings.HESABE_ACCESS_CODE,
    secret_key=settings.HESABE_SECRET_KEY,
    iv=settings.HESABE_IV,
    paymentType=1
)

print("Result:", result)


session_token = result["response"]["data"]


payment_url = f"https://sandbox.hesabe.com/payment?data={session_token}"

print(payment_url)





