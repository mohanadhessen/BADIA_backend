from sqlalchemy.orm import Session
from datetime import date

from models.subscriptions import Subscription


def get_subscription_by_user_id(db: Session, user_id: int):
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if subscription and subscription.status == "active" and subscription.end_date < date.today():
        subscription.status = "expired"
        db.commit()
    return subscription
