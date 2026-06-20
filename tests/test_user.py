from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
import models  # import models to register them on Base.metadata
from crud.user import create_new_user

def test_create_new_user_default_company_name():
    # Set up in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create the tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        # Create a user with no company_name provided (or None)
        user = create_new_user(
            db=db,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="hashedpassword",
            auth_provider="local"
        )
        
        # Verify the user has an empty string for company_name instead of "Not Provided"
        assert user.company_name == ""
        
        # Also test when company_name is explicitly passed as None
        user2 = create_new_user(
            db=db,
            email="test2@example.com",
            first_name="Test2",
            last_name="User2",
            company_name=None,
            password="hashedpassword",
            auth_provider="local"
        )
        assert user2.company_name == ""
        
        # Test when company_name is explicitly passed
        user3 = create_new_user(
            db=db,
            email="test3@example.com",
            first_name="Test3",
            last_name="User3",
            company_name="My Company",
            password="hashedpassword",
            auth_provider="local"
        )
        assert user3.company_name == "My Company"
        
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
