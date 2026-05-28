from models.user import User
from typing import Optional
from sqlalchemy.orm import Session



def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()




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
        current_plan_id=1,
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