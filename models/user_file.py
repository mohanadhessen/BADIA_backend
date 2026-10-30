from sqlalchemy import   Integer, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from database.base import Base
from typing import Optional
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .request import Request


class UserFile(Base):
    __tablename__ = "user_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("requests.id"), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(String(32),default=lambda: str(uuid.uuid7().hex), unique=True, nullable=False)
    file_key: Mapped[str] = mapped_column(String(512), nullable=False)        
    filename: Mapped[str] = mapped_column(String(255), nullable=False)        
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)   
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())
    request: Mapped["Request"] = relationship("Request", back_populates="files")
