from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    BadTimeSignature,
    SignatureExpired,
)
from config import settings

serializer = URLSafeTimedSerializer(settings.TOKEN_SECRET_KEY)


def create_email_verification_token(email: str):
   return serializer.dumps(email, salt="email-verify")


def verify_email_token(token: str, max_age=3600):
    try:
        return serializer.loads(
            token,
            salt="email-verify",
            max_age=max_age,
        )
    except (BadSignature, BadTimeSignature, SignatureExpired):
        return None


def create_password_reset_token(email: str):
    return serializer.dumps(email, salt="password-reset")



def verify_password_reset_token(token: str, max_age=3600):
    try:
        return serializer.loads(
            token,
            salt="password-reset",
            max_age=max_age,
        )
    except (BadSignature, BadTimeSignature, SignatureExpired):
        return None