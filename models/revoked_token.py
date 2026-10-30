from sqlalchemy import String, TIMESTAMP, func, Integer
from sqlalchemy.orm import mapped_column, Mapped
from database.base import Base
from datetime import datetime

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now())
