"""Database connection and session management."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy import Engine
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


# ---------------------------------------------------------------------------
# Singleton engine & session factory
# ---------------------------------------------------------------------------
_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _init_engine() -> None:
    """Initialise the module-level engine and session factory (once)."""
    global _engine, _SessionLocal  # noqa: PLW0603
    if _engine is None:
        url = get_database_url()
        _engine = create_engine(url, echo=False, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_engine() -> Engine:
    """Return the shared engine, initialising on first call."""
    _init_engine()
    if _engine is None:
        msg = "Database engine failed to initialise"
        raise RuntimeError(msg)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the shared session factory, initialising on first call."""
    _init_engine()
    if _SessionLocal is None:
        msg = "Session factory failed to initialise"
        raise RuntimeError(msg)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    The engine and session factory are created once and reused across requests
    so that the connection pool is shared.

    Yields:
        A SQLAlchemy session that is automatically closed after use.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def reset_engine() -> None:
    """Dispose and reset the shared engine (for testing only).

    After calling this, the next ``get_db()`` / ``get_engine()`` call will
    create a fresh engine from the current ``DATABASE_URL``.
    """
    global _engine, _SessionLocal  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
