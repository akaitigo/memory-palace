"""MemoryItem schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PositionSchema(BaseModel):
    """3D position coordinates."""

    x: float = Field(
        ...,
        ge=-1000.0,
        le=1000.0,
        description="X coordinate (-1000.0 to 1000.0)",
    )
    y: float = Field(
        ...,
        ge=-1000.0,
        le=1000.0,
        description="Y coordinate (-1000.0 to 1000.0)",
    )
    z: float = Field(
        ...,
        ge=-1000.0,
        le=1000.0,
        description="Z coordinate (-1000.0 to 1000.0)",
    )


class MemoryItemCreate(BaseModel):
    """Schema for creating a memory item."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Memory target text (1-10,000 characters)",
    )
    image_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Optional image URL",
    )
    position: PositionSchema = Field(
        default_factory=lambda: PositionSchema(x=0.0, y=0.0, z=0.0),
        description="3D position in the room",
    )


class MemoryItemUpdate(BaseModel):
    """Schema for updating a memory item."""

    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=10000,
        description="Memory target text (1-10,000 characters)",
    )
    image_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Optional image URL",
    )
    position: PositionSchema | None = Field(
        default=None,
        description="3D position in the room",
    )


class MemoryItemResponse(BaseModel):
    """Schema for memory item response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    content: str
    image_url: str | None
    position_x: float
    position_y: float
    position_z: float
    ease_factor: float
    interval: int
    repetitions: int
    last_reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
