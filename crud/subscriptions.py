from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date , timedelta
from models.subscription import Subscription
from crud.user import get_user_by_id
from schemas.subscription import SubscriptionStatus
from sqlalchemy import select , update
from models.user import User
from crud.plan import get_plan_by_id
from crud.payment import get_payment_py_id




async def get_subscription_by_id(db: AsyncSession,id: int):
    result = await db.execute(select(Subscription).where(Subscription.id == id))
    return result.scalar_one_or_none()



async def get_user_subscription_by_user_id(db: AsyncSession,user_id: int,):
    user = await get_user_by_id(db,user_id)
    if not user:
        raise ValueError("User not found")
    if not user.current_subscription_id:
        return {}
    
    result = await db.execute(select(Subscription).where(Subscription.id == user.current_subscription_id , Subscription.status == "active"))
    subscription = result.scalar_one_or_none()
    if not subscription:
        return {}
    if not subscription.plan_id:
        return {}
    plan = await get_plan_by_id(db,subscription.plan_id)
    payment = await get_payment_py_id(db,subscription.payment_id)

    if not payment:
        raise ValueError("payment not found")

    return {
        "subscription_id": subscription.subscription_id,
        "status": subscription.status,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "billing_cycle": payment.billing_cycle,
        "amount_paid": payment.amount,
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "plan_details": plan.plan_details,
        } if plan else None,
    }
    


        



  
async def create_subscription(
    db: AsyncSession,
    user_id: int,
    plan_id: int,
    payment_id: int,
    end_date: date,
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
    commit: bool = True,
):
    
    subscription = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        payment_id=payment_id,
        end_date=end_date,       
        status=status,
    )

    user = await get_user_by_id(db, user_id)
    db.add(subscription)
    await db.flush()  

    if user is not None:
        user.current_subscription_id = subscription.id

    if commit:
        await db.commit()
        await db.refresh(subscription)

    return subscription



async def expiring_subscriptions(db: AsyncSession):
    today = date.today()

    expired_ids = select(Subscription.id).where(
        Subscription.end_date <= today,
        Subscription.status == "active",
    )

    result = await db.execute(
        select(User, Subscription)
        .join(Subscription, User.current_subscription_id == Subscription.id)
        .where(Subscription.id.in_(expired_ids))
    )
    expired_subscriptions = result.all()

    await db.execute(
        update(User)
        .where(User.current_subscription_id.in_(expired_ids))
        .values(current_subscription_id=None)
    )

    await db.execute(
        update(Subscription)
        .where(Subscription.id.in_(expired_ids))
        .values(status="expired")
    )

    await db.commit()

    return expired_subscriptions



async def get_users_to_remind(db: AsyncSession):
    reminder_date = date.today() + timedelta(days=3)

    result = await db.execute(
        select(User)
        .join(Subscription, User.current_subscription_id == Subscription.id)
        .where(
            Subscription.status == "active",
            Subscription.end_date == reminder_date,
        )
    )

    return result.scalars().all()



