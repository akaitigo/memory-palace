"""Authentication schemas for register and login."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Username (3-100 characters)",
    )
    email: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters)",
    )


class LoginRequest(BaseModel):
    """Schema for user login."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Username",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Password",
    )


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """Schema for user information response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
