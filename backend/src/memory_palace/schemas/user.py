"""User schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Username (1-100 characters)",
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


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
