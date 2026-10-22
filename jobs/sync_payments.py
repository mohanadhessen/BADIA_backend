from config import settings
from database.session import SessionLocal
from crud.payment import mark_payment_as_failed, get_pending_payments, mark_payment_as_paid
from crud.subscriptions import create_subscription
from email_service import send_plan_update_email
from models.user import User
from models.payment import Payment
from models.subscription import Subscription
from models.plan import Plan
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
import time
import sentry_sdk
import httpx
from crud.dashboard_metrics import refresh_payment_metrics



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN and settings.ENV == "production":
    sentry_sdk.init(dsn=settings.SENTRY_DSN, send_default_pii=False)

MISSING_TOKEN_GRACE_PERIOD = timedelta(minutes=5)

db = SessionLocal()
pending_payments = get_pending_payments(db)

logging.info("Found %d pending payments", pending_payments.count()) # type: ignore


for pending_payment in pending_payments:
    email_args = None

    if not pending_payment.gateway_token:
        created_at = pending_payment.created_at
        if created_at is not None and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        if created_at is None or now - created_at >= MISSING_TOKEN_GRACE_PERIOD:
            pending_payment.status = "failed"
            db.commit()
            refresh_payment_metrics(db)
            logger.warning(
                "Marked payment %s failed because checkout did not produce a gateway token",
                pending_payment.id,
            )
        else:
            logger.info(
                "Skipping payment %s until checkout has time to return a gateway token",
                pending_payment.id,
            )
        continue

    for attempt in range(3):
        try:
            response = httpx.get(
                f"{settings.HESABE_BASE_URL}/api/transaction/{pending_payment.gateway_token}",
                headers={"accessCode": settings.HESABE_ACCESS_CODE, "Accept": "application/json"},
                timeout=30,
            )
            
            if response.status_code == 404:
                logger.warning(
                    "Payment %s not found in Hesabe; marking as failed", pending_payment.id
                )
                mark_payment_as_failed(db, pending_payment.gateway_token)
                break


            response.raise_for_status()

            data = response.json()["data"]

            if data.get("reference_number") != pending_payment.payment_hash:
                raise ValueError("Hesabe payment reference does not match the pending payment")
            if data.get("token") != pending_payment.gateway_token:
                raise ValueError("Hesabe transaction token does not match the pending payment")
            if Decimal(str(data.get("amount"))) != pending_payment.amount:
                raise ValueError("Hesabe transaction amount does not match the pending payment")

            locked_payment = (
                db.query(Payment)
                .filter(Payment.id == pending_payment.id)
                .with_for_update()
                .populate_existing()
                .first()
            )
            if locked_payment is None:
                db.rollback()
                break
            pending_payment = locked_payment
            if pending_payment.status == "paid":
                logger.info("Payment %s was already processed", pending_payment.id)
                db.rollback()
                break

            if data["status"] == "SUCCESSFUL":
                carry = 0
        
                user = db.get(User, pending_payment.user_id)
                if user.current_subscription_id :  # type: ignore
                    current_subscription = db.get(Subscription, user.current_subscription_id)  # type: ignore
                    current_subscription.status = "canceled"  # type: ignore
                    if current_subscription.plan_id == pending_payment.plan_id:# type: ignore
                        carry = max(0, (current_subscription.end_date - date.today()).days)  # type: ignore
        
                days = (365 if pending_payment.billing_cycle == "yearly" else 30) + carry # type: ignore
                end_date = date.today() + timedelta(days=days)

                subscription = create_subscription(
                    db=db,
                    user_id=pending_payment.user_id,
                    plan_id=pending_payment.plan_id,
                    payment_id=pending_payment.id,
                    end_date=end_date,
                    commit=False,
                )

                plan = db.get(Plan, subscription.plan_id)
                amount = (plan.price_yearly if pending_payment.billing_cycle == "yearly" else plan.price_monthly) # type: ignore

                email_args_after_commit = (
                    user.email,# type: ignore
                    user.first_name,# type: ignore
                    plan.name,# type: ignore
                    amount,
                    pending_payment.billing_cycle,
                    pending_payment.gateway_token,
                )

                mark_payment_as_paid(db, data["token"], commit=False)
                db.flush()
                refresh_payment_metrics(db)
                email_args = email_args_after_commit
                logger.info("Payment %s marked as paid", pending_payment.id)

            elif data["status"] in {"FAILED", "DECLINED"}:
                mark_payment_as_failed(db, data["token"])
                logger.info("Payment %s marked as failed", pending_payment.id)
            else:
                db.rollback()


            break

        except Exception as e:
            db.rollback() 

            logger.exception( "Payment %s sync attempt %d/3 failed", pending_payment.id,  attempt + 1,    )
            if attempt < 2:
                time.sleep(60 * (2 ** attempt))
            else:
                sentry_sdk.capture_exception(e)

    else:

        logger.error("Payment %s gave up; it will be retried on the next run", pending_payment.id)


    if email_args:
        try:
            send_plan_update_email(*email_args) # type: ignore
        except Exception:
            logger.exception("Email for payment %s failed", pending_payment.id)
            sentry_sdk.capture_exception()

