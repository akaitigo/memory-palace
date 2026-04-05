"""Room schemas."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_MAX_DESCRIPTION_LENGTH = 100_000
_MAX_LAYOUT_DATA_LENGTH = 100_000


def _validate_layout_data_size(v: dict[str, Any] | None) -> dict[str, Any] | None:
    """Reject layout_data payloads that exceed the size limit when serialized."""
    if v is not None and len(json.dumps(v)) > _MAX_LAYOUT_DATA_LENGTH:
        msg = f"layout_data JSON must not exceed {_MAX_LAYOUT_DATA_LENGTH} characters"
        raise ValueError(msg)
    return v


class RoomCreate(BaseModel):
    """Schema for creating a new room."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Room name (1-100 characters)",
    )
    description: Annotated[
        str | None,
        Field(
            default=None, max_length=_MAX_DESCRIPTION_LENGTH, description="Room description (max 100 000 characters)"
        ),
    ]
    layout_data: dict[str, Any] | None = Field(
        default=None,
        description="3D layout data (JSON, max 100 000 characters when serialized)",
    )

    @field_validator("layout_data")
    @classmethod
    def check_layout_data_size(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_layout_data_size(v)


class RoomUpdate(BaseModel):
    """Schema for updating a room."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Room name (1-100 characters)",
    )
    description: Annotated[
        str | None,
        Field(
            default=None, max_length=_MAX_DESCRIPTION_LENGTH, description="Room description (max 100 000 characters)"
        ),
    ]
    layout_data: dict[str, Any] | None = Field(
        default=None,
        description="3D layout data (JSON, max 100 000 characters when serialized)",
    )

    @field_validator("layout_data")
    @classmethod
    def check_layout_data_size(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_layout_data_size(v)


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
