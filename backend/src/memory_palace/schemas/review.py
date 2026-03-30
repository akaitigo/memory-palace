"""Review schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewRecordCreate(BaseModel):
    """Schema for recording a review result."""

    memory_item_id: uuid.UUID = Field(
        ...,
        description="ID of the memory item being reviewed",
    )
    quality: int = Field(
        ...,
        ge=0,
        le=5,
        description="Self-assessment quality (0=blackout, 5=perfect recall)",
    )
    response_time_ms: int = Field(
        ...,
        gt=0,
        le=300000,
        description="Response time in milliseconds (max 300,000 = 5 minutes)",
    )


class ReviewRecordResponse(BaseModel):
    """Schema for review record response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    memory_item_id: uuid.UUID
    quality: int
    response_time_ms: int
    reviewed_at: datetime


class ReviewSessionResponse(BaseModel):
    """Schema for review session response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    total_items: int
    completed_items: int
    started_at: datetime
    completed_at: datetime | None
    review_records: list[ReviewRecordResponse] = Field(default_factory=list)
