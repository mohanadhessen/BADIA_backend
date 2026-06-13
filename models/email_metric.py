from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from database.base import Base

class EmailMetric(Base):
    __tablename__ = "email_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    sent_at = Column(TIMESTAMP, server_default=func.now())
