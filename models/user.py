from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Enum, Text, ForeignKey, func, text
from sqlalchemy.orm import relationship
from database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)
    company_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    google_id = Column(String(255), unique=True, index=True)
    avatar_url = Column(Text)
    auth_provider = Column(Enum("local", "google", name="auth_provider"), nullable=False, server_default="local")
    is_email_verified = Column(Boolean, nullable=False, server_default="0", index=True)

    current_subscription_id = Column(
        Integer,
        ForeignKey(
            "subscriptions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_users_current_subscription",
        ),
        nullable=True,
        unique=True,
    )

    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    role = Column(Enum("user", "admin", name="user_roles"), nullable=False, server_default="user", index=True)
    phone = Column(String(20))
    is_active = Column(Boolean, nullable=False, server_default=text("1"), index=True)

    reviews = relationship("Review", back_populates="user")
    requests = relationship("Request", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user")

    # full history
    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        foreign_keys="Subscription.user_id",
    )
    # the current one
    current_subscription = relationship(
        "Subscription",
        foreign_keys=[current_subscription_id],
        post_update=True,
    )