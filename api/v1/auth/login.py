from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.user import LoginRequest
from crud.user import get_user_by_email , get_user_by_id
from security import  create_access_token , verify_password , create_refresh_token , verify_refresh_token , set_auth_cookies , clear_auth_cookies
from api.rate_limiter import limiter
from models.revoked_token import RevokedToken
from api.dependencies import get_current_user
from models.user import User


router = APIRouter(tags=["Auth"])


@router.post("/auth/login")
@limiter.limit("5/minute")
def login(request: Request, response: Response, user_in: LoginRequest, db: Session = Depends(get_db)):
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

    set_auth_cookies(response, access_token, refresh_token)

    return {
        "status": "success",
        "user": {
            "id": existing_user.id,
            "email": existing_user.email,
            "role": existing_user.role,
            "first_name": existing_user.first_name,
            "last_name": existing_user.last_name,
        }
    }



@router.post("/refresh")
@limiter.limit("10/minute")
def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    is_revoked = db.query(RevokedToken).filter(RevokedToken.token == refresh_token).first()
    if is_revoked:
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
        "email": decoded_data.get("email"),
        "role": decoded_data.get("role", "user")
    }
    new_access_token = create_access_token(data=new_payload)
    
    set_auth_cookies(response, new_access_token)

    return {"status": "success"}


@router.post("/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        is_revoked = db.query(RevokedToken).filter(RevokedToken.token == refresh_token).first()
        if not is_revoked:
            revoked = RevokedToken(token=refresh_token)
            db.add(revoked)
            db.commit()

    clear_auth_cookies(response)
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/auth/check")
def auth_check(current_user: User = Depends(get_current_user)):
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
        }
    }


@router.post("/auth/revoke")
def revoke_token(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token")

    is_revoked = db.query(RevokedToken).filter(RevokedToken.token == refresh_token).first()
    if is_revoked:
        return {"msg": "Token already revoked"}
        
    revoked = RevokedToken(token=refresh_token)
    db.add(revoked)
    db.commit()
    return {"msg": "Token revoked successfully"}

@router.delete("/auth/flush-revoked")
def flush_revoked_tokens(db: Session = Depends(get_db)):
    db.query(RevokedToken).delete()
    db.commit()
    return {"msg": "Flushed revoked tokens successfully"}