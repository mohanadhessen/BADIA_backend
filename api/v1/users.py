from fastapi import APIRouter, Depends, HTTPException, status, Request , Response
from sqlalchemy.orm import Session
import sentry_sdk
from schemas.user import UserUpdate, UserPasswordReset
from database.session import get_db 
from api.dependencies import get_current_user
from models.user import User
from crud.user import update_user_data, delete_user, update_user_password
from security import verify_password, hash_password
from models.UserFile import UserFile
from crud.request import get_request_by_id, delete_request, get_user_requests
from crud.review import get_reviews_by_user
from config import settings
from r2_client import s3
from api.rate_limiter import limiter



R2_BUCKET = settings.R2_BUCKET
router = APIRouter(tags=["Users"])


from api.etag import compute_etag, check_etag, compute_db_etag
from models.request import Request as DBRequest
from models.review import Review


@router.get("/me")
@limiter.limit("60/minute")
def get_user_profile(
    request: Request,
    response: Response,  
    current_user: User = Depends(get_current_user)
):
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
    
    etag = compute_etag(current_user)
    check_etag(request, etag)
    response.headers["ETag"] = etag
    return data


@router.get("/me/requests")
@limiter.limit("60/minute")
def get_my_requests(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    etag = compute_db_etag(db, DBRequest, filters=[DBRequest.user_id == current_user.id], order_by=DBRequest.created_at.desc())
    check_etag(request, etag)

    requests = get_user_requests(db=db, user_id=current_user.id)
    formatted_requests = []
    for req in requests:
        formatted_requests.append({
            "id": req.id,
            "service_type": req.service_type,
            "status": req.status,
            "created_at": req.created_at,
            "files": [
                {
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "created_at": f.created_at
                }
                for f in req.files
            ] if req.files else []
        })

    data = {
        "status": "success",
        "requests": formatted_requests
    }
    
    response.headers["ETag"] = etag
    return data

@router.get("/me/reviews")
@limiter.limit("60/minute")
def get_my_reviews(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    etag = compute_db_etag(db, Review, filters=[Review.user_id == current_user.id], order_by=Review.created_at.desc())
    check_etag(request, etag)

    reviews = get_reviews_by_user(db=db, user_id=current_user.id)
    formatted_reviews = []
    for rev in reviews:
        formatted_reviews.append({
            "id": rev.id,
            "stars": rev.stars,
            "review_text": rev.review_text,
            "is_published": rev.is_published,
            "created_at": rev.created_at,
            "updated_at": rev.updated_at
        })

    data = {
        "status": "success",
        "reviews": formatted_reviews
    }
    
    response.headers["ETag"] = etag
    return data

@router.delete("/me/requests/{request_id}")
@limiter.limit("10/minute")
def delete_my_request(
    request: Request,
    request_id: int,  # Matches your standard request ID type
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    request = get_request_by_id(db=db, request_id=request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
        
    # 2. Guard: Prevent users from deleting requests that belong to someone else
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this request"
        )

    # 3. Trigger your CRUD function to drop storage objects and clear rows
    deletion_result = delete_request(
        db=db,
        request_id=request_id,
        s3=s3,
        bucket=R2_BUCKET
    )

    return {
        "status": "success",
        "message": "Request and associated storage objects deleted successfully",
        "details": deletion_result
    }




@router.patch("/me")
@limiter.limit("10/minute")
def update_user_profile(
    request: Request,
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

    return {
        "status": "success",
        "message": "Password updated successfully"
    }


@router.get("/requests/{request_id}/files/{file_id}")
@limiter.limit("30/minute")
def download_my_file(
    request: Request,
    request_id: int,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    request = get_request_by_id(db=db, request_id=request_id)
    if not request or request.user_id != current_user.id:
        raise HTTPException(404, "Request not found")

    db_file = db.query(UserFile).filter(
        UserFile.file_id == file_id,
        UserFile.request_id == request_id
    ).first()
    if not db_file:
        raise HTTPException(404, "File not found")

    try:
        inline_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": db_file.file_key,
                "ResponseContentDisposition": f'inline; filename="{db_file.filename}"',
            },
            ExpiresIn=300
        )
        download_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": db_file.file_key,
                "ResponseContentDisposition": f'attachment; filename="{db_file.filename}"',
            },
            ExpiresIn=300
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(500, f"Could not generate download URL: {str(e)}")

    from fastapi.responses import JSONResponse

    return JSONResponse({
        "url": inline_url,
        "download_url": download_url,
        "filename": db_file.filename
    })









