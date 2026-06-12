from database.session import SessionLocal
from crud.user import get_user_by_email

db = SessionLocal()
user = get_user_by_email(db, "mohanadhessen@gmail.com")
if user:
    print("User found!")
    print(f"is_email_verified: {user.is_email_verified}")
    print(f"auth_provider: {user.auth_provider}")
else:
    print("User NOT found!")
db.close()
