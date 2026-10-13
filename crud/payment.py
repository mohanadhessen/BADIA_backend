from datetime import date, timedelta

from models.payment import Payment 
from models.user import User
from models.plan import Plan
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import or_
from schemas.payment import PaymentBase, PaymentCheckoutRequest, PaymentUpdate
from crud.dashboard_metrics import refresh_payment_metrics, get_dashboard_metrics
from crud.subscriptions import create_subscription













# todo create these two functions : get_payment_by_user_id, get_payments_by_user_email




def get_payment_by_hash(db: Session, payment_hash: str) -> Payment | None:
    return (
        db.query(Payment)
        .filter(Payment.payment_hash == payment_hash,
                Payment.source == "paymentgateway")
        .with_for_update()
        .first()
    )




def create_payment_gateaway(db: Session, data: PaymentCheckoutRequest, billing_cycle: str,user_id:int):
    user = db.query(User).filter(User.id == user_id).first()
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
        user_id=user_id,
        plan_id=data.plan_id,
        amount=amount,
        billing_cycle=billing_cycle,
        status="pending",  
        source="paymentgateway"
    )

    db.add(payment)

    db.commit()
    db.refresh(payment)
    refresh_payment_metrics(db)

    return payment


def mark_payment_as_paid(db: Session, payment_id: int , gateway_token: str):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise ValueError("Payment not found")

    setattr(payment, "gateway_token", gateway_token)

    payment.status = "paid"
    db.commit()
    db.refresh(payment)
    refresh_payment_metrics(db)

    return payment


def mark_payment_as_failed(db: Session):
    db.query(Payment).filter(Payment.status == "pending").update({Payment.status : "failed"},synchronize_session=False)
    db.commit()





def create_payment_admin(db: Session, data: PaymentBase, billing_cycle: str):
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
        status="paid",  
        source="manual"
    )

    db.add(payment)

    db.commit()
    db.refresh(payment)
    end_date = date.today() + timedelta(days=365 if billing_cycle == "yearly" else 30)
    create_subscription(
        db=db,
        user_id=user.id,
        plan_id=plan.id,
        payment_id=payment.id,
        end_date=end_date,
    )
    refresh_payment_metrics(db)

    return payment



def admin_update_manual_payment(db: Session, payment_id: int, data: PaymentUpdate):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise ValueError("Payment not found")

    if data.status:
        payment.status = data.status

    db.commit()
    db.refresh(payment)
    refresh_payment_metrics(db)

    return payment




def admin_get_all_payments(
    db: Session,
    page: int = 1,
    limit: int = 25,
    q: str | None = None,
    status: str | None = None,
    sort: str = "newest",
):
    offset = (page - 1) * limit

    query = (
        db.query(Payment)
        .join(Payment.user)
        .join(Payment.plan)
        .options(
            joinedload(Payment.user),
            joinedload(Payment.plan)
        )
    )

    if status:
        query = query.filter(Payment.status == status)

    if q:
        search_filters = [
            User.email.ilike(f"%{q}%"),
            User.first_name.ilike(f"%{q}%"),
            User.last_name.ilike(f"%{q}%"),
            Plan.name.ilike(f"%{q}%"),
        ]
        if q.isdigit():
            search_filters.append(Payment.id == int(q))

        query = query.filter(or_(*search_filters))

    if sort == "oldest":
        query = query.order_by(Payment.created_at.asc())
    else:  # default / "newest"
        query = query.order_by(Payment.created_at.desc())

    payments_plus_one = (
        query
        .offset(offset)
        .limit(limit + 1)
        .all()
    )

    has_next = len(payments_plus_one) > limit
    payments = payments_plus_one[:limit]

    metrics_row = get_dashboard_metrics(db)

    return {
        "metrics": {
            "total_payments": metrics_row.get("total_payments", 0) if metrics_row else 0,
            "paid_payments": metrics_row.get("paid_payments", 0) if metrics_row else 0,
            "rejected_payments": metrics_row.get("rejected_payments", 0) if metrics_row else 0,
            "canceled_payments": metrics_row.get("canceled_payments", 0) if metrics_row else 0,
            "monthly_payments": metrics_row.get("monthly_payments", 0) if metrics_row else 0,
            "yearly_payments": metrics_row.get("yearly_payments", 0) if metrics_row else 0,
            "payments_this_month": metrics_row.get("payments_this_month", 0) if metrics_row else 0,
            "total_revenue": float(metrics_row.get("total_revenue", 0)) if metrics_row else 0.0,
            "revenue_this_month": float(metrics_row.get("revenue_this_month", 0)) if metrics_row else 0.0,
        },
        "page": page,
        "limit": limit,
        "has_next": has_next,
        "items": payments
    }
