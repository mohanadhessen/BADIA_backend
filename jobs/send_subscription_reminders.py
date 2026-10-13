import logging

import sentry_sdk

from config import settings
from crud.subscriptions import get_users_to_remind
from email_service import send_plan_expiry_reminder_email

from database.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN and settings.ENV == "production":
    sentry_sdk.init(dsn=settings.SENTRY_DSN, send_default_pii=False)


def run_job():
    logger.info("Starting subscription reminders job")
    db = None
    try:
        db = SessionLocal()
        users = get_users_to_remind(db)
        logger.info("Found %d users to remind", len(users))
        for user in users:
            subscription = user.current_subscription
            send_plan_expiry_reminder_email(
                email=user.email,
                user_name=" ".join(filter(None, [user.first_name, user.last_name])),
                plan_name=subscription.plan.name,
                expiry_date=subscription.end_date,
            )
        logger.info("Subscription reminders job completed")
    except Exception as exc:
        logger.exception("Subscription reminders job failed")
        sentry_sdk.capture_exception(exc)
        raise
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    run_job()


