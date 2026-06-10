from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(                                                                                                                                                                                                                                                  
        settings.database_url,                                                                                                                                                                                                                                               
        pool_pre_ping=True,                                                                                                                                                                                                                                                  
        pool_size=20,                                                                                                                                                                                                           
        max_overflow=20,                                                                                                                                                                                                      
        pool_timeout=15,                                                                                                                                                                                           
        connect_args={                                                                                                                                                                                                                                                       
            "ssl": {                                                                                                                                                                                                                                                         
                "ssl_mode": "VERIFY_IDENTITY"                                                                                                                                                                                                                                
            }                                                                                                                                                                                                                                                                
        }                                                                                                                                                                                                                                                                    
    )



SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        