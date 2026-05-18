from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Enum, Text, ForeignKey, func, text
from sqlalchemy.orm import relationship
from database.base import Base

class UserSchema(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    google_id = Column(String(255), unique=True, index=True)
    avatar_url = Column(Text)

    auth_provider = Column(Enum("local", "google", name="auth_provider"), nullable=False, server_default="local")
    is_email_verified = Column(Boolean, nullable=False, server_default="0")

    current_plan_id = Column(Integer, ForeignKey("plans.id"))
    subscription_end_date = Column(TIMESTAMP)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    role = Column(Enum("user", "admin", name="user_roles"), nullable=False, server_default="user")
    phone = Column(String(20))
    is_active = Column(Boolean, nullable=False, server_default=text("1"))

    reviews = relationship("Review", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    current_plan = relationship("Plan", back_populates="users")