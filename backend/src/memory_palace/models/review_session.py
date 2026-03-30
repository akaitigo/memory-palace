"""ReviewSession model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_palace.database import Base

if TYPE_CHECKING:
    from memory_palace.models.review_record import ReviewRecord
    from memory_palace.models.room import Room


class ReviewSession(Base):
    """A review session grouping multiple review records.

    Tracks a single study session where the user reviews items in a room.
    """

    __tablename__ = "review_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_items: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of items reviewed in this session",
    )
    completed_items: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of items completed in this session",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the session was completed (null if in progress)",
    )

    # Relationships
    room: Mapped[Room] = relationship(
        "Room",
    )
    review_records: Mapped[list[ReviewRecord]] = relationship(
        "ReviewRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ReviewSession(id={self.id}, room_id={self.room_id})>"
