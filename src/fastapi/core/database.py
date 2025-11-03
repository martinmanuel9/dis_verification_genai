"""
Database connection and session management.

This module handles:
- Database engine creation with connection pooling
- Session factory setup
- Connection health checks
- Retry logic for database initialization
"""

import time
from typing import Generator, Dict, Any
from chromadb import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging 

from core.config import get_settings

logger = logging.getLogger('CORE_DATABASE')

# Get settings
settings = get_settings()

# Database engine configuration
engine_config = {
    'poolclass': QueuePool,
    'pool_size': settings.db_pool_size,
    'max_overflow': settings.db_max_overflow,
    'pool_timeout': settings.db_pool_timeout,
    'pool_recycle': settings.db_pool_recycle,
    'pool_pre_ping': settings.db_pool_pre_ping,
    'echo': settings.db_echo,
}

# Initialize engine with retry logic
DATABASE_URL = settings.get_database_url()
logger.info(f"Initializing database connection to: postgresql://{settings.db_username}:***@{settings.get_database_host()}:{settings.db_port}/{settings.get_database_name()}")

# Optimized retry logic with exponential backoff
retry_delays = [1, 2, 3, 5, 8]
engine = None

for i, delay in enumerate(retry_delays):
    try:
        engine = create_engine(DATABASE_URL, **engine_config)
        # Test connection with health check
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Database connection established successfully on attempt {i+1}")
        break
    except OperationalError as e:
        logger.error(f"✗ Database not ready (attempt {i+1}/{len(retry_delays)}): {e}")
        if i < len(retry_delays) - 1:
            logger.info(f"  Retrying in {delay} seconds...")
            time.sleep(delay)
        else:
            raise Exception(f"Could not connect to the database after {len(retry_delays)} attempts") from e

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_health() -> Dict[str, Any]:
    """
    Check database connection health and return status.

    Returns:
        dict: Health status with connection pool information

    Example:
        {
            "status": "healthy",
            "connection_pool": "Pool size: 5  Connections in pool: 0 ..."
        }
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            return {
                "status": "healthy",
                "connection_pool": engine.pool.status(),
                "database": settings.get_database_name(),
                "host": settings.get_database_host(),
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": settings.get_database_name(),
            "host": settings.get_database_host(),
        }


def init_db() -> None:
    """
    Initialize database tables.

    This function should be called during application startup to ensure
    all tables are created. Note: In production, use Alembic migrations instead.

    Important: This import triggers all model registrations through models/__init__.py
    """
    from models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
