"""Review API endpoints: review queue, review recording, and room statistics."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_palace.auth import get_current_user
from memory_palace.database import get_db
from memory_palace.models.room import Room
from memory_palace.models.user import User
from memory_palace.schemas.memory_item import MemoryItemResponse
from memory_palace.schemas.review import (
    DailyStatsResponse,
    ForgettingCurveResponse,
    ReviewRecordCreate,
    ReviewRecordResponse,
    RoomStatsResponse,
)
from memory_palace.services.review import (
    get_daily_stats,
    get_forgetting_curves,
    get_review_queue,
    get_room_stats,
    record_review,
)

router = APIRouter(prefix="/api/rooms", tags=["reviews"])


def _get_room_or_404(db: Session, room_id: uuid.UUID, owner_id: uuid.UUID) -> Room:
    """Retrieve a room by ID, ensuring the owner matches.

    Args:
        db: Database session.
        room_id: Room UUID.
        owner_id: Expected owner UUID for authorization.

    Returns:
        The Room object.

    Raises:
        HTTPException: 404 if the room does not exist or does not belong to the owner.
    """
    room = db.execute(select(Room).where(Room.id == room_id, Room.owner_id == owner_id)).scalar_one_or_none()
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room {room_id} not found",
        )
    return room


@router.get(
    "/{room_id}/review-queue",
    response_model=list[MemoryItemResponse],
    summary="Get review queue",
    description="Returns memory items due for review, sorted by urgency.",
)
def get_review_queue_endpoint(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list:
    """Get memory items due for review in a room."""
    _get_room_or_404(db, room_id, current_user.id)
    return get_review_queue(db, room_id)


@router.post(
    "/{room_id}/review",
    response_model=ReviewRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a review result",
    description="Records a review result and updates SM-2 parameters on the memory item.",
)
def post_review(
    room_id: uuid.UUID,
    body: ReviewRecordCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> object:
    """Record a review result for a memory item."""
    _get_room_or_404(db, room_id, current_user.id)
    return record_review(
        db=db,
        room_id=room_id,
        memory_item_id=body.memory_item_id,
        quality=body.quality,
        response_time_ms=body.response_time_ms,
    )


@router.get(
    "/{room_id}/stats",
    response_model=RoomStatsResponse,
    summary="Get room review statistics",
    description="Returns review statistics for a room including mastery levels and review counts.",
)
def get_stats(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get review statistics for a room."""
    _get_room_or_404(db, room_id, current_user.id)
    return get_room_stats(db, room_id)


@router.get(
    "/{room_id}/stats/daily",
    response_model=DailyStatsResponse,
    summary="Get daily review statistics",
    description="Returns daily review counts and accuracy rates for chart rendering.",
)
def get_daily_stats_endpoint(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back (1-365)"),
) -> dict:
    """Get daily review statistics for a room."""
    _get_room_or_404(db, room_id, current_user.id)
    return get_daily_stats(db, room_id, days)


@router.get(
    "/{room_id}/stats/forgetting-curve",
    response_model=ForgettingCurveResponse,
    summary="Get forgetting curve data",
    description="Returns predicted forgetting curves for reviewed items using R(t) = e^(-t/S).",
)
def get_forgetting_curve_endpoint(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get forgetting curve data for a room's items."""
    _get_room_or_404(db, room_id, current_user.id)
    return get_forgetting_curves(db, room_id)
