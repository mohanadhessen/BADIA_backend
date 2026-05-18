from sqlalchemy import create_engine, Integer, String, Column, Boolean, TIMESTAMP, func, Enum, Text, ForeignKey, Numeric, text 
from sqlalchemy.orm import declarative_base, sessionmaker , relationship
from decimal import Decimal
from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()




class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2), nullable=False)
    max_transactions = Column(Integer)
    max_users = Column(Integer)
    has_inventory = Column(Boolean, default=False)
    has_payroll = Column(Boolean, default=False)
    users = relationship("User", back_populates="current_plan")
    payments = relationship("Payment", back_populates="plan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), server_default="KWD")
    payment_method = Column(String(50)) 
    
    status = Column(Enum("pending", "success", "failed", "refunded", name="payment_status"), server_default="pending")
    transaction_id = Column(String(100), unique=True)
    gateway_ref = Column(String(255)) 
    
    billing_cycle = Column(Enum("monthly", "yearly", name="billing_cycle"), nullable=False)
    start_date = Column(TIMESTAMP, nullable=False)
    end_date = Column(TIMESTAMP, nullable=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    user = relationship("User", back_populates="payments")
    plan = relationship("Plan", back_populates="payments")




class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Rating from 1 to 5
    stars = Column(Integer, nullable=False) 
    
    # The user who wrote the review
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    review_text = Column(Text, nullable=False)
    
    # Visibility control (allows admin to approve reviews before they show on the site)
    is_published = Column(Boolean, server_default=text("0")) 

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Optional: Add a relationship to easily access user data from a review
    user = relationship("User", back_populates="reviews")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()