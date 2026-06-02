from sqlalchemy import Column, Integer, String, Boolean, Numeric, JSON, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.base import Base



class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2), nullable=False)
    users = relationship("User", back_populates="current_plan")
    payments = relationship("Payment", back_populates="plan")
    plan_details = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())