from sqlalchemy.orm import Session, joinedload
from models.user import User
from models.review import Review
from models.request import Request
from models.plan import Plan
from sqlalchemy import func, case
from crud.request import get_request_by_id
from crud.review import get_review_by_id
from typing import Optional


def admin_get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def admin_update_user_data(db: Session, email: str, update_data: dict) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user
    


def admin_get_all_users(
    db: Session,
    page: int = 1,
    limit: int = 25,
    only_active: bool = False
):
    offset = (page - 1) * limit

    total_users = db.query(func.count(User.id)).scalar() or 0

    active_users = (
        db.query(func.count(User.id))
        .filter(User.is_active == True)
        .scalar() or 0
    )

    inactive_users = (
        db.query(func.count(User.id))
        .filter(User.is_active == False)
        .scalar() or 0
    )

    verified_users = (
        db.query(func.count(User.id))
        .filter(User.is_email_verified == True)
        .scalar() or 0
    )

    unverified_users = (
        db.query(func.count(User.id))
        .filter(User.is_email_verified == False)
        .scalar() or 0
    )

    query = db.query(User)

    if only_active:
        query = query.filter(User.is_active == True)

    users = (
        query
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "metrics": {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "verified_users": verified_users,
            "unverified_users": unverified_users
        },
        "page": page,
        "limit": limit,
        "has_next": offset + limit < total_users,
        "items": users
    }



def get_users_plans_distribution(db: Session):
    results = (
        db.query(
            func.coalesce(Plan.name, "No Plan").label("plan"),
            func.count(User.id).label("count")
        )
        .select_from(User)
        .outerjoin(Plan, User.current_plan_id == Plan.id)
        .group_by(Plan.id, Plan.name)
        .all()
    )

    return [
        {
            "plan": row.plan,
            "count": row.count
        }
        for row in results
    ]




def admin_get_all_review(
    db: Session,
    page: int = 1,
    limit: int = 25
):
    offset = (page - 1) * limit

    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    published_reviews = (
    db.query(func.count(Review.id))
    .filter(Review.is_published == True)
    .scalar() or 0
    )
    pending_reviews = (
    db.query(func.count(Review.id))
    .filter(Review.is_published == False)
    .scalar() or 0
        )
    reviews = (
        db.query(Review)
        .options(
            joinedload(Review.user)  

        )
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "metrics": {
            "total_reviews": total_reviews,
            "published_reviews": published_reviews,
            "pending_reviews": pending_reviews
        },
        "page": page,
        "limit": limit,
        "has_next": offset + limit < total_reviews,
        "items": reviews}



def admin_get_all_requests(
    db: Session,
    page: int = 1,
    limit: int = 25
):
    offset = (page - 1) * limit


    stats = db.query(
        func.count(Request.id).label("total"),
        func.sum(case((Request.status == "pending", 1), else_=0)).label("pending"),
        func.sum(case((Request.status == "rejected", 1), else_=0)).label("rejected"),
        func.sum(case((Request.status == "approved", 1), else_=0)).label("approved")
    ).first()


    total = stats.total or 0
    pending_count = stats.pending or 0
    rejected = stats.rejected or 0
    approved_count = stats.approved or 0


    requests = (
        db.query(Request)
        .options(
            joinedload(Request.user),
            joinedload(Request.files)
        )
        .order_by(Request.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "metrics": {
            "total": total,
            "pending": pending_count,
            "rejected": rejected,
            "approved": approved_count
        },
        "page": page,
        "limit": limit,
        "has_next": offset + limit < total,
        "items": requests
    }





def admin_delete_request(db: Session, request_id: str) -> bool:
    request = get_request_by_id(db, request_id)
    if not request:
        return False
    db.delete(request)
    db.commit()
    return True



def admin_update_request_status(
    db: Session,
    request_id: str,
    status: str
):
    request = get_request_by_id(db=db, request_id=request_id)

    if not request:
        return False

    request.status = status

    db.commit()
    db.refresh(request)

    return request





def admin_delete_review(db: Session, review_id: int) -> bool:
    review = get_review_by_id(db, review_id)
    if not review:
        return False

    db.delete(review)
    db.commit()
    return True



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

    return review






