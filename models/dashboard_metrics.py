from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, func, JSON
from database.base import Base

class DashboardMetrics(Base):
    __tablename__ = "dashboard_metrics"

    id = Column(Integer, primary_key=True, default=1) 

    # users
    total_users = Column(Integer, nullable=False, server_default="0")
    active_users = Column(Integer, nullable=False, server_default="0")
    inactive_users = Column(Integer, nullable=False, server_default="0")
    verified_users = Column(Integer, nullable=False, server_default="0")
    unverified_users = Column(Integer, nullable=False, server_default="0")
    
    plans_distribution = Column(JSON, nullable=True)

    # payments
    total_payments = Column(Integer, nullable=False, server_default="0")
    paid_payments = Column(Integer, nullable=False, server_default="0")
    rejected_payments = Column(Integer, nullable=False, server_default="0")
    canceled_payments = Column(Integer, nullable=False, server_default="0")
    monthly_payments = Column(Integer, nullable=False, server_default="0")
    yearly_payments = Column(Integer, nullable=False, server_default="0")
    total_revenue = Column(Numeric(12, 2), nullable=False, server_default="0")

    # reviews
    total_reviews = Column(Integer, nullable=False, server_default="0")
    published_reviews = Column(Integer, nullable=False, server_default="0")
    pending_reviews = Column(Integer, nullable=False, server_default="0")

    # requests
    total_requests = Column(Integer, nullable=False, server_default="0")
    pending_requests = Column(Integer, nullable=False, server_default="0")
    approved_requests = Column(Integer, nullable=False, server_default="0")
    rejected_requests = Column(Integer, nullable=False, server_default="0")

    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())