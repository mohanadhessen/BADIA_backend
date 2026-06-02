from models.review import Review
from typing import Optional, List
from sqlalchemy.orm import Session , joinedload


def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    return db.query(Review).filter(Review.id == review_id).first()


def get_reviews_by_user(db: Session, user_id: int) -> List[Review]:
    return db.query(Review).filter(Review.user_id == user_id).all()


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
    return review



def delete_review(db: Session, review_id: int) -> bool:
    review = get_review_by_id(db, review_id)

    if not review:
        return False

    db.delete(review)
    db.commit()
    return True



