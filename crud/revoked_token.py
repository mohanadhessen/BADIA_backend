from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import RevokedToken
from security import hash_token


async def get_revoked_token(db: AsyncSession, token: str):
    hashed_token = hash_token(token)
    result = await db.execute( select(RevokedToken).where(RevokedToken.token == hashed_token))
    revoked = result.scalar_one_or_none()
    if revoked:
        return revoked
    # Fallback for legacy revoked tokens already in the DB
    result = await db.execute( select(RevokedToken).where(RevokedToken.token == token))
    return result.scalar_one_or_none()


async def create_revoked_token(db: AsyncSession, token: str):
    hashed_token = hash_token(token)
    revoked = RevokedToken(token=hashed_token)
    db.add(revoked)
    await db.commit()
    await db.refresh(revoked)

    return revoked


async def is_token_revoked(db: AsyncSession, token: str) -> bool:
    hashed_token = hash_token(token)

    result = await db.execute(
        select(RevokedToken.token).where(
            RevokedToken.token == hashed_token
        ).limit(1)
    )

    if result.scalar_one_or_none() is not None:
        return True

    # Fallback for legacy raw tokens
    result = await db.execute(
        select(RevokedToken.token).where(
            RevokedToken.token == token
        ).limit(1)
    )

    return result.scalar_one_or_none() is not None