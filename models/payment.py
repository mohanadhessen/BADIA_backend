from sqlalchemy import Integer, ForeignKey, Numeric, Enum, TIMESTAMP, func, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.base import Base
from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from decimal import Decimal


if TYPE_CHECKING:
    from .user import User
    from .plan import Plan


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_hash: Mapped[str] = mapped_column(String(32),default=lambda: str(uuid.uuid7().hex), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    billing_cycle: Mapped[str] = mapped_column(Enum("monthly", "yearly", name="billing_cycle"),nullable=False,index=True)
    status: Mapped[str] = mapped_column(
    Enum("pending", "paid", "failed", name="payment_status" ),nullable=False,index=True , default="pending")
    gateway_token: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    source: Mapped[str] = mapped_column(Enum("manual", "paymentgateway", name="payment_source"), nullable=False, index=True)
    

    created_at: Mapped[datetime ] = mapped_column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="payments")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="payments")
