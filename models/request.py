from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    Enum,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import relationship

from database.base import Base

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    request_id = Column(String(36), unique=True, nullable=False, index=True)

    service_type = Column(
        Enum(
            "operational_partnership",
            "feasibility_study",
            name="service_type"
        ),
        nullable=False,
        index=True
    )
    status = Column(
        Enum(
            "pending",
            "approved",
            "rejected",
            name="request_status"
        ),
        nullable=False,
        server_default="pending",
        index=True
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = relationship("User", back_populates="requests")
    files = relationship(
        "UserFile",
        back_populates="request",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "service_type", name="uq_user_service_type"),
    )