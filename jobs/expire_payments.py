import logging

import sentry_sdk

from config import settings
from crud.payment import mark_payment_as_failed
from database.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN and settings.ENV == "production":
    sentry_sdk.init(dsn=settings.SENTRY_DSN, send_default_pii=False)


def run_job():
    logger.info("Starting expired payments job")
    db = None
    try:
        db = SessionLocal()
        result = mark_payment_as_failed(db)
        logger.info("Expired payments job completed")
        return result
    except Exception as exc:
        logger.exception("Expired payments job failed")
        sentry_sdk.capture_exception(exc)
        raise
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    run_job()


