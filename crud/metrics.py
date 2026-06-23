from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from models.email_metric import EmailMetric
from models.user_file import UserFile
from datetime import datetime


def log_email_sent(db: Session, recipient: str, subject: str):
    new_log = EmailMetric(recipient=recipient, subject=subject)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def get_emails_metric(db_session):
    now = datetime.now()
    daily_count = (
        db_session.query(EmailMetric)
        .filter(func.date(EmailMetric.sent_at) == now.date())
        .count()
    )
    monthly_count = (
        db_session.query(EmailMetric)
        .filter(func.extract('year', EmailMetric.sent_at) == now.year)
        .filter(func.extract('month', EmailMetric.sent_at) == now.month)
        .count()
    )

    return {
        "daily_count": daily_count,
        "monthly_count": monthly_count,
        "day_limit": 300,
        "month_limit": 3000
    }


def get_files_metric(db: Session):
    total_bytes, total_files = db.query(
        func.coalesce(func.sum(UserFile.size), 0),
        func.count(UserFile.id)
    ).one()

    total_bytes = int(total_bytes)
    total_gb = total_bytes / (1024 ** 3)
    FREE_TIER_GB = 10
    return {
        "used_bytes": total_bytes,
        "used_kb": round(total_bytes / 1024, 2),
        "used_mb": round(total_bytes / (1024 ** 2), 4),
        "used_gb": round(total_bytes / (1024 ** 3), 6),
        "remaining_gb": round(max(FREE_TIER_GB - total_gb, 0), 6),
        "usage_percent": round((total_gb / FREE_TIER_GB) * 100, 6),
        "total_files": total_files,
    }