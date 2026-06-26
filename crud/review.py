from models.review import Review
from typing import Optional, List
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import func
from crud.dashboard_metrics import refresh_review_metrics


from crud.dashboard_metrics import refresh_review_metrics, get_dashboard_metrics

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
    pending_only: bool = False,
    q: str | None = None,
    status: str | None = None,
    rating: int | None = None,
    sort: str = "newest"
):
    from sqlalchemy import or_
    from models.user import User
    offset = (page - 1) * limit

    query = db.query(Review).join(User, Review.user_id == User.id).options(joinedload(Review.user))
    if pending_only or status == "pending":
        query = query.filter(Review.is_published == False)
    elif status == "accepted":
        query = query.filter(Review.is_published == True)
        
    if rating:
        query = query.filter(Review.stars == rating)
        
    if q:
        search_filters = [
            User.email.ilike(f"%{q}%"),
            User.first_name.ilike(f"%{q}%"),
            User.last_name.ilike(f"%{q}%"),
            Review.review_text.ilike(f"%{q}%"),
        ]
        if q.isdigit():
            search_filters.append(Review.id == int(q))
        query = query.filter(or_(*search_filters))
        
    if sort == "oldest":
        query = query.order_by(Review.created_at.asc())
    else:
        query = query.order_by(Review.created_at.desc())

    reviews_plus_one = (
        query
        .offset(offset)
        .limit(limit + 1)
        .all()
    )

    has_next = len(reviews_plus_one) > limit
    reviews = reviews_plus_one[:limit]

    metrics_row = get_dashboard_metrics(db)

    return {
        "metrics": {
            "total_reviews": metrics_row.get("total_reviews", 0) if metrics_row else 0,
            "published_reviews": metrics_row.get("published_reviews", 0) if metrics_row else 0,
            "pending_reviews": metrics_row.get("pending_reviews", 0) if metrics_row else 0
        },
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
