from sqlalchemy import Column, Integer, ForeignKey, Numeric, Enum, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.base import Base



class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id",ondelete="RESTRICT"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    billing_cycle = Column(
        Enum("monthly", "yearly", name="billing_cycle"),
        nullable=False
    )
    status = Column(
    Enum("paid", "rejected", "canceled", name="payment_status"),
    nullable=False
)

    start_date = Column(TIMESTAMP, nullable=False)
    end_date = Column(TIMESTAMP, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="payments")
    plan = relationship("Plan", back_populates="payments")