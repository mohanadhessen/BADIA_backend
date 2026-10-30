from models.user import User
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from security import hash_password
from sqlalchemy import select , or_ , func
from datetime import datetime, timezone , timedelta

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def admin_get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute( select(User).where(User.email == email, User.role == "user")  )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, id: int) -> Optional[User]:
    return await db.get(User, id)



async def create_new_user(
    db: AsyncSession,
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    company_name: str | None = None,
    password: str | None = None,
    phone: str | None = None,
    google_id: str | None = None,
    avatar_url: str | None = None,
    auth_provider: str = "local",
) -> User:

    if auth_provider == "local" and not password:
        raise ValueError("Password is required for local registration.")

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        company_name=company_name or "",
        email=email,
        password_hash=password,
        google_id=google_id,
        avatar_url=avatar_url,
        phone=phone,
        role="user",
        is_active=True,
        auth_provider=auth_provider,
        is_email_verified=auth_provider == "google",
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user




async def update_user_data(db: AsyncSession, email: str, update_data: dict) -> Optional[User]:
    user = await get_user_by_email(db, email=email)
    if not user:
        raise ValueError("User not found")

    # prevent unsafe updates
    protected_fields = {"id", "email", "is_active"}

    for key, value in update_data.items():
        if key in protected_fields:
            continue
        if hasattr(user, key):
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user



async def delete_user(db: AsyncSession, email: str) -> bool:
    user = await get_user_by_email(db, email=email)
    if not user:
        raise ValueError("User not found")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return True



async def update_user_password(db: AsyncSession, email: str, new_password_hash: str) -> bool:
    user = await get_user_by_email(db, email=email)
    if not user:
       raise ValueError("User not found")
    user.password_hash = new_password_hash
    await db.commit()
    return True




async def admin_update_user_data(db: AsyncSession, email: str, update_data: dict) -> User|None:
    user = await get_user_by_email(db, email=email)
    if not user:
       raise ValueError("User not found")

    for key, value in update_data.items():
        if key == "password" and value:
            user.password_hash = hash_password(value)
        elif hasattr(user, key):
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)


    return user



