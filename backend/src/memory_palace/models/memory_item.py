"""MemoryItem model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_palace.database import Base

if TYPE_CHECKING:
    from memory_palace.models.review_record import ReviewRecord
    from memory_palace.models.room import Room


class MemoryItem(Base):
    """A memory item placed in a room at a specific 3D position.

    SM-2 parameters:
        - ease_factor: Difficulty factor (minimum 1.3, default 2.5)
        - interval: Review interval in days (default 1)
        - repetitions: Number of consecutive correct answers (default 0)
    """

    __tablename__ = "memory_items"

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
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Memory target text (1-10,000 characters)",
    )
    image_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        doc="Optional image URL for the memory item",
    )

    # 3D position in the room
    position_x: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="X coordinate in 3D space (-1000.0 to 1000.0)",
    )
    position_y: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Y coordinate in 3D space (-1000.0 to 1000.0)",
    )
    position_z: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Z coordinate in 3D space (-1000.0 to 1000.0)",
    )

    # SM-2 algorithm parameters
    ease_factor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=2.5,
        doc="SM-2 ease factor (minimum 1.3)",
    )
    interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Review interval in days",
    )
    repetitions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of consecutive correct answers",
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Timestamp of the last review",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Optimistic lock version counter",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    room: Mapped[Room] = relationship(
        "Room",
        back_populates="memory_items",
    )
    review_records: Mapped[list[ReviewRecord]] = relationship(
        "ReviewRecord",
        back_populates="memory_item",
        cascade="all, delete-orphan",
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version}

    def __repr__(self) -> str:
        return f"<MemoryItem(id={self.id}, content={self.content[:30]!r}...)>"
