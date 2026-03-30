"""Room model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_palace.database import Base

if TYPE_CHECKING:
    from memory_palace.models.memory_item import MemoryItem
    from memory_palace.models.user import User


class Room(Base):
    """A virtual room in the memory palace containing memory items."""

    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    layout_data: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
        default=dict,
        doc="3D layout data for the room (floor, walls, decorations)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owner: Mapped[User] = relationship(
        "User",
        back_populates="rooms",
    )
    memory_items: Mapped[list[MemoryItem]] = relationship(
        "MemoryItem",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Room(id={self.id}, name={self.name!r})>"
