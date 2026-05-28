from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from itsdangerous import BadSignature, SignatureExpired

from database.session import get_db
from crud.user import get_user_by_email
from email_tokens import (
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_email_verification_token
)
from email_service import send_password_reset_email , send_verification_email
from security import hash_password
from schemas.auth import ForgotPasswordRequest , ResetPasswordRequest , VerificationRequest , VerifyEmailRequest



router = APIRouter(tags=["email_services"])


@router.post("/auth/request-verification")
def request_verification(request: VerificationRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, request.email)
    
    # If the user doesn't exist, or they are already verified, do nothing quietly (security best practice)
    if not user or user.is_email_verified:
        return {"message": "If the account exists and is unverified, a link has been sent."}
        
    # Generate token using your existing token utility
    token = create_email_verification_token(request.email) 
    # Send the email
    send_verification_email(request.email, token) 
    
    return {"message": "If the account exists and is unverified, a link has been sent."}



@router.post("/auth/verify-email")
def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        # Access token from the JSON body request object
        email = verify_email_token(request.token)
    except SignatureExpired:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    except BadSignature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_email_verified:
        return {"message": "Already verified"}

    user.is_email_verified = True
    db.commit()

    return {"message": "Email verified successfully"}



@router.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, request.email)

    
    if not user:
        return {"message": "If email exists, reset link was sent"}

    token = create_password_reset_token(request.email)
    send_password_reset_email(request.email, token)

    return {"message": "If email exists, reset link was sent"}



@router.post("/auth/reset-password")  
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)): 
    try:
        email = verify_password_reset_token(request.token)
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expired"
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.password = hash_password(request.new_password)
    db.commit()

    return {"message": "Password updated successfully"}