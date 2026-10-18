"""Database connection and engine initialization with SQLAlchemy 2."""

import logging
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

connect_args = {"connect_timeout": 3} if "postgresql" in settings.database_url else {}

# SQLAlchemy 2.0 engine using psycopg 3 driver
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Test connections before checkout to prevent stale disconnects
    echo=False,
    connect_args=connect_args,
)

# Session factory producing isolated unit-of-work sessions
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""

    pass


def get_db() -> Generator[Session, Any, None]:
    """FastAPI dependency yielding a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(db: Session) -> bool:
    """Perform a live round-trip query against the database engine.

    Returns True if database responds to `SELECT 1`, False otherwise.
    """
    try:
        result = db.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception as exc:
        logger.error("Database healthcheck failed: %s", exc)
        return False
