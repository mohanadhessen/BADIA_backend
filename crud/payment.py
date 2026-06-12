from models.payment import Payment 
from models.user import User
from models.plan import Plan
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import func
from schemas.payment import PaymentBase , PaymentUpdate
from datetime import datetime



def get_payment_by_user_id(
    db: Session,
    user_id: int,
    status: str | None = None  
):
    query = db.query(Payment).filter(Payment.user_id == user_id)

    if status:
        query = query.filter(Payment.status == status)

    return query.order_by(Payment.created_at.desc()).all()
    

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

    return payment



def admin_get_all_payments(
    db: Session,
    page: int = 1,
    limit: int = 25,
    status: str | None = None
):
    offset = (page - 1) * limit

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    total_payments = db.query(func.count(Payment.id)).scalar() or 0

    paid_payments = (
        db.query(func.count(Payment.id))
        .filter(Payment.status == "paid")
        .scalar() or 0
    )

    rejected_payments = (
        db.query(func.count(Payment.id))
        .filter(Payment.status == "rejected")
        .scalar() or 0
    )

    canceled_payments = (
        db.query(func.count(Payment.id))
        .filter(Payment.status == "canceled")
        .scalar() or 0
    )

    monthly_payments = (
        db.query(func.count(Payment.id))
        .filter(Payment.billing_cycle == "monthly")
        .scalar() or 0
    )

    yearly_payments = (
        db.query(func.count(Payment.id))
        .filter(Payment.billing_cycle == "yearly")
        .scalar() or 0
    )

    payments_this_month = (
        db.query(func.count(Payment.id))
        .filter(Payment.created_at >= month_start)
        .scalar() or 0
    )

    total_revenue = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status.in_(["paid", "canceled"]))
        .scalar()
    )

    revenue_this_month = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.status.in_(["paid", "canceled"]),
            Payment.created_at >= month_start
        )
        .scalar()
    )

    average_payment_amount = (
        db.query(func.coalesce(func.avg(Payment.amount), 0))
        .filter(Payment.status.in_(["paid", "canceled"]))
        .scalar()
    )

    query = (
        db.query(Payment)
        .options(
            joinedload(Payment.user),
            joinedload(Payment.plan)
        )
    )

    if status:
        query = query.filter(Payment.status == status)

    filtered_count = (
        query.with_entities(func.count(Payment.id))
        .scalar() or 0
    )

    payments = (
        query
        .order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "metrics": {
            "total_payments": total_payments,
            "paid_payments": paid_payments,
            "rejected_payments": rejected_payments,
            "canceled_payments": canceled_payments,
            "monthly_payments": monthly_payments,
            "yearly_payments": yearly_payments,
            "payments_this_month": payments_this_month,
            "total_revenue": float(total_revenue),
            "revenue_this_month": float(revenue_this_month),
            "average_payment_amount": round(float(average_payment_amount), 2)
        },
        "page": page,
        "limit": limit,
        "has_next": offset + limit < filtered_count,
        "items": payments
    }