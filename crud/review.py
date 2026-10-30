from models.review import Review
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from models.user import User
from sqlalchemy.orm import joinedload


async def get_review_by_id(db: AsyncSession, review_id: int) -> Optional[Review]:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def get_reviews_by_user(db: AsyncSession, user_id: int) -> List[Review]:
    result = await db.execute(select(Review).where(Review.user_id == user_id))
    return list(result.scalars().all())



async def get_reviews_by_user_email(db: AsyncSession, email: str) -> List[Review]:
    result = await db.execute(
    select(Review)
    .join(User, Review.user_id == User.id)
    .where(User.email == email))
    reviews = list(result.scalars().all())
    return reviews


async def get_all_reviews(
    db: AsyncSession,
    published_only: bool = True
):
    query = select(Review).options(joinedload(Review.user))

    if published_only:
        query = query.where(Review.is_published.is_(True))

    result = await db.execute(query)

    return result.scalars().all()



async def create_review(db: AsyncSession,user_id: int,stars: int,review_text: str,is_published: bool = False):
    new_review = Review(
        user_id=user_id,
        stars=stars,
        review_text=review_text,
        is_published=is_published
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review



async def update_review(db: AsyncSession, review_id: int, update_data: dict) -> Optional[Review]:
    review = await get_review_by_id(db, review_id)

    if not review:
        raise

    for key, value in update_data.items():
        if hasattr(review, key):
            setattr(review, key, value)

    await db.commit()
    await db.refresh(review)

    return review



async def delete_review(db: AsyncSession, review_id: int) -> bool:
    review = await get_review_by_id(db, review_id)

    if not review:
        raise

    await db.delete(review)
    await db.commit()

    return True






async def admin_set_review_publish_status(
    db: AsyncSession,
    review_id: int,
    is_published: bool
) -> Optional[Review]:

    review = await get_review_by_id(db, review_id)

    if not review:
        raise

    review.is_published = is_published

    await db.commit()
    await db.refresh(review)


    return review





