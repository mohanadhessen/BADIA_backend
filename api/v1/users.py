from fastapi import APIRouter, Depends, HTTPException, status, Request , Response
from sqlalchemy.orm import Session
from schemas.user import UserUpdate, UserPasswordReset
from database.session import get_db 
from api.dependencies import get_current_user, require_admin
from models.user import User
from crud.user import update_user_data, delete_user, update_user_password, get_user_by_email, create_new_user
from security import verify_password, hash_password
from api.rate_limiter import limiter
from cache.user import get_user_version , bump_user_version , bump_global_users_version
from cache.etags import make_etag , check_etag
from pydantic import BaseModel, EmailStr
from typing import Optional
from crud.dashboard_metrics import refresh_user_metrics


router = APIRouter(tags=["Users"])






@router.get("/me")
@limiter.limit("60/minute")
def get_user_profile(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    minimal: bool = False
):

    if minimal:
        return {
            "status": "logged_in"
        }
    
    version = get_user_version(current_user.id)
    if version == 0:
        bump_user_version(current_user.id)
        version = 1
    
    etag_source = f"{version}_{current_user.role}_{current_user.is_email_verified}_{current_user.updated_at}"
    etag = make_etag(etag_source)
    if check_etag(request, response, etag):
        return []
    data = {
        "status": "success",
        "user_info": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "company_name": current_user.company_name,
            "phone": current_user.phone,
            "avatar_url": current_user.avatar_url,
            "auth_provider": current_user.auth_provider,
            "role": current_user.role,
            "created_at": current_user.created_at,
            "is_email_verified": current_user.is_email_verified
        }
    }
    
    return data


@router.patch("/me")
@limiter.limit("10/minute")
def update_user_profile(
    request: Request,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    update_dict = user_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
    
    bump_global_users_version()
    bump_user_version(current_user.id)


    updated_user = update_user_data(
        db=db, 
        email=current_user.email, 
        update_data=update_dict
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    refresh_user_metrics(db)
    return {
        "status": "success",
        "user_info": {
            "id": updated_user.id,
            "email": updated_user.email,
            "first_name": updated_user.first_name,
            "last_name": updated_user.last_name,
            "company_name": updated_user.company_name,
            "phone": updated_user.phone,
            "avatar_url": updated_user.avatar_url,
            "auth_provider": updated_user.auth_provider,
            "role": updated_user.role,
            "created_at": updated_user.created_at
        }
    }


@router.post("/me/password")
@limiter.limit("5/minute")
def reset_user_password(
    request: Request,
    password_data: UserPasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.password_hash or not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    new_hash = hash_password(password_data.new_password)
    success = update_user_password(db, current_user.email, new_hash)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update password"
        )

    refresh_user_metrics(db)
    return {
        "status": "success",
        "message": "Password updated successfully"
    }


@router.delete("/me")
@limiter.limit("3/minute")
def delete_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    bump_global_users_version()
    bump_user_version(current_user.id)
    deleted = delete_user(db=db, email=current_user.email)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User could not be deleted or does not exist"
        )

    refresh_user_metrics(db)
    return {
        "status": "success",
        "message": "User account deleted successfully",
        "deleted_user": {
            "email": current_user.email
        }
    }


class AdminUserCreate(BaseModel):
    first_name: str
    last_name: str
    company_name: str
    email: EmailStr
    password: Optional[str] = None
    phone: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_user_by_admin(
    request: Request,
    user_in: AdminUserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered to a company.",
        )
    
    raw_password = user_in.password
    if not raw_password:
        import secrets
        raw_password = secrets.token_urlsafe(12)
        
    try:
        new_user = create_new_user(
            db=db,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            company_name=user_in.company_name,
            email=user_in.email,
            password=hash_password(raw_password),
            phone=user_in.phone,
        )
        
        new_user.is_email_verified = True
        db.commit()
        
        bump_global_users_version()
        
        refresh_user_metrics(db)
        return {
            "status": "success",
            "message": "User created successfully",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "company_name": new_user.company_name,
                "phone": new_user.phone,
                "role": new_user.role,
                "is_active": new_user.is_active,
                "is_email_verified": new_user.is_email_verified,
                "created_at": new_user.created_at
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during user creation: {str(e)}",
        )