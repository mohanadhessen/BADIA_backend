from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.user import UserRegister
from crud.user import get_user_by_email , create_new_user
from security import hash_password , create_access_token , create_refresh_token , set_auth_cookies
from api.rate_limiter import limiter
from email_tokens import create_email_verification_token
from email_service import send_verification_email



router = APIRouter(tags=["Auth"])

@router.post("/auth/register_local", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register_company(request: Request, response: Response, user_in: UserRegister, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered to a company.",
        )

    try:
        new_user = create_new_user(
            db=db,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            company_name=user_in.company_name,
            email=user_in.email,
            password=hash_password(user_in.password),
            phone=user_in.phone,
        )

        try:
            token = create_email_verification_token(new_user.email)
            send_verification_email(new_user.email, token)
        except Exception as e:
            # We don't want to crash registration if email fails
            print(f"Warning: Could not send verification email to {new_user.email}: {e}")

        token_payload = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role
        }

        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data=token_payload)

        set_auth_cookies(response, access_token, refresh_token)

        return {
            "status": "success",
            "message": "Company account created",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "role": new_user.role,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "company_name": new_user.company_name,
            }
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during registration",
        )