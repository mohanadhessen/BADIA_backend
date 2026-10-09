from sqlalchemy import Column, Integer, ForeignKey, Enum, TIMESTAMP, Date, func
from sqlalchemy.orm import relationship
from database.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,  index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, unique=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum("active", "expired", "canceled", name="subscription_status"), nullable=False, default="active", index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    user = relationship("User", back_populates="subscriptions") 
    plan = relationship("Plan", back_populates="subscriptions") 
    payment = relationship("Payment")