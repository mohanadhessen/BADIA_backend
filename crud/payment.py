from models.payment import Payment 
from models.user import User
from models.plan import Plan
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import func
from schemas.payment import PaymentBase , PaymentUpdate
from datetime import datetime
from crud.dashboard_metrics import refresh_payment_metrics



def get_payment_by_user_id(
    db: Session,
    user_id: int,
    status: str | None = None  
):
    query = db.query(Payment).filter(Payment.user_id == user_id)

    if status:
        query = query.filter(Payment.status == status)

    return query.order_by(Payment.created_at.desc()).all()


def get_payments_by_user_email(db: Session, email: str):
    return (
        db.query(Payment)
        .join(User, Payment.user_id == User.id)
        .filter(User.email == email)
        .options(joinedload(Payment.user), joinedload(Payment.plan))
        .order_by(Payment.created_at.desc())
        .all()
    )
    

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
    refresh_payment_metrics(db)

    return payment



def update_payment(
    db: Session,
    payment_id: int,
    data: PaymentUpdate
):
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if not payment:
        raise ValueError("Payment not found")


    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "status":
            if isinstance(value, dict) and "status" in value:
                value = value["status"]
            elif hasattr(value, "status"):
                value = getattr(value, "status")
        setattr(payment, field, value)

    user = db.query(User).filter(User.id == payment.user_id).first()

    if user:
        if payment.status == "paid":
            user.current_plan_id = payment.plan_id

        elif payment.status in ["canceled", "rejected"]:
            user.current_plan_id = None

    db.commit()
    db.refresh(payment)
    refresh_payment_metrics(db)

    return payment



def admin_get_all_payments(
    db: Session,
    page: int = 1,
    limit: int = 25,
    status: str | None = None
):
    offset = (page - 1) * limit

    query = (
        db.query(Payment)
        .options(
            joinedload(Payment.user),
            joinedload(Payment.plan)
        )
    )

    if status:
        query = query.filter(Payment.status == status)

    payments_plus_one = (
        query
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .offset(offset)
        .limit(limit + 1)
        .all()
    )

    has_next = len(payments_plus_one) > limit
    payments = payments_plus_one[:limit]

    return {
        "page": page,
        "limit": limit,
        "has_next": has_next,
        "items": payments
    }