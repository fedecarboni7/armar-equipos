import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.logging_config import logger
from app.config.settings import Settings

from dotenv import load_dotenv


load_dotenv()

# Check if the code is being run in a test environment
TESTING = "pytest" in sys.modules


def create_sync_engine(database_url: str):
    # Si es PostgreSQL, usar el dialecto psycopg3 (psycopg versión 3)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return create_engine(database_url)


if not TESTING:
    DATABASE_URL = Settings().database_url

    engine = create_sync_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    logger.info(
        "Running in test mode - database connection will be handled by pytest fixtures"
    )
    # Create a dummy engine and session for import purposes
    engine = None
    SessionLocal = None


def get_db():
    if TESTING:
        # This will be overridden by the test fixtures
        raise RuntimeError(
            "get_db() called in test mode. This should be overridden by test fixtures."
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
