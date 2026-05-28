from sqlalchemy import Column, Integer, String, TIMESTAMP, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base


class UserFile(Base):
    __tablename__ = "user_files"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    file_id = Column(String, unique=True, index=True)
    file_key = Column(String, unique=True)

    filename = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)

    service_type = Column(
        Enum("operational_partnership", "feasibility_study", name="service_type"),
        nullable=False,
        index=True
    )

    status = Column(
        Enum("pending", "approved", "rejected", name="request_status"),
        nullable=False,
        server_default="pending",
        index=True
    )
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="files")