from sqlalchemy import Column, Integer, ForeignKey, Numeric, Enum, TIMESTAMP, func , String
from sqlalchemy.orm import relationship
from database.base import Base
import uuid


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_hash = Column(String(64), nullable=False, unique=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_id = Column(ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    billing_cycle = Column(Enum("monthly", "yearly", name="billing_cycle"),nullable=False,index=True)
    status = Column(
    Enum("pending", "paid", "rejected", "canceled", name="payment_status" ),nullable=False,index=True , default="pending")

    source = Column(Enum("manual", "paymentgateway", name="payment_source"), nullable=False, index=True)
    
    start_date = Column(TIMESTAMP, nullable=True)
    end_date = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="payments") 
    plan = relationship("Plan", back_populates="payments")