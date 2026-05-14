import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.logging_config import logger
from app.config.settings import Settings
from app.db.models import Base

from dotenv import load_dotenv


load_dotenv()

# Check if the code is being run in a test environment
TESTING = "pytest" in sys.modules

if not TESTING:
    DATABASE_URL = Settings().database_url

    # Configure connection args based on database type
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    # Si es PostgreSQL, usar el dialecto psycopg3 (psycopg versión 3)
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    Base.metadata.create_all(engine)
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
