from models.payment import Payment 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select
from schemas.payment import  PaymentCheckoutRequest

from crud.user import get_user_by_id
from crud.plan import get_plan_by_id






async def get_payment_py_id(db: AsyncSession,payment_id:int):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()
    


async def get_pending_payments(db: AsyncSession):
    result = await db.execute(select(Payment).where(Payment.status == "pending" , Payment.source == "paymentgateway"))
    return result.scalars().all()



async def get_payment_by_hash(db: AsyncSession, payment_hash: str) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.payment_hash == payment_hash , Payment.source == "paymentgateway"))
    return result.scalar_one_or_none()


async def get_payment_by_gateway_token(db: AsyncSession, gateway_token: str):
    result = await db.execute(select(Payment).where(Payment.gateway_token == gateway_token))
    return result.scalar_one_or_none()


async def create_payment(db: AsyncSession, data: PaymentCheckoutRequest, billing_cycle: str,user_id:int):
    user = await get_user_by_id(db,user_id)
    if not user:
        raise ValueError("User not found")

    plan = await get_plan_by_id(db,data.plan_id)
    if not plan:
        raise ValueError("Plan not found")

    if billing_cycle == "monthly":
        amount = plan.price_monthly
    elif billing_cycle == "yearly":
        amount = plan.price_yearly
    else:
        raise ValueError("Invalid billing cycle")

    payment = Payment(
        user_id=user_id,
        plan_id=data.plan_id,
        amount=amount,
        billing_cycle=billing_cycle,
        status="pending",  
        source="paymentgateway"
    )

    db.add(payment)

    await db.commit()
    await db.refresh(payment)


    return payment


async def mark_payment_as_paid(db: AsyncSession, gateway_token: str, commit: bool = True):
    payment = await get_payment_by_gateway_token(db,gateway_token)
    if not payment:
        raise ValueError("Payment not found")


    payment.status = "paid"
    if commit:
        await db.commit()
        await db.refresh(payment)

    else:
        await db.flush()

    return payment


async def mark_payment_as_failed(db: AsyncSession, gateway_token: str):
    payment = await get_payment_by_gateway_token(db,gateway_token)
    if not payment:
        raise ValueError("Payment not found")


    payment.status = "failed" 
    await db.commit()
    await db.refresh(payment)


    return payment





