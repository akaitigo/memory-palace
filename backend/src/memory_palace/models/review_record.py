"""ReviewRecord model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_palace.database import Base

if TYPE_CHECKING:
    from memory_palace.models.memory_item import MemoryItem
    from memory_palace.models.review_session import ReviewSession


class ReviewRecord(Base):
    """A single review record for a memory item within a session.

    Attributes:
        quality: Self-assessment score (0-5).
            0 = Complete blackout
            1 = Incorrect, but recognized the correct answer
            2 = Incorrect, but seemed easy to recall
            3 = Correct with significant difficulty
            4 = Correct after hesitation
            5 = Perfect, instant recall
        response_time_ms: Time taken to respond in milliseconds (max 300,000 = 5 min).
    """

    __tablename__ = "review_records"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("review_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quality: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Self-assessment quality score (0-5)",
    )
    response_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Response time in milliseconds (max 300,000)",
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped[ReviewSession] = relationship(
        "ReviewSession",
        back_populates="review_records",
    )
    memory_item: Mapped[MemoryItem] = relationship(
        "MemoryItem",
        back_populates="review_records",
    )

    def __repr__(self) -> str:
        return f"<ReviewRecord(id={self.id}, quality={self.quality})>"
