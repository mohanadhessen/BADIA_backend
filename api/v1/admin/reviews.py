from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from api.etag import compute_etag, check_etag, compute_db_etag
from models.review import Review
from crud.review import (
    admin_get_all_review,
    delete_review,
    admin_set_review_publish_status,
)
from schemas.admin import ReviewPublishUpdate


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
    db: Session = Depends(get_db)
):
    etag = compute_db_etag(db, Review, page=page, limit=limit, order_by=Review.created_at.desc())
    check_etag(request, etag)
    
    data = admin_get_all_review(
        db=db,
        page=page,
        limit=limit
    )
    response.headers["ETag"] = etag
    return data


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
