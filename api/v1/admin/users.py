from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from api.etag import compute_etag, check_etag
from crud.user import (
    admin_get_all_users,
    get_user_by_email,
    get_users_plans_distribution,
    admin_update_user_data,
    get_user_by_id,
    delete_user
)
from schemas.admin import AdminUserUpdateSchema


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
    db: Session = Depends(get_db)
):
    data = admin_get_all_users(
        db=db,
        page=page,
        limit=limit,
        only_active=only_active
    )
    etag = compute_etag(data)
    check_etag(request, etag)
    response.headers["ETag"] = etag
    return data


@router.get("/users/plan-distribution")
@limiter.limit("60/minute")
def get_users_plan_distribution(request: Request, response: Response, db: Session = Depends(get_db)):
    data = get_users_plans_distribution(db)
    etag = compute_etag(data)
    check_etag(request, etag)
    response.headers["ETag"] = etag
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

    return {"message": "User deleted successfully"}



@router.get("/user")
@limiter.limit("60/minute")
def get_user_endpoint(
    request: Request,
    response: Response,
    user_id: int | None = None,
    email: str | None = None,
    db: Session = Depends(get_db)
):
    if user_id is None and email is None:
        raise HTTPException(
            status_code=400,
            detail="Either user_id or email is required"
        )

    if user_id is not None:
        user = get_user_by_id(db, user_id)
    else:
        user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    etag = compute_etag(user)
    check_etag(request, etag)
    response.headers["ETag"] = etag
    return user