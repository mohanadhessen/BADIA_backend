from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.user import LoginRequest
from crud.user import get_user_by_email 
from security import  create_access_token , verify_password , create_refresh_token , verify_refresh_token
from schemas.auth import TokenRefreshRequest, TokenResponse


router = APIRouter()
router = APIRouter(tags=["Auth"])


@router.post("/auth/login",response_model=TokenResponse)
def login(user_in: LoginRequest, db: Session = Depends(get_db),remember_me: bool = True):
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
    refresh_token = create_refresh_token(token_payload, remember_me)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "refresh_token":refresh_token
    }



@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(payload: TokenRefreshRequest):

    decoded_data = verify_refresh_token(payload.refresh_token)
    user_id = decoded_data.get("sub")
    
    new_payload = {
        "sub": str(user_id),
        "email": decoded_data.get("email"),
        "role": decoded_data.get("role", "user")
    }
    new_access_token = create_access_token(data=new_payload)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }