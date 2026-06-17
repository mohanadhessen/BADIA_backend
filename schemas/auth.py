from pydantic import BaseModel, EmailStr
from typing import Optional



class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"



# --- Request Schemas ---
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class VerificationRequest(BaseModel):
    email: EmailStr


class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    message: str