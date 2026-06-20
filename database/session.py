from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

connect_args = {}
if settings.ENV == "production":
    connect_args["ssl"] = {"ssl_mode": "VERIFY_IDENTITY"}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
    pool_timeout=15,
    pool_recycle=300,  
    connect_args=connect_args
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

        