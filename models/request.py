from sqlalchemy import Integer, String, TIMESTAMP, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from datetime import datetime
from typing import TYPE_CHECKING
from database.base import Base
import uuid

if TYPE_CHECKING:
    from .user import User
    from .user_file import UserFile

class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(32),default=lambda: str(uuid.uuid7().hex), unique=True, nullable=False)

    service_type: Mapped[str] = mapped_column(Enum("partnership", "feasibility_study", name="service_type"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(Enum("pending", "approved", "rejected", name="request_status"), nullable=False, server_default="pending", index=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="requests")
    files: Mapped[list["UserFile"]] = relationship("UserFile", back_populates="request", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "service_type", name="uq_user_service_type"),
    )
