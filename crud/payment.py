from models.payment import Payment 
from models.user import User
from models.plan import Plan
from sqlalchemy.orm import Session 
from sqlalchemy import func
from schemas.payment import PaymentBase


def create_payment(db: Session, data: PaymentBase, billing_cycle: str):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise ValueError("User not found")

    plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
    if not plan:
        raise ValueError("Plan not found")

    if billing_cycle == "monthly":
        amount = plan.price_monthly
    elif billing_cycle == "yearly":
        amount = plan.price_yearly
    else:
        raise ValueError("Invalid billing cycle")

    payment = Payment(
        user_id=data.user_id,
        plan_id=data.plan_id,
        amount=amount,
        billing_cycle=billing_cycle,
        start_date=data.start_date,
        end_date=data.end_date,
        status="paid"  
    )

    db.add(payment)

    user.current_plan_id = plan.id

    db.commit()
    db.refresh(payment)

    return payment



def update_payment_status(db: Session, payment_id: int, status: str):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise ValueError("Payment not found")

    allowed_statuses = {"paid", "rejected", "canceled"}
    if status not in allowed_statuses:
        raise ValueError("Invalid status")

    payment.status = status

    if status == "paid":
        user = db.query(User).filter(User.id == payment.user_id).first()
        if user:
            user.plan_id = payment.plan_id

    db.commit()
    db.refresh(payment)

    return payment




def get_payments_telemetry(db: Session):

    results = (
        db.query(
            Payment.status,
            func.count(Payment.id)
        )
        .group_by(Payment.status)
        .all()
    )

    stats = {
        "paid": 0,
        "rejected": 0,
        "canceled": 0,
    }

    for status, count in results:
        stats[status] = count

    total = sum(stats.values())

    return {
        "total_payments": total,
        "by_status": stats
    }