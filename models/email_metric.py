from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import mapped_column, Mapped
from database.base import Base
from datetime import datetime

class EmailMetric(Base):
    __tablename__ = "email_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now())
