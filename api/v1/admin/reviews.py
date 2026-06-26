from fastapi import APIRouter, Depends, HTTPException, Request, Response
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
from crud.dashboard_metrics import refresh_review_metrics
from cache.reviews import bump_global_reviews_version , bump_user_review_version, get_global_reviews_version
from cache.etags import make_etag, check_etag


router = APIRouter(
    prefix="",
    tags=["Admin - Reviews"],
    dependencies=[Depends(require_admin)]
)


@router.get("/reviews")
@limiter.limit("60/minute")
def get_all_reviews(
    request: Request,
    response: Response,
    page: int = 1,
    limit: int = 25,
    q: str | None = None,
    status: str | None = None,
    rating: int | None = None,
    sort: str = "newest",
    db: Session = Depends(get_db)
):
    version = get_global_reviews_version()
    etag_str = f"{version}:{page}:{limit}:{q}:{status}:{rating}:{sort}"
    etag = make_etag(etag_str)
    
    if check_etag(request, response, etag):
        return {}

    data = admin_get_all_review(
        db=db,
        page=page,
        limit=limit,
        q=q,
        status=status,
        rating=rating,
        sort=sort
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
    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        bump_user_review_version(review.user_id)
    bump_global_reviews_version()
    success = delete_review(db=db, review_id=review_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    refresh_review_metrics(db)
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

    bump_user_review_version(review.user_id)
    bump_global_reviews_version()

    refresh_review_metrics(db)
    return review
