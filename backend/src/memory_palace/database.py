"""Database connection and session management."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm import Session


def get_database_url() -> str:
    """Get database URL from environment variable."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        msg = "DATABASE_URL environment variable is not set"
        raise ValueError(msg)
    return url


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory.

    Args:
        database_url: Optional database URL. If not provided, reads from DATABASE_URL env var.

    Returns:
        A configured sessionmaker instance.
    """
    url = database_url or get_database_url()
    engine = create_engine(url, echo=False)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Yields:
        A SQLAlchemy session that is automatically closed after use.
    """
    session_factory = create_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
