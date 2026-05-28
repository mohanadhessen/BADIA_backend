from models.user import User
from sqlalchemy.orm import Session


def admin_get_all_users(db: Session, only_active: bool = False):
    query = db.query(User)

    if only_active:
        query = query.filter(User.is_active == True)

    return query.all()


def admin_get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()




def admin_deactivate_user(db: Session, email: str) -> bool:
    user = admin_get_user_by_email(db, email=email)
    if not user:
        return False

    user.is_active = False
    db.commit()
    return True

def admin_delete_user(db: Session, email: str) -> bool:
    
    user = admin_get_user_by_email(db, email=email)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True