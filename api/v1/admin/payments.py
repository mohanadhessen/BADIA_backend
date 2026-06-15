from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Response
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from api.etag import compute_etag, check_etag, compute_db_etag
from models.payment import Payment
from crud.user import get_user_by_id
from crud.plan import get_plan_by_id
from crud.payment import create_payment, update_payment, admin_get_all_payments , get_payment_by_user_id
from email_service import send_plan_update_email , send_plan_cancelled_by_admin_email
from schemas.payment import PaymentBase , PaymentUpdate



router = APIRouter(
    prefix="",
    tags=["Admin - payment"],
    dependencies=[Depends(require_admin)]
)


@router.get("/payments")
@limiter.limit("60/minute")
def get_all_payments(
    request: Request,
    response: Response,
    page: int = 1,
    limit: int = 25,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    filters = [Payment.status == status] if status else None
    etag = compute_db_etag(db, Payment, page=page, limit=limit, filters=filters, order_by=Payment.created_at.desc())
    check_etag(request, etag)

    data = admin_get_all_payments(
        db=db,
        page=page,
        limit=limit,
        status=status
    )
    response.headers["ETag"] = etag
    return data



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