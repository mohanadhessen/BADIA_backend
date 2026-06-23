from models.review import Review
from typing import Optional, List
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import func
from crud.dashboard_metrics import refresh_review_metrics


def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    return db.query(Review).filter(Review.id == review_id).first()


def get_reviews_by_user(db: Session, user_id: int) -> List[Review]:
    return db.query(Review).filter(Review.user_id == user_id).all()


def get_reviews_by_user_email(db: Session, email: str) -> List[Review]:
    from models.user import User
    return (
        db.query(Review)
        .join(User, Review.user_id == User.id)
        .filter(User.email == email)
        .options(joinedload(Review.user))
        .order_by(Review.created_at.desc())
        .all()
    )


def get_all_reviews(
    db: Session,
    published_only: bool = True
):
    query = db.query(Review).options(joinedload(Review.user))

    if published_only:
        query = query.filter(Review.is_published == True)

    return query.all()


def create_review(
    db: Session,
    user_id: int,
    stars: int,
    review_text: str,
    is_published: bool = False
):
    new_review = Review(
        user_id=user_id,
        stars=stars,
        review_text=review_text,
        is_published=is_published
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    refresh_review_metrics(db)
    return new_review


def update_review(db: Session, review_id: int, update_data: dict) -> Optional[Review]:
    review = get_review_by_id(db, review_id)

    if not review:
        return None

    for key, value in update_data.items():
        if hasattr(review, key):
            setattr(review, key, value)

    db.commit()
    db.refresh(review)
    refresh_review_metrics(db)
    return review



def delete_review(db: Session, review_id: int) -> bool:
    review = get_review_by_id(db, review_id)

    if not review:
        return False

    db.delete(review)
    db.commit()
    refresh_review_metrics(db)
    return True



def admin_get_all_review(
    db: Session,
    page: int = 1,
    limit: int = 25,
    pending_only: bool = False
):
    offset = (page - 1) * limit

    query = db.query(Review).options(joinedload(Review.user))
    if pending_only:
        query = query.filter(Review.is_published == False)

    reviews_plus_one = (
        query
        .order_by(Review.created_at.desc(), Review.id.desc())
        .offset(offset)
        .limit(limit + 1)
        .all()
    )

    has_next = len(reviews_plus_one) > limit
    reviews = reviews_plus_one[:limit]

    return {
        "page": page,
        "limit": limit,
        "has_next": has_next,
        "items": reviews
    }



def admin_set_review_publish_status(
    db: Session,
    review_id: int,
    is_published: bool
) -> Optional[Review]:

    review = get_review_by_id(db, review_id)

    if not review:
        return None

    review.is_published = is_published

    db.commit()
    db.refresh(review)
    refresh_review_metrics(db)

    return review
