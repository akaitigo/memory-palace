"""Shared test fixtures."""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from memory_palace.auth import create_access_token, hash_password
from memory_palace.database import Base, get_db
from memory_palace.main import app
from memory_palace.models.user import User

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm import Session

# Ensure JWT_SECRET is set for tests
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")

# Shared engine for all tests — StaticPool ensures the same in-memory DB is reused.
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(bind=_engine)


@pytest.fixture(autouse=True)
def _setup_db():
    """Create all tables before each test and drop after."""
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


def _override_get_db() -> Generator[Session, None, None]:
    session = _TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a raw DB session for direct model testing."""
    session = _TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user and return it."""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Return Authorization headers with a valid JWT for the test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
