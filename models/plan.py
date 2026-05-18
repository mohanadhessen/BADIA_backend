from sqlalchemy import Column, Integer, String, Boolean, Numeric
from sqlalchemy.orm import relationship
from database.base import Base

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2), nullable=False)

    max_transactions = Column(Integer)
    max_users = Column(Integer)

    has_inventory = Column(Boolean, default=False)
    has_payroll = Column(Boolean, default=False)

    users = relationship("User", back_populates="current_plan")
    payments = relationship("Payment", back_populates="plan")