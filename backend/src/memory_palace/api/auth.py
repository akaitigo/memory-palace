"""Authentication API endpoints: register and login."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_palace.auth import create_access_token, get_current_user, hash_password, verify_password
from memory_palace.database import get_db
from memory_palace.models.user import User
from memory_palace.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Register a new user account.

    Returns a JWT access token on success. Email format is validated by the
    ``EmailStr`` field on :class:`RegisterRequest`, which returns 422 for
    malformed addresses before this handler runs.

    Raises:
        HTTPException: 409 if username or email already exists.
    """
    # Check for existing username
    existing_user = db.execute(select(User).where(User.username == body.username)).scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # Check for existing email
    existing_email = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Authenticate a user and return a JWT access token.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = db.execute(select(User).where(User.username == body.username)).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Get the current authenticated user's information."""
    return current_user
