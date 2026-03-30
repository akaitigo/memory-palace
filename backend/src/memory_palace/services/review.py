"""Review service: queue generation, review recording, and statistics."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from memory_palace.models.memory_item import MemoryItem
from memory_palace.models.review_record import ReviewRecord
from memory_palace.models.review_session import ReviewSession
from memory_palace.services.scheduling import SchedulingStrategy, SM2Strategy

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

# Items with interval >= this threshold are considered "mastered"
_MASTERY_INTERVAL_DAYS = 21


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (assume UTC if naive).

    SQLite does not store timezone info, so datetimes from SQLite
    may be naive. This helper normalizes them to UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _get_scheduling_strategy() -> SchedulingStrategy:
    """Return the current scheduling strategy.

    Currently SM-2; will be swapped to ML-based strategy in Phase 2.
    """
    return SM2Strategy()


def get_review_queue(db: Session, room_id: uuid.UUID) -> list[MemoryItem]:
    """Get memory items due for review in a room.

    An item is due for review if:
    - It has never been reviewed (last_reviewed_at is NULL), OR
    - Its next review date (last_reviewed_at + interval days) is today or earlier.

    Items are sorted by urgency: never-reviewed first, then by due date ascending.

    Args:
        db: Database session.
        room_id: Room UUID to get queue for.

    Returns:
        List of MemoryItem objects due for review.
    """
    now = datetime.now(tz=UTC)

    # Fetch all items in the room and filter in Python for SQLite compatibility
    all_items = list(
        db.execute(select(MemoryItem).where(MemoryItem.room_id == room_id).order_by(MemoryItem.created_at))
        .scalars()
        .all()
    )

    queue: list[MemoryItem] = []
    for item in all_items:
        if item.last_reviewed_at is None:
            queue.append(item)
        else:
            reviewed_at = _ensure_aware(item.last_reviewed_at)
            next_review_date = reviewed_at + timedelta(days=item.interval)
            if next_review_date <= now:
                queue.append(item)

    # Sort: never-reviewed first, then by due date
    def sort_key(item: MemoryItem) -> tuple[int, datetime]:
        if item.last_reviewed_at is None:
            return (0, _ensure_aware(item.created_at))
        reviewed_at = _ensure_aware(item.last_reviewed_at)
        return (1, reviewed_at + timedelta(days=item.interval))

    queue.sort(key=sort_key)
    return queue


def record_review(
    db: Session,
    room_id: uuid.UUID,
    memory_item_id: uuid.UUID,
    quality: int,
    response_time_ms: int,
    session_id: uuid.UUID | None = None,
) -> ReviewRecord:
    """Record a review result and update SM-2 parameters on the memory item.

    Args:
        db: Database session.
        room_id: Room UUID (used to verify item belongs to room).
        memory_item_id: ID of the memory item being reviewed.
        quality: Self-assessment score (0-5).
        response_time_ms: Time to respond in milliseconds.
        session_id: Optional review session ID. A new session is created if None.

    Returns:
        The created ReviewRecord.

    Raises:
        ValueError: If the memory item is not found in the specified room.
    """
    # Fetch the memory item
    item = db.execute(
        select(MemoryItem).where(
            MemoryItem.id == memory_item_id,
            MemoryItem.room_id == room_id,
        )
    ).scalar_one_or_none()

    if item is None:
        msg = f"MemoryItem {memory_item_id} not found in room {room_id}"
        raise ValueError(msg)

    # Create or fetch review session
    if session_id is None:
        session = ReviewSession(
            room_id=room_id,
            total_items=1,
            completed_items=1,
            completed_at=datetime.now(tz=UTC),
        )
        db.add(session)
        db.flush()
        session_id = session.id
    else:
        session = db.execute(select(ReviewSession).where(ReviewSession.id == session_id)).scalar_one_or_none()
        if session is not None:
            session.completed_items += 1
            if session.completed_items >= session.total_items:
                session.completed_at = datetime.now(tz=UTC)

    # Calculate new SM-2 parameters
    strategy = _get_scheduling_strategy()
    result = strategy.calculate(
        quality=quality,
        ease_factor=item.ease_factor,
        interval=item.interval,
        repetitions=item.repetitions,
    )

    # Update memory item with new SM-2 parameters
    item.ease_factor = result.ease_factor
    item.interval = result.interval
    item.repetitions = result.repetitions
    item.last_reviewed_at = datetime.now(tz=UTC)

    # Create review record
    review_record = ReviewRecord(
        session_id=session_id,
        memory_item_id=memory_item_id,
        quality=quality,
        response_time_ms=response_time_ms,
    )
    db.add(review_record)
    db.commit()
    db.refresh(review_record)

    return review_record


def get_room_stats(db: Session, room_id: uuid.UUID) -> dict:
    """Get review statistics for a room.

    Returns:
        Dictionary with:
        - total_items: Total number of memory items in the room.
        - reviewed_items: Number of items that have been reviewed at least once.
        - mastered_items: Items with interval >= 21 days (well-learned).
        - learning_items: Items with 0 < repetitions and interval < 21 days.
        - new_items: Items never reviewed.
        - average_ease_factor: Average ease factor across all items.
        - total_reviews: Total number of review records.
        - average_quality: Average quality score across all reviews.
        - reviews_today: Number of reviews completed today.
    """
    # Total items in room
    total_items = db.execute(select(func.count(MemoryItem.id)).where(MemoryItem.room_id == room_id)).scalar_one()

    # Items categorized by learning state
    items = list(db.execute(select(MemoryItem).where(MemoryItem.room_id == room_id)).scalars().all())

    new_items = sum(1 for i in items if i.last_reviewed_at is None)
    mastered_items = sum(1 for i in items if i.last_reviewed_at is not None and i.interval >= _MASTERY_INTERVAL_DAYS)
    learning_items = sum(1 for i in items if i.last_reviewed_at is not None and i.interval < _MASTERY_INTERVAL_DAYS)

    # Average ease factor
    avg_ease = db.execute(select(func.avg(MemoryItem.ease_factor)).where(MemoryItem.room_id == room_id)).scalar_one()

    # Review records via sessions
    session_ids_subquery = select(ReviewSession.id).where(ReviewSession.room_id == room_id)

    total_reviews = db.execute(
        select(func.count(ReviewRecord.id)).where(ReviewRecord.session_id.in_(session_ids_subquery))
    ).scalar_one()

    avg_quality = db.execute(
        select(func.avg(ReviewRecord.quality)).where(ReviewRecord.session_id.in_(session_ids_subquery))
    ).scalar_one()

    # Reviews today
    today_start = datetime.now(tz=UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    reviews_today = db.execute(
        select(func.count(ReviewRecord.id)).where(
            ReviewRecord.session_id.in_(session_ids_subquery),
            ReviewRecord.reviewed_at >= today_start,
        )
    ).scalar_one()

    return {
        "total_items": total_items,
        "reviewed_items": total_items - new_items,
        "mastered_items": mastered_items,
        "learning_items": learning_items,
        "new_items": new_items,
        "average_ease_factor": round(float(avg_ease), 2) if avg_ease is not None else None,
        "total_reviews": total_reviews,
        "average_quality": round(float(avg_quality), 2) if avg_quality is not None else None,
        "reviews_today": reviews_today,
    }


_MAX_DAILY_STATS_DAYS = 365
_DEFAULT_DAILY_STATS_DAYS = 30
_FORGETTING_CURVE_POINTS = 20
_MAX_FORGETTING_CURVE_ITEMS = 20
_CORRECT_QUALITY_THRESHOLD = 3
_CONTENT_PREVIEW_LENGTH = 50
_PERCENT_MULTIPLIER = 100
_MIN_CURVE_DAYS = 7


def get_daily_stats(db: Session, room_id: uuid.UUID, days: int = _DEFAULT_DAILY_STATS_DAYS) -> dict:
    """Get daily review statistics for chart rendering.

    Args:
        db: Database session.
        room_id: Room UUID.
        days: Number of days to look back (max 365).

    Returns:
        Dictionary with 'entries' list of daily stats.
    """
    days = min(days, _MAX_DAILY_STATS_DAYS)
    now = datetime.now(tz=UTC)
    start_date = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

    # Get all review records for this room in the date range
    session_ids_subquery = select(ReviewSession.id).where(ReviewSession.room_id == room_id)
    records = list(
        db.execute(
            select(ReviewRecord).where(
                ReviewRecord.session_id.in_(session_ids_subquery),
                ReviewRecord.reviewed_at >= start_date,
            )
        )
        .scalars()
        .all()
    )

    # Group by date
    daily_map: dict[str, list[int]] = {}
    for record in records:
        reviewed_at = _ensure_aware(record.reviewed_at)
        date_str = reviewed_at.strftime("%Y-%m-%d")
        if date_str not in daily_map:
            daily_map[date_str] = []
        daily_map[date_str].append(record.quality)

    # Build entries for each day in the range
    entries = []
    current = start_date
    while current <= now:
        date_str = current.strftime("%Y-%m-%d")
        qualities = daily_map.get(date_str, [])
        review_count = len(qualities)
        avg_q = round(sum(qualities) / len(qualities), 2) if qualities else None
        correct_count = sum(1 for q in qualities if q >= _CORRECT_QUALITY_THRESHOLD)
        correct_rate = round(correct_count / len(qualities) * _PERCENT_MULTIPLIER, 1) if qualities else None

        entries.append(
            {
                "date": date_str,
                "review_count": review_count,
                "average_quality": avg_q,
                "correct_rate": correct_rate,
            }
        )
        current += timedelta(days=1)

    return {"entries": entries}


def get_forgetting_curves(db: Session, room_id: uuid.UUID) -> dict:
    """Get forgetting curve data for items in a room.

    Uses the formula R(t) = e^(-t/S) where S = interval * ease_factor (stability).

    Args:
        db: Database session.
        room_id: Room UUID.

    Returns:
        Dictionary with 'items' list of forgetting curve data per item.
    """
    items = list(
        db.execute(
            select(MemoryItem)
            .where(MemoryItem.room_id == room_id, MemoryItem.last_reviewed_at.isnot(None))
            .order_by(MemoryItem.last_reviewed_at.desc())
            .limit(_MAX_FORGETTING_CURVE_ITEMS)
        )
        .scalars()
        .all()
    )

    result_items = []
    for item in items:
        stability = item.interval * item.ease_factor
        # Prevent division by zero
        if stability <= 0:
            stability = 1.0

        # Generate curve points from 0 to 2 * interval days
        max_days = max(item.interval * 2, _MIN_CURVE_DAYS)
        curve_points = []
        for i in range(_FORGETTING_CURVE_POINTS + 1):
            t = (i / _FORGETTING_CURVE_POINTS) * max_days
            retention = math.exp(-t / stability)
            curve_points.append(
                {
                    "days_since_review": round(t, 2),
                    "retention": round(retention, 4),
                }
            )

        content_preview = (
            item.content[:_CONTENT_PREVIEW_LENGTH] if len(item.content) > _CONTENT_PREVIEW_LENGTH else item.content
        )
        result_items.append(
            {
                "item_id": item.id,
                "content": content_preview,
                "stability": round(stability, 2),
                "curve": curve_points,
            }
        )

    return {"items": result_items}
