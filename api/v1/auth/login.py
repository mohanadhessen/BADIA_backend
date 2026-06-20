from fastapi import APIRouter, Depends, HTTPException, status, Request , Response , Cookie
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.user import LoginRequest
from crud.user import get_user_by_email , get_user_by_id 
from security import (
    create_access_token,
    verify_password,
    create_refresh_token,
    verify_refresh_token,
    set_auth_cookies,
    clear_auth_cookies,
)
from api.rate_limiter import limiter
from models.user import User
from api.dependencies import get_current_user
from config import settings
from crud.revoked_token import (
    get_revoked_token,
    create_revoked_token,
    is_token_revoked
)


router = APIRouter(tags=["Auth"])


@router.post("/auth/login", status_code=200)
@limiter.limit("5/minute")
def login(request: Request, user_in: LoginRequest, response: Response, db: Session = Depends(get_db)):
    # ... same validation logic as before ...
    existing_user = get_user_by_email(db, user_in.email)
    if not existing_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not existing_user.password_hash:
        raise HTTPException(status_code=400, detail="This account uses Google sign-in. Please continue with Google.")
    if not verify_password(user_in.password, existing_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not existing_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    token_payload = {
        "sub": str(existing_user.id),
    }
    access_token  = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    set_auth_cookies(response, access_token, refresh_token, role=existing_user.role)

    return {"status": "Login successful"}



@router.post("/refresh", status_code=200)
@limiter.limit("10/minute")
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    if is_token_revoked(db, refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    decoded_data = verify_refresh_token(refresh_token)
    user_id = decoded_data.get("sub")

    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user account")

    new_payload = {
        "sub": str(user_id),
    }
    create_revoked_token(db, refresh_token)          # revoke old refresh token
    new_access_token  = create_access_token(data=new_payload)
    new_refresh_token = create_refresh_token(data=new_payload)

    set_auth_cookies(response, new_access_token, new_refresh_token, role=user.role)

    return {"status": "ok"}




@router.post("/auth/logout", status_code=200)
@limiter.limit("20/minute")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
):
    if refresh_token and not is_token_revoked(db, refresh_token):
        try:
            verify_refresh_token(refresh_token)      
            create_revoked_token(db, refresh_token)
        except Exception:
            pass                                    

    clear_auth_cookies(response)
    return {"status": "ok"}
