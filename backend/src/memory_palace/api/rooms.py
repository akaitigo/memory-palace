"""Room CRUD API endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from memory_palace.database import get_db
from memory_palace.models.memory_item import MemoryItem
from memory_palace.models.room import Room
from memory_palace.schemas.memory_item import (
    MemoryItemCreate,
    MemoryItemResponse,
    MemoryItemUpdate,
)
from memory_palace.schemas.room import RoomCreate, RoomResponse, RoomUpdate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


def _get_room_or_404(db: Session, room_id: uuid.UUID) -> Room:
    """Retrieve a room by ID or raise 404."""
    room = db.execute(select(Room).where(Room.id == room_id)).scalar_one_or_none()
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room {room_id} not found",
        )
    return room


def _get_item_or_404(db: Session, item_id: uuid.UUID, room_id: uuid.UUID) -> MemoryItem:
    """Retrieve a memory item by ID within a room or raise 404."""
    item = db.execute(
        select(MemoryItem).where(
            MemoryItem.id == item_id,
            MemoryItem.room_id == room_id,
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MemoryItem {item_id} not found in room {room_id}",
        )
    return item


# =============================================================================
# Room CRUD
# =============================================================================


@router.get("", response_model=list[RoomResponse])
def list_rooms(db: Session = Depends(get_db)) -> list[Room]:
    """List all rooms.

    Note: MVP does not implement auth. Owner filtering will be added later.
    """
    return list(db.execute(select(Room).order_by(Room.created_at.desc())).scalars().all())


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(body: RoomCreate, db: Session = Depends(get_db)) -> Room:
    """Create a new room.

    Note: MVP uses a hardcoded owner_id. Auth will be added later.
    """
    # MVP: use a deterministic dummy owner id until auth is implemented
    dummy_owner_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    room = Room(
        owner_id=dummy_owner_id,
        name=body.name,
        description=body.description,
        layout_data=body.layout_data,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: uuid.UUID, db: Session = Depends(get_db)) -> Room:
    """Get a room by ID."""
    return _get_room_or_404(db, room_id)


@router.patch("/{room_id}", response_model=RoomResponse)
def update_room(room_id: uuid.UUID, body: RoomUpdate, db: Session = Depends(get_db)) -> Room:
    """Update a room."""
    room = _get_room_or_404(db, room_id)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a room and all its memory items (cascade)."""
    room = _get_room_or_404(db, room_id)
    db.delete(room)
    db.commit()


# =============================================================================
# MemoryItem CRUD (nested under rooms)
# =============================================================================


@router.get("/{room_id}/items", response_model=list[MemoryItemResponse])
def list_items(room_id: uuid.UUID, db: Session = Depends(get_db)) -> list[MemoryItem]:
    """List all memory items in a room."""
    _get_room_or_404(db, room_id)
    return list(
        db.execute(select(MemoryItem).where(MemoryItem.room_id == room_id).order_by(MemoryItem.created_at))
        .scalars()
        .all()
    )


@router.post("/{room_id}/items", response_model=MemoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(room_id: uuid.UUID, body: MemoryItemCreate, db: Session = Depends(get_db)) -> MemoryItem:
    """Create a memory item in a room."""
    _get_room_or_404(db, room_id)
    item = MemoryItem(
        room_id=room_id,
        content=body.content,
        image_url=body.image_url,
        position_x=body.position.x,
        position_y=body.position.y,
        position_z=body.position.z,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{room_id}/items/{item_id}", response_model=MemoryItemResponse)
def get_item(room_id: uuid.UUID, item_id: uuid.UUID, db: Session = Depends(get_db)) -> MemoryItem:
    """Get a memory item by ID."""
    return _get_item_or_404(db, item_id, room_id)


@router.patch("/{room_id}/items/{item_id}", response_model=MemoryItemResponse)
def update_item(
    room_id: uuid.UUID,
    item_id: uuid.UUID,
    body: MemoryItemUpdate,
    db: Session = Depends(get_db),
) -> MemoryItem:
    """Update a memory item (content, position, image_url)."""
    item = _get_item_or_404(db, item_id, room_id)
    update_data = body.model_dump(exclude_unset=True)

    # Handle nested position schema
    if "position" in update_data and update_data["position"] is not None:
        position = update_data.pop("position")
        item.position_x = position["x"]
        item.position_y = position["y"]
        item.position_z = position["z"]
    else:
        update_data.pop("position", None)

    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{room_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(room_id: uuid.UUID, item_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a memory item."""
    item = _get_item_or_404(db, item_id, room_id)
    db.delete(item)
    db.commit()
