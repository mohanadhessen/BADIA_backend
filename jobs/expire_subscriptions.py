import logging

import sentry_sdk

from config import settings
from crud.subscriptions import expiring_subscriptions
from email_service import send_plan_expiry_email

from database.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN and settings.ENV == "production":
    sentry_sdk.init(dsn=settings.SENTRY_DSN, send_default_pii=False)


def run_job():
    logger.info("Starting expired subscriptions job")
    db = None
    try:
        db = SessionLocal()
        expired_subscriptions = expiring_subscriptions(db)
        logger.info("Found %d expired subscriptions", len(expired_subscriptions))
        for user, subscription in expired_subscriptions:
            send_plan_expiry_email(
                email=user.email,
                user_name=" ".join(filter(None, [user.first_name, user.last_name])),
                plan_name=subscription.plan.name,
                expiry_date=subscription.end_date,
            )
        logger.info("Expired subscriptions job completed")
    except Exception as exc:
        logger.exception("Expired subscriptions job failed")
        sentry_sdk.capture_exception(exc)
        raise
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    run_job()


