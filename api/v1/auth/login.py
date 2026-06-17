from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.user import LoginRequest
from crud.user import get_user_by_email , get_user_by_id
from security import  create_access_token , verify_password , create_refresh_token , verify_refresh_token
from schemas.auth import TokenRefreshRequest, TokenResponse
from api.rate_limiter import limiter
from models.user import User
from api.dependencies import get_current_user

from crud.revoked_token import (
    get_revoked_token,
    create_revoked_token,
    is_token_revoked
)


router = APIRouter(tags=["Auth"])


@router.post("/auth/login",response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, user_in: LoginRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user_in.email)
    if not existing_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not existing_user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="This account uses Google sign-in. Please continue with Google."
        )
    
    if not verify_password(user_in.password, existing_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not existing_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    token_payload = {
        "sub": str(existing_user.id),
        "email": existing_user.email,
        "role": existing_user.role
    }

    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(token_payload)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "refresh_token":refresh_token
    }



@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
def refresh_access_token(request: Request, payload: TokenRefreshRequest, db: Session = Depends(get_db)):

    if is_token_revoked(db, payload.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")


    decoded_data = verify_refresh_token(payload.refresh_token)
    old_refresh_token = payload.refresh_token
    user_id = decoded_data.get("sub")

    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user account")

    new_payload = {
        "sub": str(user_id),
        "email": decoded_data.get("email"),
        "role": decoded_data.get("role", "user")
    }
    create_revoked_token(db, old_refresh_token)
    new_access_token = create_access_token(data=new_payload)
    new_refresh_token = create_refresh_token(data=new_payload)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }




@router.post("/auth/revoke")
@limiter.limit("10/minute")
def revoke_token(
    request: Request,
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    decoded_data = verify_refresh_token(payload.refresh_token)
    user_id = decoded_data.get("sub")

    if str(user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot revoke this token"
        )

    if is_token_revoked(db, payload.refresh_token):
        return {"msg": "Token already revoked"}

    create_revoked_token(db, payload.refresh_token)

    return {"msg": "Token revoked successfully"}
