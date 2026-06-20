import logging
from database.base import Base
from database.session import engine
# Import models to ensure they are registered with Base.metadata before creation
import models

# Set up logging to output to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_tables():
    logger.info("Initializing database tables creation...")
    try:
        # Create all tables defined by classes subclassing Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error("An error occurred while creating database tables.", exc_info=True)
        raise

if __name__ == "__main__":
    create_tables()
