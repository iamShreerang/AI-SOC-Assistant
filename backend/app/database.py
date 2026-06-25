"""Database connection and session management for Supabase PostgreSQL."""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.utils.config import settings
from app.models.database import Base

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Configure connection pool event listeners
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Execute on database connection."""
    logger.debug("Database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Execute when connection is retrieved from pool."""
    logger.debug("Connection checked out from pool")

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def create_tables():
    """Create all database tables.
    
    This should only be used in development.
    In production, use Alembic migrations.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


def drop_tables():
    """Drop all database tables.
    
    WARNING: This will delete all data!
    Only use in development/testing.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.
    
    Yields a SQLAlchemy session and ensures it's closed after use.
    
    Usage in FastAPI routes:
        @router.get("/")
        async def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    """Check if database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection check successful")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
