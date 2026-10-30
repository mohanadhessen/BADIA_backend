from models.plan import Plan
from models.payment import Payment
from sqlalchemy import func , select
from sqlalchemy.ext.asyncio import AsyncSession 


async def get_plans_cache_metadata(db: AsyncSession):
    result = await db.execute(select( func.max(Plan.updated_at), func.count(Plan.id) ))

    last_updated, count = result.one()

    return {"last_updated": last_updated,"count": count}

async def get_all_plans(db: AsyncSession):
    result = await db.execute(select(Plan))
    return result.scalars().all()


async def get_plan_by_id(db: AsyncSession, plan_id: int):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalar_one_or_none()

async def get_plan_by_name(db: AsyncSession, name: str):
    result = await db.execute(select(Plan).where(Plan.name == name))
    return result.scalar_one_or_none()


async def create_plan(db: AsyncSession, data: dict):
    plan = Plan(**data)

    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return plan


async def update_plan(db: AsyncSession, plan: Plan, data: dict):
    update_data = {
        key: value
        for key, value in data.items()
        if value is not None
    }

    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)

    return plan


async def delete_plan(db: AsyncSession, plan: Plan):
    await db.delete(plan)
    await db.commit()

    return True