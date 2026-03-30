"""Tests for SQLAlchemy ORM models (CRUD operations)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from memory_palace.database import Base
from memory_palace.models import MemoryItem, ReviewRecord, ReviewSession, Room, User


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


# =============================================================================
# User model tests
# =============================================================================


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, db_session: Session):
        """User can be created with required fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"

    def test_user_has_uuid_id(self, db_session: Session):
        """User ID is a valid UUID."""
        user = User(
            username="uuiduser",
            email="uuid@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # ID should be a valid UUID (may be string in SQLite)
        assert user.id is not None
        if isinstance(user.id, uuid.UUID):
            assert user.id.version == 4

    def test_read_user(self, db_session: Session):
        """User can be queried from database."""
        user = User(
            username="readuser",
            email="read@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        found = db_session.query(User).filter_by(username="readuser").first()
        assert found is not None
        assert found.email == "read@example.com"

    def test_update_user(self, db_session: Session):
        """User fields can be updated."""
        user = User(
            username="updateuser",
            email="update@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        user.email = "updated@example.com"
        db_session.commit()
        db_session.refresh(user)

        assert user.email == "updated@example.com"

    def test_delete_user(self, db_session: Session):
        """User can be deleted from database."""
        user = User(
            username="deleteuser",
            email="delete@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        db_session.delete(user)
        db_session.commit()

        found = db_session.query(User).filter_by(username="deleteuser").first()
        assert found is None

    def test_user_repr(self, db_session: Session):
        """User repr includes id and username."""
        user = User(
            username="repruser",
            email="repr@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        repr_str = repr(user)
        assert "User" in repr_str
        assert "repruser" in repr_str


# =============================================================================
# Room model tests
# =============================================================================


class TestRoomModel:
    """Tests for the Room model."""

    @pytest.fixture
    def user(self, db_session: Session):
        """Create a user for room tests."""
        user = User(
            username="roomowner",
            email="owner@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_create_room(self, db_session: Session, user: User):
        """Room can be created with required fields."""
        room = Room(
            owner_id=user.id,
            name="Test Room",
            description="A test room",
        )
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)

        assert room.id is not None
        assert room.name == "Test Room"
        assert room.description == "A test room"
        assert room.owner_id == user.id

    def test_room_with_layout_data(self, db_session: Session, user: User):
        """Room can store JSONB layout data."""
        layout = {
            "floor": {"width": 10, "height": 10},
            "walls": [{"x": 0, "y": 0, "z": 0, "width": 10, "height": 3}],
        }
        room = Room(
            owner_id=user.id,
            name="Layout Room",
            layout_data=layout,
        )
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)

        assert room.layout_data is not None
        assert room.layout_data["floor"]["width"] == 10

    def test_room_owner_relationship(self, db_session: Session, user: User):
        """Room has a relationship to its owner."""
        room = Room(
            owner_id=user.id,
            name="Relationship Room",
        )
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)

        assert room.owner is not None
        assert room.owner.username == "roomowner"

    def test_user_rooms_relationship(self, db_session: Session, user: User):
        """User has a list of owned rooms."""
        room1 = Room(owner_id=user.id, name="Room 1")
        room2 = Room(owner_id=user.id, name="Room 2")
        db_session.add_all([room1, room2])
        db_session.commit()
        db_session.refresh(user)

        assert len(user.rooms) == 2

    def test_update_room(self, db_session: Session, user: User):
        """Room fields can be updated."""
        room = Room(owner_id=user.id, name="Original")
        db_session.add(room)
        db_session.commit()

        room.name = "Updated"
        db_session.commit()
        db_session.refresh(room)

        assert room.name == "Updated"

    def test_delete_room(self, db_session: Session, user: User):
        """Room can be deleted."""
        room = Room(owner_id=user.id, name="To Delete")
        db_session.add(room)
        db_session.commit()

        db_session.delete(room)
        db_session.commit()

        found = db_session.query(Room).filter_by(name="To Delete").first()
        assert found is None

    def test_room_repr(self, db_session: Session, user: User):
        """Room repr includes id and name."""
        room = Room(owner_id=user.id, name="ReprRoom")
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)

        repr_str = repr(room)
        assert "Room" in repr_str
        assert "ReprRoom" in repr_str


# =============================================================================
# MemoryItem model tests
# =============================================================================


class TestMemoryItemModel:
    """Tests for the MemoryItem model."""

    @pytest.fixture
    def room(self, db_session: Session):
        """Create a user and room for memory item tests."""
        user = User(
            username="itemowner",
            email="item@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        room = Room(owner_id=user.id, name="Item Room")
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)
        return room

    def test_create_memory_item(self, db_session: Session, room: Room):
        """MemoryItem can be created with required fields."""
        item = MemoryItem(
            room_id=room.id,
            content="The capital of France is Paris",
            position_x=1.0,
            position_y=2.0,
            position_z=3.0,
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.id is not None
        assert item.content == "The capital of France is Paris"
        assert item.position_x == 1.0
        assert item.position_y == 2.0
        assert item.position_z == 3.0

    def test_memory_item_sm2_defaults(self, db_session: Session, room: Room):
        """MemoryItem has correct SM-2 default values."""
        item = MemoryItem(
            room_id=room.id,
            content="SM-2 defaults test",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.ease_factor == 2.5
        assert item.interval == 1
        assert item.repetitions == 0
        assert item.last_reviewed_at is None

    def test_memory_item_position_defaults(self, db_session: Session, room: Room):
        """MemoryItem position defaults to origin."""
        item = MemoryItem(
            room_id=room.id,
            content="Position defaults test",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.position_x == 0.0
        assert item.position_y == 0.0
        assert item.position_z == 0.0

    def test_memory_item_with_image_url(self, db_session: Session, room: Room):
        """MemoryItem can store an optional image URL."""
        item = MemoryItem(
            room_id=room.id,
            content="Item with image",
            image_url="https://example.com/image.png",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.image_url == "https://example.com/image.png"

    def test_memory_item_room_relationship(self, db_session: Session, room: Room):
        """MemoryItem has a relationship to its room."""
        item = MemoryItem(room_id=room.id, content="Relationship test")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.room is not None
        assert item.room.name == "Item Room"

    def test_room_memory_items_relationship(self, db_session: Session, room: Room):
        """Room has a list of memory items."""
        item1 = MemoryItem(room_id=room.id, content="Item 1")
        item2 = MemoryItem(room_id=room.id, content="Item 2")
        db_session.add_all([item1, item2])
        db_session.commit()
        db_session.refresh(room)

        assert len(room.memory_items) == 2

    def test_update_memory_item_sm2_params(self, db_session: Session, room: Room):
        """SM-2 parameters can be updated after review."""
        item = MemoryItem(room_id=room.id, content="Update test")
        db_session.add(item)
        db_session.commit()

        # Simulate a quality=5 review
        item.ease_factor = 2.6
        item.interval = 6
        item.repetitions = 1
        item.last_reviewed_at = datetime.now(tz=UTC)
        db_session.commit()
        db_session.refresh(item)

        assert item.ease_factor == 2.6
        assert item.interval == 6
        assert item.repetitions == 1
        assert item.last_reviewed_at is not None

    def test_delete_memory_item(self, db_session: Session, room: Room):
        """MemoryItem can be deleted."""
        item = MemoryItem(room_id=room.id, content="To delete")
        db_session.add(item)
        db_session.commit()

        db_session.delete(item)
        db_session.commit()

        found = db_session.query(MemoryItem).filter_by(content="To delete").first()
        assert found is None


# =============================================================================
# ReviewSession model tests
# =============================================================================


class TestReviewSessionModel:
    """Tests for the ReviewSession model."""

    @pytest.fixture
    def room(self, db_session: Session):
        """Create a user and room for review session tests."""
        user = User(
            username="reviewowner",
            email="review@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        room = Room(owner_id=user.id, name="Review Room")
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)
        return room

    def test_create_review_session(self, db_session: Session, room: Room):
        """ReviewSession can be created."""
        session = ReviewSession(
            room_id=room.id,
            total_items=5,
            completed_items=0,
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        assert session.id is not None
        assert session.total_items == 5
        assert session.completed_items == 0
        assert session.completed_at is None

    def test_complete_review_session(self, db_session: Session, room: Room):
        """ReviewSession can be marked as completed."""
        session = ReviewSession(
            room_id=room.id,
            total_items=3,
            completed_items=0,
        )
        db_session.add(session)
        db_session.commit()

        session.completed_items = 3
        session.completed_at = datetime.now(tz=UTC)
        db_session.commit()
        db_session.refresh(session)

        assert session.completed_items == 3
        assert session.completed_at is not None

    def test_review_session_room_relationship(self, db_session: Session, room: Room):
        """ReviewSession has a relationship to its room."""
        session = ReviewSession(room_id=room.id, total_items=1)
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        assert session.room is not None
        assert session.room.name == "Review Room"

    def test_delete_review_session(self, db_session: Session, room: Room):
        """ReviewSession can be deleted."""
        session = ReviewSession(room_id=room.id, total_items=1)
        db_session.add(session)
        db_session.commit()

        db_session.delete(session)
        db_session.commit()

        found = db_session.query(ReviewSession).filter_by(room_id=room.id).first()
        assert found is None


# =============================================================================
# ReviewRecord model tests
# =============================================================================


class TestReviewRecordModel:
    """Tests for the ReviewRecord model."""

    @pytest.fixture
    def review_context(self, db_session: Session):
        """Create user, room, item, and session for review record tests."""
        user = User(
            username="recordowner",
            email="record@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        room = Room(owner_id=user.id, name="Record Room")
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)

        item = MemoryItem(room_id=room.id, content="Review target")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        session = ReviewSession(room_id=room.id, total_items=1)
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        return {"room": room, "item": item, "session": session}

    def test_create_review_record(self, db_session: Session, review_context):
        """ReviewRecord can be created with quality and response time."""
        record = ReviewRecord(
            session_id=review_context["session"].id,
            memory_item_id=review_context["item"].id,
            quality=5,
            response_time_ms=1500,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        assert record.id is not None
        assert record.quality == 5
        assert record.response_time_ms == 1500

    def test_review_record_quality_range(self, db_session: Session, review_context):
        """ReviewRecord supports quality values 0-5."""
        for q in range(6):
            record = ReviewRecord(
                session_id=review_context["session"].id,
                memory_item_id=review_context["item"].id,
                quality=q,
                response_time_ms=1000,
            )
            db_session.add(record)
        db_session.commit()

        records = db_session.query(ReviewRecord).all()
        qualities = sorted([r.quality for r in records])
        assert qualities == [0, 1, 2, 3, 4, 5]

    def test_review_record_session_relationship(self, db_session: Session, review_context):
        """ReviewRecord has a relationship to its session."""
        record = ReviewRecord(
            session_id=review_context["session"].id,
            memory_item_id=review_context["item"].id,
            quality=4,
            response_time_ms=2000,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        assert record.session is not None
        assert record.session.total_items == 1

    def test_review_record_memory_item_relationship(self, db_session: Session, review_context):
        """ReviewRecord has a relationship to its memory item."""
        record = ReviewRecord(
            session_id=review_context["session"].id,
            memory_item_id=review_context["item"].id,
            quality=3,
            response_time_ms=3000,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        assert record.memory_item is not None
        assert record.memory_item.content == "Review target"

    def test_session_review_records_relationship(self, db_session: Session, review_context):
        """ReviewSession has a list of review records."""
        for i in range(3):
            record = ReviewRecord(
                session_id=review_context["session"].id,
                memory_item_id=review_context["item"].id,
                quality=i + 3,
                response_time_ms=1000 * (i + 1),
            )
            db_session.add(record)
        db_session.commit()
        db_session.refresh(review_context["session"])

        assert len(review_context["session"].review_records) == 3

    def test_delete_review_record(self, db_session: Session, review_context):
        """ReviewRecord can be deleted."""
        record = ReviewRecord(
            session_id=review_context["session"].id,
            memory_item_id=review_context["item"].id,
            quality=5,
            response_time_ms=500,
        )
        db_session.add(record)
        db_session.commit()

        db_session.delete(record)
        db_session.commit()

        found = db_session.query(ReviewRecord).first()
        assert found is None

    def test_review_record_repr(self, db_session: Session, review_context):
        """ReviewRecord repr includes id and quality."""
        record = ReviewRecord(
            session_id=review_context["session"].id,
            memory_item_id=review_context["item"].id,
            quality=4,
            response_time_ms=1200,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        repr_str = repr(record)
        assert "ReviewRecord" in repr_str
        assert "4" in repr_str


# =============================================================================
# Cascade delete tests
# =============================================================================


class TestCascadeDelete:
    """Tests for cascade delete behavior."""

    def test_delete_user_cascades_to_rooms(self, db_session: Session):
        """Deleting a user also deletes their rooms."""
        user = User(username="cascade_user", email="cascade@example.com", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        room = Room(owner_id=user.id, name="Cascade Room")
        db_session.add(room)
        db_session.commit()

        db_session.delete(user)
        db_session.commit()

        assert db_session.query(Room).count() == 0

    def test_delete_room_cascades_to_items(self, db_session: Session):
        """Deleting a room also deletes its memory items."""
        user = User(username="cascade_room", email="cascade_room@example.com", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        room = Room(owner_id=user.id, name="To Delete Room")
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)

        item = MemoryItem(room_id=room.id, content="Cascade item")
        db_session.add(item)
        db_session.commit()

        db_session.delete(room)
        db_session.commit()

        assert db_session.query(MemoryItem).count() == 0

    def test_delete_session_cascades_to_records(self, db_session: Session):
        """Deleting a review session also deletes its records."""
        user = User(username="cascade_session", email="cascade_session@example.com", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        room = Room(owner_id=user.id, name="Cascade Session Room")
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)

        item = MemoryItem(room_id=room.id, content="Cascade review item")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        session = ReviewSession(room_id=room.id, total_items=1)
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        record = ReviewRecord(
            session_id=session.id,
            memory_item_id=item.id,
            quality=5,
            response_time_ms=1000,
        )
        db_session.add(record)
        db_session.commit()

        db_session.delete(session)
        db_session.commit()

        assert db_session.query(ReviewRecord).count() == 0
