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


class MemoryItemSM2Response(BaseModel):
    """SM-2 parameters of a memory item after review update."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ease_factor: float
    interval: int
    repetitions: int
    last_reviewed_at: datetime | None


class RoomStatsResponse(BaseModel):
    """Schema for room review statistics."""

    total_items: int = Field(..., description="Total memory items in the room")
    reviewed_items: int = Field(..., description="Items reviewed at least once")
    mastered_items: int = Field(..., description="Items with interval >= 21 days")
    learning_items: int = Field(..., description="Items being learned (interval < 21)")
    new_items: int = Field(..., description="Items never reviewed")
    average_ease_factor: float | None = Field(None, description="Average ease factor")
    total_reviews: int = Field(..., description="Total review records")
    average_quality: float | None = Field(None, description="Average quality score")
    reviews_today: int = Field(..., description="Reviews completed today")


class DailyStatsEntry(BaseModel):
    """A single day's review statistics."""

    date: str = Field(..., description="Date string (YYYY-MM-DD)")
    review_count: int = Field(..., description="Number of reviews on this day")
    average_quality: float | None = Field(None, description="Average quality score for the day")
    correct_rate: float | None = Field(None, description="Percentage of reviews with quality >= 3")


class DailyStatsResponse(BaseModel):
    """Daily review statistics for chart rendering."""

    entries: list[DailyStatsEntry] = Field(default_factory=list, description="Daily stats entries")


class ForgettingCurvePoint(BaseModel):
    """A point on the forgetting curve."""

    days_since_review: float = Field(..., description="Days since last review")
    retention: float = Field(..., description="Predicted retention probability (0-1)")


class ForgettingCurveItem(BaseModel):
    """Forgetting curve data for a single memory item."""

    item_id: uuid.UUID = Field(..., description="Memory item ID")
    content: str = Field(..., description="Memory item content (truncated)")
    stability: float = Field(..., description="Stability (interval * ease_factor)")
    curve: list[ForgettingCurvePoint] = Field(default_factory=list, description="Forgetting curve points")


class ForgettingCurveResponse(BaseModel):
    """Forgetting curve data for a room's items."""

    items: list[ForgettingCurveItem] = Field(default_factory=list, description="Per-item forgetting curves")
