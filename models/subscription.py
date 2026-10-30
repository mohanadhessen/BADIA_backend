from sqlalchemy import Integer, ForeignKey, Enum, TIMESTAMP, Date, func , String
from sqlalchemy.orm import relationship, mapped_column, Mapped
from database.base import Base
from datetime import date, datetime
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .plan import Plan
    from .payment import Payment
    from .user import User

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[str] = mapped_column(String(32),default=lambda: str(uuid.uuid7().hex), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,  index=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_id: Mapped[int] = mapped_column(Integer, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Enum("active", "expired", "canceled", name="subscription_status"), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), index=True)

    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
    payment: Mapped["Payment"] = relationship("Payment")
    
    user: Mapped["User"] = relationship("User", back_populates="subscriptions", foreign_keys=[user_id])
