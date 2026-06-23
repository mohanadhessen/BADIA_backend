from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from models.payment import Payment
from crud.user import get_user_by_id
from crud.plan import get_plan_by_id
from crud.payment import create_payment, update_payment, admin_get_all_payments , get_payment_by_user_id, get_payments_by_user_email
from email_service import send_plan_update_email , send_plan_cancelled_by_admin_email
from schemas.payment import PaymentBase , PaymentUpdate, AdminPaymentResponse



router = APIRouter(
    prefix="",
    tags=["Admin - payment"],
    dependencies=[Depends(require_admin)]
)


@router.get("/payments")
@limiter.limit("60/minute")
def get_all_payments(
    request: Request,
    page: int = 1,
    limit: int = 25,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    data = admin_get_all_payments(
        db=db,
        page=page,
        limit=limit,
        status=status
    )
    return data


@router.get("/payments/by-email", response_model=list[AdminPaymentResponse])
@limiter.limit("60/minute")
def get_payments_by_email_endpoint(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email query parameter is required"
        )
    payments = get_payments_by_user_email(db, email)
    return payments



@router.post("/payments")
def create_new_payment(
    data: PaymentBase,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_paid_payment = get_payment_by_user_id(db=db, user_id=data.user_id, status="paid")

    if existing_paid_payment:
        raise HTTPException(
            status_code=400,
            detail="User already has an active paid payment"
        )

    try:
        payment = create_payment(db=db, data=data, billing_cycle=data.billing_cycle)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = get_user_by_id(db, payment.user_id)
    plan = get_plan_by_id(db, payment.plan_id)

    if user and plan:
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.company_name
        background_tasks.add_task(
            send_plan_update_email,
            email=user.email,
            user_name=user_name,
            plan_name=plan.name,
            amount=payment.amount,
            billing_cycle=payment.billing_cycle,
            transaction_id=str(payment.id)
        )
    return {"message": "Payment created successfully", "payment_id": payment.id}

@router.patch("/payments/{payment_id}")
def update_payment_endpoint(
    payment_id: int,
    data: PaymentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        payment = update_payment(
            db=db,
            payment_id=payment_id,
            data=data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = get_user_by_id(db, payment.user_id)
    plan = get_plan_by_id(db, payment.plan_id)

    if user and plan:
        user_name = (
            f"{user.first_name or ''} {user.last_name or ''}".strip()
            or user.company_name
        )

        if payment.status == "paid":
            background_tasks.add_task(
                send_plan_update_email,
                email=user.email,
                user_name=user_name,
                plan_name=plan.name,
                amount=payment.amount,
                billing_cycle=payment.billing_cycle,
                transaction_id=str(payment.id),
            )

        elif payment.status in {"canceled", "rejected"}:
            background_tasks.add_task(
                send_plan_cancelled_by_admin_email,
                email=user.email,
                user_name=user_name,
                plan_name=plan.name,
            )

    return {
        "message": "Payment updated successfully",
        "payment_id": payment.id,
        "status": payment.status,
    }