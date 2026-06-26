from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from models.user import User
from models.plan import Plan
from crud.user import (
    admin_get_all_users,
    get_user_by_email,
    admin_get_user_by_email,
    get_users_plans_distribution,
    admin_update_user_data,
    get_user_by_id,
    delete_user
)
from schemas.admin import AdminUserUpdateSchema
from schemas.user import AdminUserSearchResponse
from crud.dashboard_metrics import refresh_user_metrics 
from cache.user import get_global_users_version, bump_global_users_version, bump_user_version
from cache.etags import make_etag, check_etag


router = APIRouter(
    prefix="",
    tags=["Admin - Users"],
    dependencies=[Depends(require_admin)]
)


@router.get("/users")
@limiter.limit("60/minute")
def get_all_users(
    request: Request,
    response: Response,
    page: int = 1,
    limit: int = 25,
    only_active: bool = False,
    plan: str | None = None,
    status: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db)
):
    version = get_global_users_version()
    etag_str = f"{version}:{page}:{limit}:{only_active}:{plan}:{status}:{q}"
    etag = make_etag(etag_str)
    
    if check_etag(request, response, etag):
        return {}

    filters = [User.role == "user"]
    if only_active or status == "active":
        filters.append(User.is_active == True)
    elif status == "inactive":
        filters.append(User.is_active == False)
        
    if plan:
        from models.plan import Plan
        filters.append(User.current_plan.has(Plan.name == plan))
        
    data = admin_get_all_users(
        db=db,
        page=page,
        limit=limit,
        only_active=only_active,
        plan=plan,
        status=status,
        q=q
    )
    return data


@router.get("/users/plan-distribution")
@limiter.limit("60/minute")
def get_users_plan_distribution(request: Request, db: Session = Depends(get_db)):
    data = get_users_plans_distribution(db)
    return data




@router.patch("/users/{email}")
@limiter.limit("30/minute")
def update_user_data(
    request: Request,
    email: str,
    payload: AdminUserUpdateSchema,
    db: Session = Depends(get_db)
):
    update_dict = payload.model_dump(exclude_unset=True)

    updated_user = admin_update_user_data(
        db=db,
        email=email,
        update_data=update_dict
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    refresh_user_metrics(db)
    bump_global_users_version()
    bump_user_version(updated_user.id)
    return updated_user



@router.delete("/users/{identifier}")
@limiter.limit("20/minute")
def delete_user_endpoint(
    request: Request,
    identifier: str,
    db: Session = Depends(get_db)
):
    if "@" in identifier:
        user = get_user_by_email(db, identifier)
    else:
        try:
            user = get_user_by_id(db, int(identifier))
        except ValueError:
            raise HTTPException(400, "Invalid user identifier")

    if not user:
        raise HTTPException(404, "User not found")

    success = delete_user(db, user.email)
    if not success:
        raise HTTPException(400, "Could not delete user")

    refresh_user_metrics(db)
    bump_global_users_version()
    bump_user_version(user.id)
    return {"message": "User deleted successfully"}



@router.get("/user")
@limiter.limit("60/minute")
def get_user_endpoint(
    request: Request,
    user_id: int | None = None,
    email: str | None = None,
    db: Session = Depends(get_db)
):
    if user_id is None and email is None:
        raise HTTPException(
            status_code=400,
            detail="Either user_id or email is required"
        )

    filters = []
    if user_id is not None:
        filters.append(User.id == user_id)
    else:
        filters.append(User.email == email)

    if user_id is not None:
        user = get_user_by_id(db, user_id)
    else:
        user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.get("/users/by-email", response_model=AdminUserSearchResponse)
@limiter.limit("60/minute")
def get_user_by_email_endpoint(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email query parameter is required"
        )
    user = admin_get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/users/search/autocomplete")
@limiter.limit("120/minute")
def autocomplete_user_emails(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db)
):
    if not q:
        return []
    emails = (
        db.query(User.email)
        .filter(User.role == "user")
        .filter(User.email.ilike(f"{q}%"))
        .limit(15)
        .all()
    )
    return [email[0] for email in emails]


@router.get("/users/search/results")
@limiter.limit("30/minute")
def search_user_by_email(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    if not email:
        raise HTTPException(status_code=400, detail="Email query parameter is required")
        
    user = db.query(User).filter(User.email == email, User.role == "user").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    from models.request import Request as DBRequest
    from models.review import Review as DBReview
    from sqlalchemy.orm import joinedload
    
    requests = (
        db.query(DBRequest)
        .options(joinedload(DBRequest.files))
        .filter(DBRequest.user_id == user.id)
        .order_by(DBRequest.created_at.desc())
        .all()
    )
    
    reviews = (
        db.query(DBReview)
        .filter(DBReview.user_id == user.id)
        .order_by(DBReview.created_at.desc())
        .all()
    )
    
    formatted_requests = [
        {
            "id": r.id,
            "request_id": r.request_id,
            "service_type": r.service_type,
            "status": r.status,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "files": [
                {
                    "id": f.id,
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "file_key": f.file_key,
                    "content_type": f.content_type,
                    "size": f.size,
                    "created_at": f.created_at,
                }
                for f in r.files
            ]
        }
        for r in requests
    ]
    
    formatted_reviews = [
        {
            "id": rev.id,
            "stars": rev.stars,
            "review_text": rev.review_text,
            "is_published": rev.is_published,
            "created_at": rev.created_at,
            "updated_at": rev.updated_at
        }
        for rev in reviews
    ]
    
    return {
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "company_name": user.company_name,
            "email": user.email,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "is_email_verified": user.is_email_verified,
            "current_plan_id": user.current_plan_id,
            "subscription_end_date": user.subscription_end_date,
            "created_at": user.created_at,
        },
        "requests": formatted_requests,
        "reviews": formatted_reviews
    }