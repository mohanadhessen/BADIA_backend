from sqlalchemy import Column, Integer, ForeignKey, Numeric, Enum, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.base import Base



class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    plan_id = Column(Integer, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    billing_cycle = Column(
        Enum("monthly", "yearly", name="billing_cycle"),
        nullable=False,
        index=True
    )
    status = Column(
    Enum("paid", "rejected", "canceled", name="payment_status"),
    nullable=False,
    index=True
)

    start_date = Column(TIMESTAMP, nullable=False)
    end_date = Column(TIMESTAMP, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", primaryjoin="Payment.user_id == User.id", foreign_keys=[user_id], back_populates="payments")
    plan = relationship("Plan", primaryjoin="Payment.plan_id == Plan.id", foreign_keys=[plan_id], back_populates="payments")