from sqlalchemy import Column, String, TIMESTAMP, func, Integer
from database.base import Base

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(512), unique=True, index=True, nullable=False)
    revoked_at = Column(TIMESTAMP, server_default=func.now())
