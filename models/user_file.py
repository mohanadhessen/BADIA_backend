from sqlalchemy import (  Column, Integer, String, TIMESTAMP, ForeignKey, func
)
from sqlalchemy.orm import relationship
from database.base import Base


class user_file(Base):
    __tablename__ = "user_files"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False, index=True)
    file_id = Column(String(36), unique=True, nullable=False, index=True)
    file_key = Column(String(512), nullable=False)        # ← was 36
    filename = Column(String(255), nullable=False)        # ← was 36
    content_type = Column(String(100), nullable=False)    # ← was 36
    size = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    request = relationship("Request", back_populates="files")