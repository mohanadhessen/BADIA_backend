from sqlalchemy import Integer, Text, ForeignKey, Boolean, TIMESTAMP, func, text , String
from sqlalchemy.orm import relationship, mapped_column, Mapped
from database.base import Base
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .user import User

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    review_id : Mapped[str] = mapped_column(String(32),default=lambda: str(uuid.uuid7().hex), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)

    is_published: Mapped[bool | None] = mapped_column(Boolean, server_default=text("0"), index=True)

    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="reviews")
