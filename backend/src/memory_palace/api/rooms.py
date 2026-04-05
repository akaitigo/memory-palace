"""Room CRUD API endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_palace.auth import get_current_user
from memory_palace.database import get_db
from memory_palace.models.memory_item import MemoryItem
from memory_palace.models.room import Room
from memory_palace.models.user import User
from memory_palace.schemas.memory_item import (
    MemoryItemCreate,
    MemoryItemResponse,
    MemoryItemUpdate,
)
from memory_palace.schemas.room import RoomCreate, RoomResponse, RoomUpdate

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


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


_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500


@router.get("", response_model=list[RoomResponse])
def list_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT, description="Maximum number of rooms to return"),
    offset: int = Query(default=0, ge=0, description="Number of rooms to skip"),
) -> list[Room]:
    """List rooms owned by the authenticated user with pagination."""
    return list(
        db.execute(
            select(Room)
            .where(Room.owner_id == current_user.id)
            .order_by(Room.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    body: RoomCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Room:
    """Create a new room owned by the authenticated user."""
    room = Room(
        owner_id=current_user.id,
        name=body.name,
        description=body.description,
        layout_data=body.layout_data,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Room:
    """Get a room by ID (must be owned by the authenticated user)."""
    return _get_room_or_404(db, room_id, current_user.id)


@router.patch("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: uuid.UUID,
    body: RoomUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Room:
    """Update a room.

    Only fields explicitly included in the request body are updated.
    Null values are excluded to prevent accidentally clearing columns.
    """
    room = _get_room_or_404(db, room_id, current_user.id)
    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a room and all its memory items (cascade)."""
    room = _get_room_or_404(db, room_id, current_user.id)
    db.delete(room)
    db.commit()


# =============================================================================
# MemoryItem CRUD (nested under rooms)
# =============================================================================


@router.get("/{room_id}/items", response_model=list[MemoryItemResponse])
def list_items(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT, description="Maximum number of items to return"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
) -> list[MemoryItem]:
    """List memory items in a room with pagination."""
    _get_room_or_404(db, room_id, current_user.id)
    return list(
        db.execute(
            select(MemoryItem)
            .where(MemoryItem.room_id == room_id)
            .order_by(MemoryItem.created_at)
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )


@router.post("/{room_id}/items", response_model=MemoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    room_id: uuid.UUID,
    body: MemoryItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MemoryItem:
    """Create a memory item in a room."""
    _get_room_or_404(db, room_id, current_user.id)
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
def get_item(
    room_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MemoryItem:
    """Get a memory item by ID."""
    _get_room_or_404(db, room_id, current_user.id)
    return _get_item_or_404(db, item_id, room_id)


@router.patch("/{room_id}/items/{item_id}", response_model=MemoryItemResponse)
def update_item(
    room_id: uuid.UUID,
    item_id: uuid.UUID,
    body: MemoryItemUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MemoryItem:
    """Update a memory item (content, position, image_url)."""
    _get_room_or_404(db, room_id, current_user.id)
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
def delete_item(
    room_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a memory item."""
    _get_room_or_404(db, room_id, current_user.id)
    item = _get_item_or_404(db, item_id, room_id)
    db.delete(item)
    db.commit()
