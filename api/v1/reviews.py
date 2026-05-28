from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.review import ReviewCreate  , ReviewUpdate
from database.session import get_db 
from api.dependencies import get_current_user
from models.user import User
from crud.review import   update_review , delete_review , get_review_by_id , create_review



router = APIRouter(tags=["Reviews"])


@router.post("")
def create_review_endpoint(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_review(
        db=db,
        user_id=current_user.id,
        stars=data.stars,
        review_text=data.review_text,
        is_published=False  # always false initially
    )

@router.patch("/{review_id}")
def update_review_endpoint(
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

    # prevent user from changing publish state
    update_data.pop("is_published", None)

    updated = update_review(db, review_id, update_data)

    return updated


@router.delete("/{review_id}")
def delete_review_endpoint(
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

    return {"status": "success"}