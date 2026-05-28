from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.user import UserUpdate
from database.session import get_db 
from api.dependencies import get_current_user
from models.user import User
from crud.user import update_user_data , delete_user
router = APIRouter()
router = APIRouter(tags=["Users"])


@router.get("/me")
def get_user_profile(current_user: User = Depends(get_current_user)):
    return {
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
            "is_email_verified":current_user.is_email_verified
        }
    }




@router.patch("/me")
def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Extract only the fields the user actually sent
    update_dict = user_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
        
    # 2. Call your existing CRUD utility function
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

    # 3. Return the exact same format as your GET endpoint
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


@router.delete("/me")
def delete_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    deleted = delete_user(db=db, email=current_user.email)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User could not be deleted or does not exist"
        )

    return {
        "status": "success",
        "message": "User account deleted successfully",
        "deleted_user": {
            "email": current_user.email
        }
    }


