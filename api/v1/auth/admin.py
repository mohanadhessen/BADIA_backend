from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from crud.admin import admin_get_all_users , admin_get_user_by_email
from ...dependencies import require_admin

router = APIRouter(
    prefix="",
    tags=["admin"],
    dependencies=[Depends(require_admin)]
)




@router.get("/")
def admin_root():
    return {"message": "Admin API is active"}


@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    return admin_get_all_users(db)


@router.get("/users/{email}")
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    return admin_get_user_by_email(db, email)



