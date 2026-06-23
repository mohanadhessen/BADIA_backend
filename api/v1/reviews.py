from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from schemas.review import ReviewCreate, ReviewUpdate
from database.session import get_db
from api.dependencies import get_current_user
from models.user import User

from crud.review import (
    update_review,
    delete_review,
    get_review_by_id,
    create_review,
    get_reviews_by_user
)

from api.rate_limiter import limiter
from cache.reviews import (
    bump_global_reviews_version,
    bump_user_review_version,
    get_review_version
)
from cache.etags import make_etag, check_etag


router = APIRouter(tags=["Reviews"])



@router.get("")
@limiter.limit("60/minute")
def get_my_reviews(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = get_review_version(current_user.id)

    if version == 0:
        bump_user_review_version(current_user.id)
        version = 1

    etag = make_etag(version)
    if check_etag(request, response, etag):
        return Response(status_code=304)

    reviews = get_reviews_by_user(db=db, user_id=current_user.id)

    return {
        "status": "success",
        "reviews": [
            {
                "id": r.id,
                "stars": r.stars,
                "review_text": r.review_text,
                "is_published": r.is_published,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in reviews
        ]
    }


# -------------------------
# POST (create)
# -------------------------
@router.post("")
@limiter.limit("5/minute")
def create_review_endpoint(
    request: Request,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = create_review(
        db=db,
        user_id=current_user.id,
        stars=data.stars,
        review_text=data.review_text,
        is_published=False
    )

    bump_user_review_version(current_user.id)
    bump_global_reviews_version()

    return review


# -------------------------
# PATCH (update)
# -------------------------
@router.patch("/{review_id}")
@limiter.limit("10/minute")
def update_review_endpoint(
    request: Request,
    review_id: int,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = get_review_by_id(db, review_id)

    if not review:
        raise HTTPException(404, "Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("is_published", None)

    updated = update_review(db, review_id, update_data)

    bump_user_review_version(current_user.id)
    bump_global_reviews_version()

    return updated


# -------------------------
# DELETE (remove)
# -------------------------
@router.delete("/{review_id}")
@limiter.limit("10/minute")
def delete_review_endpoint(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = get_review_by_id(db, review_id)

    if not review:
        raise HTTPException(404, "Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    delete_review(db, review_id)

    bump_user_review_version(current_user.id)
    bump_global_reviews_version()

    return {"status": "success"}