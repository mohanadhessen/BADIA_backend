from sqlalchemy import Integer, String, Numeric, JSON, TIMESTAMP, func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from database.base import Base
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .payment import Payment
    from .subscription import Subscription



class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price_monthly: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_yearly: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    plan_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    

    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="plan")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="plan")




