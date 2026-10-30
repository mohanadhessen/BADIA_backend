from sqlalchemy import  Integer, String, Boolean, TIMESTAMP, Enum, Text, ForeignKey, func, text
from sqlalchemy.orm import relationship , mapped_column , Mapped
from database.base import Base
from typing import Optional
from datetime import datetime
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .review import Review
    from .request import Request
    from .payment import Payment
    from .subscription import Subscription

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hash_id: Mapped[str] = mapped_column(String(32),default=lambda: str(uuid.uuid7().hex), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    auth_provider: Mapped[str] = mapped_column(Enum("local", "google", name="auth_provider"), nullable=False, server_default="local")
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", index=True)

    current_subscription_id: Mapped[Optional[int]] = mapped_column(Integer,ForeignKey("subscriptions.id",ondelete="SET NULL",use_alter=True,name="fk_users_current_subscription",),nullable=True,unique=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    role: Mapped[str] = mapped_column(Enum("user", "admin", name="user_roles"), nullable=False, server_default="user", index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"), index=True)

    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user")
    requests: Mapped[list["Request"]] = relationship("Request", back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="user")

    # full history
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription",back_populates="user",foreign_keys="Subscription.user_id",)
    # the current one
    current_subscription: Mapped[Optional["Subscription"]] = relationship("Subscription",foreign_keys=[current_subscription_id],post_update=True)
