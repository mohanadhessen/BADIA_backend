from sqlalchemy import Column, Integer, Text, ForeignKey, Boolean, TIMESTAMP, func, text
from sqlalchemy.orm import relationship
from database.base import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stars = Column(Integer, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_text = Column(Text, nullable=False)

    is_published = Column(Boolean, server_default=text("0"))

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="reviews")