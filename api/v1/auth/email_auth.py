from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from database.session import get_db
from crud.user import get_user_by_email
from email_tokens import (
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_email_verification_token
)
from email_service import send_password_reset_email , send_verification_email, send_contact_form_email
from security import hash_password
from schemas.auth import ForgotPasswordRequest , ResetPasswordRequest , VerificationRequest , VerifyEmailRequest, ContactFormRequest
from api.rate_limiter import limiter



router = APIRouter(tags=["email_services"])


@router.post("/auth/request-verification")
@limiter.limit("3/minute")
def request_verification(
    request: Request,
    payload: VerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, payload.email)
    
    # If the user doesn't exist, or they are already verified, do nothing quietly (security best practice)
    if not user or user.is_email_verified:
        return {"message": "If the account exists and is unverified, a link has been sent."}
        
    # Generate token using your existing token utility
    token = create_email_verification_token(user.email) 
    # Send the email
    background_tasks.add_task(send_verification_email, user.email, token) 
    
    return {"message": "If the account exists and is unverified, a link has been sent."}



@router.post("/auth/verify-email")
@limiter.limit("10/minute")
def verify_email(request: Request, payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    email = verify_email_token(payload.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is invalid or expired"
        )

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_email_verified:
        return {"message": "Already verified"}

    user.is_email_verified = True
    db.commit()

    return {"message": "Email verified successfully"}



@router.post("/auth/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, payload.email)

    
    if not user:
        return {"message": "If email exists, reset link was sent"}

    token = create_password_reset_token(payload.email)
    background_tasks.add_task(send_password_reset_email, payload.email, token)

    return {"message": "If email exists, reset link was sent"}



@router.post("/auth/reset-password")  
@limiter.limit("10/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)): 
    email = verify_password_reset_token(payload.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is invalid or expired"
        )

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/contact")
@limiter.limit("5/minute")
def send_contact_form(
    request: Request,
    payload: ContactFormRequest,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(
        send_contact_form_email,
        name=payload.name,
        visitor_email=payload.email,
        phone=payload.phone,
        message=payload.message
    )
    return {"message": "Contact message sent successfully"}