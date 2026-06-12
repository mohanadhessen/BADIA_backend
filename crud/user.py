from models.user import User
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.plan import Plan
from security import hash_password





def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, id: int) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()


def create_new_user(
    db: Session, 
    email: str,
    first_name: str | None = None, 
    last_name: str | None = None, 
    company_name: str | None = None, # Made optional for OAuth
    password: str | None = None,     # Made optional for OAuth
    phone: str | None = None,
    google_id: str | None = None,
    avatar_url: str | None = None,
    auth_provider: str = "local"     # Defaults to local if not specified
):
    # If it's a local user, you might want to enforce password/company_name check here
    if auth_provider == "local" and not password:
        raise ValueError("Password is required for local registration.")

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        company_name=company_name or "Not Provided", # Fallback if your DB column is nullable=False
        email=email,
        password_hash=password, # Ensure this is pre-hashed for 'local' users before calling this function
        google_id=google_id,
        avatar_url=avatar_url,
        phone=phone,
        role="user",
        is_active=True,
        auth_provider=auth_provider,
        is_email_verified=True if auth_provider == "google" else False # Google emails are already verified
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user




def update_user_data(db: Session, email: str, update_data: dict):
    db_user = get_user_by_email(db, email=email)
    if not db_user:
        return None

    # prevent unsafe updates
    protected_fields = {"id", "email", "is_active"}

    for key, value in update_data.items():
        if key in protected_fields:
            continue
        if hasattr(db_user, key):
            setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, email: str) -> bool:
    db_user = get_user_by_email(db, email=email)
    if not db_user:
        return False

    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return True


def update_user_password(db: Session, email: str, new_password_hash: str) -> bool:
    db_user = get_user_by_email(db, email=email)
    if not db_user:
        return False
    db_user.password_hash = new_password_hash
    db.commit()
    return True


def admin_update_user_data(db: Session, email: str, update_data: dict) -> User:
    user = db.query(User).filter(User.email == email).first()

    if user:
        for key, value in update_data.items():
            if key == "password" and value:
                user.password_hash = hash_password(value)
            elif hasattr(user, key):
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
