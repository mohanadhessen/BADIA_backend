from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from models.email_metric import EmailMetric

def log_email_sent(db: Session, recipient: str, subject: str):
    new_log = EmailMetric(recipient=recipient, subject=subject)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def get_emails_metric(db: Session):
    now = datetime.now(timezone.utc)
    
    daily_count = db.query(EmailMetric).filter(
        func.extract('year', EmailMetric.sent_at) == now.year,
        func.extract('month', EmailMetric.sent_at) == now.month,
        func.extract('day', EmailMetric.sent_at) == now.day
    ).count()

    monthly_count = db.query(EmailMetric).filter(
        func.extract('year', EmailMetric.sent_at) == now.year,
        func.extract('month', EmailMetric.sent_at) == now.month
    ).count()

    return {
        "daily_count": daily_count,
        "monthly_count": monthly_count,
        "day_limit": 300,
        "month_limit": 3000
    }
