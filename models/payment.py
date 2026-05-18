from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Enum, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), server_default="KWD")

    payment_method = Column(String(50))

    status = Column(Enum("pending", "success", "failed", "refunded", name="payment_status"), server_default="pending")

    transaction_id = Column(String(100), unique=True)
    gateway_ref = Column(String(255))

    billing_cycle = Column(Enum("monthly", "yearly", name="billing_cycle"), nullable=False)

    start_date = Column(TIMESTAMP, nullable=False)
    end_date = Column(TIMESTAMP, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="payments")
    plan = relationship("Plan", back_populates="payments")