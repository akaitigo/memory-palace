"""JWT authentication and password hashing utilities."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_palace.database import get_db
from memory_palace.models.user import User

# ---------------------------------------------------------------------------
# Password hashing (using bcrypt directly for Python 3.12+ compatibility)
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT token management
# ---------------------------------------------------------------------------
_ACCESS_TOKEN_EXPIRE_MINUTES = 60
_ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    """Read JWT_SECRET from environment variables.

    Returns:
        The JWT secret key.

    Raises:
        RuntimeError: If JWT_SECRET is not set or is empty.
    """
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        msg = "JWT_SECRET environment variable is not set"
        raise RuntimeError(msg)
    return secret


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a JWT access token for a user.

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        An encoded JWT string.
    """
    expire = datetime.now(tz=UTC) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(tz=UTC),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The user UUID extracted from the token.

    Raises:
        HTTPException: 401 if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[_ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return uuid.UUID(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from None
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None


# ---------------------------------------------------------------------------
# FastAPI dependency: get current user from Authorization header
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """FastAPI dependency that extracts and validates the current user from a JWT.

    Args:
        credentials: The HTTP Bearer token from the Authorization header.
        db: Database session.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException: 401 if the token is invalid or the user does not exist.
    """
    user_id = decode_access_token(credentials.credentials)
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
