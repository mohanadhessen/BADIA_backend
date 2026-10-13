from sqlalchemy.orm import Session
from datetime import date , timedelta
from models.subscription import Subscription
from crud.user import get_user_by_id
from enum import StrEnum
from sqlalchemy import select
from models.user import User

class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"

def create_subscription(db:Session, user_id:int , plan_id:int , payment_id:int ,end_date :date,status:SubscriptionStatus = SubscriptionStatus.ACTIVE ) :
    
    subscription = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        payment_id=payment_id,
        end_date=end_date,       
        status=status,
    )
    user = get_user_by_id(db=db , id=user_id)
    db.add(subscription)
    db.flush()  # Generates subscription.id

    if user is not None:
        user.current_subscription_id = subscription.id

    db.commit()
    db.refresh(subscription)

    return subscription



def expiring_subscriptions(db: Session):
    today = date.today()

    expired_ids = select(Subscription.id).where(
        Subscription.end_date <= today,
        Subscription.status == "active",
    )

    expired_subscriptions = db.query(User, Subscription).join(
        Subscription,
        User.current_subscription_id == Subscription.id,
    ).filter(
        Subscription.id.in_(expired_ids)
    ).all()

    db.query(User).filter(
        User.current_subscription_id.in_(expired_ids)
    ).update(
        {User.current_subscription_id: None},
        synchronize_session=False,
    )

    db.query(Subscription).filter(
        Subscription.id.in_(expired_ids)
    ).update(
        {Subscription.status: "expired"},
        synchronize_session=False,
    )

    db.commit()

    return expired_subscriptions



def get_users_to_remind(db: Session):
    reminder_date = date.today() + timedelta(days=3)

    return (
        db.query(User)
        .join(Subscription, User.current_subscription_id == Subscription.id)
        .filter(
            Subscription.status == "active",
            Subscription.end_date == reminder_date,
        )
        .all()
    )
