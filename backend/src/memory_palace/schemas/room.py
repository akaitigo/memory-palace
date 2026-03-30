"""Room schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    """Schema for creating a new room."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Room name (1-100 characters)",
    )
    description: str | None = Field(
        default=None,
        description="Room description",
    )
    layout_data: dict[str, Any] | None = Field(
        default=None,
        description="3D layout data (JSON)",
    )
    owner_id: uuid.UUID | None = Field(
        default=None,
        description="Owner user ID. If omitted a new UUID is generated (MVP: no auth).",
    )


class RoomUpdate(BaseModel):
    """Schema for updating a room."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Room name (1-100 characters)",
    )
    description: str | None = Field(
        default=None,
        description="Room description",
    )
    layout_data: dict[str, Any] | None = Field(
        default=None,
        description="3D layout data (JSON)",
    )


class RoomResponse(BaseModel):
    """Schema for room response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID | None
    name: str
    description: str | None
    layout_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
