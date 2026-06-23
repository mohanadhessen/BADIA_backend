from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from models.review import Review
from crud.review import (
    admin_get_all_review,
    delete_review,
    admin_set_review_publish_status,
    get_reviews_by_user_email,
)
from schemas.admin import ReviewPublishUpdate
from schemas.review import AdminReviewResponse


router = APIRouter(
    prefix="",
    tags=["Admin - Reviews"],
    dependencies=[Depends(require_admin)]
)


@router.get("/reviews")
@limiter.limit("60/minute")
def get_all_reviews(
    request: Request,
    page: int = 1,
    limit: int = 25,
    db: Session = Depends(get_db)
):
    data = admin_get_all_review(
        db=db,
        page=page,
        limit=limit
    )
    return data


@router.get("/reviews/by-email", response_model=list[AdminReviewResponse])
@limiter.limit("60/minute")
def get_reviews_by_email_endpoint(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email query parameter is required"
        )
    reviews = get_reviews_by_user_email(db, email)
    return reviews


@router.delete("/reviews/{review_id}")
@limiter.limit("30/minute")
def delete_review_endpoint(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db)
):
    success = delete_review(db=db, review_id=review_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return {"success": True, "review_id": review_id}


@router.patch("/reviews/{review_id}/publish")
@limiter.limit("30/minute")
def set_review_publish_status(
    request: Request,
    review_id: int,
    body: ReviewPublishUpdate,
    db: Session = Depends(get_db)
):
    review = admin_set_review_publish_status(
        db=db,
        review_id=review_id,
        is_published=body.is_published
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return review
