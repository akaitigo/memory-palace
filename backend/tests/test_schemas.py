"""Tests for Pydantic schemas (request/response DTOs)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from memory_palace.schemas import (
    MemoryItemCreate,
    MemoryItemResponse,
    MemoryItemUpdate,
    PositionSchema,
    ReviewRecordCreate,
    ReviewRecordResponse,
    ReviewSessionResponse,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)

# =============================================================================
# RoomCreate validation tests
# =============================================================================


class TestRoomCreate:
    """Tests for RoomCreate schema validation."""

    def test_valid_room_create(self):
        """Valid room creation data passes validation."""
        room = RoomCreate(name="My Room", description="A test room")
        assert room.name == "My Room"
        assert room.description == "A test room"

    def test_room_name_empty(self):
        """Empty room name is rejected."""
        with pytest.raises(ValidationError):
            RoomCreate(name="")

    def test_room_name_too_long(self):
        """Room name exceeding 100 characters is rejected."""
        with pytest.raises(ValidationError):
            RoomCreate(name="a" * 101)

    def test_room_with_layout_data(self):
        """Room can include layout data."""
        layout = {"floor": {"width": 10, "height": 10}}
        room = RoomCreate(name="Layout Room", layout_data=layout)
        assert room.layout_data is not None
        assert room.layout_data["floor"]["width"] == 10

    def test_room_optional_fields(self):
        """Room can be created with only required fields."""
        room = RoomCreate(name="Minimal Room")
        assert room.description is None
        assert room.layout_data is None


class TestRoomUpdate:
    """Tests for RoomUpdate schema validation."""

    def test_partial_update(self):
        """RoomUpdate allows partial updates."""
        update = RoomUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.description is None

    def test_update_name_too_long(self):
        """Updated room name exceeding 100 characters is rejected."""
        with pytest.raises(ValidationError):
            RoomUpdate(name="a" * 101)


class TestRoomResponse:
    """Tests for RoomResponse schema."""

    def test_room_response_from_dict(self):
        """RoomResponse can be created from a dict."""
        now = datetime.now(tz=UTC)
        response = RoomResponse(
            id=uuid.uuid4(),
            owner_id=uuid.uuid4(),
            name="Test Room",
            description=None,
            layout_data=None,
            created_at=now,
            updated_at=now,
        )
        assert response.name == "Test Room"


# =============================================================================
# PositionSchema validation tests
# =============================================================================


class TestPositionSchema:
    """Tests for PositionSchema validation."""

    def test_valid_position(self):
        """Valid position passes validation."""
        pos = PositionSchema(x=1.0, y=2.0, z=3.0)
        assert pos.x == 1.0
        assert pos.y == 2.0
        assert pos.z == 3.0

    def test_position_at_bounds(self):
        """Position at boundary values passes validation."""
        pos = PositionSchema(x=-1000.0, y=1000.0, z=0.0)
        assert pos.x == -1000.0
        assert pos.y == 1000.0

    def test_position_x_too_large(self):
        """X coordinate exceeding 1000.0 is rejected."""
        with pytest.raises(ValidationError):
            PositionSchema(x=1000.1, y=0.0, z=0.0)

    def test_position_x_too_small(self):
        """X coordinate below -1000.0 is rejected."""
        with pytest.raises(ValidationError):
            PositionSchema(x=-1000.1, y=0.0, z=0.0)

    def test_position_y_too_large(self):
        """Y coordinate exceeding 1000.0 is rejected."""
        with pytest.raises(ValidationError):
            PositionSchema(x=0.0, y=1001.0, z=0.0)

    def test_position_z_too_small(self):
        """Z coordinate below -1000.0 is rejected."""
        with pytest.raises(ValidationError):
            PositionSchema(x=0.0, y=0.0, z=-1001.0)


# =============================================================================
# MemoryItemCreate validation tests
# =============================================================================


class TestMemoryItemCreate:
    """Tests for MemoryItemCreate schema validation."""

    def test_valid_memory_item_create(self):
        """Valid memory item creation data passes validation."""
        item = MemoryItemCreate(
            content="The capital of France is Paris",
            position=PositionSchema(x=1.0, y=2.0, z=3.0),
        )
        assert item.content == "The capital of France is Paris"
        assert item.position.x == 1.0

    def test_content_empty(self):
        """Empty content is rejected."""
        with pytest.raises(ValidationError):
            MemoryItemCreate(content="")

    def test_content_too_long(self):
        """Content exceeding 10,000 characters is rejected."""
        with pytest.raises(ValidationError):
            MemoryItemCreate(content="a" * 10001)

    def test_default_position(self):
        """Default position is origin (0, 0, 0)."""
        item = MemoryItemCreate(content="Default position")
        assert item.position.x == 0.0
        assert item.position.y == 0.0
        assert item.position.z == 0.0

    def test_with_image_url(self):
        """Memory item can include an image URL."""
        item = MemoryItemCreate(
            content="Item with image",
            image_url="https://example.com/image.png",
        )
        assert item.image_url == "https://example.com/image.png"

    def test_image_url_too_long(self):
        """Image URL exceeding 2048 characters is rejected."""
        with pytest.raises(ValidationError):
            MemoryItemCreate(content="Test", image_url="https://example.com/" + "a" * 2048)

    def test_position_out_of_bounds_rejected(self):
        """Memory item with out-of-bounds position is rejected."""
        with pytest.raises(ValidationError):
            MemoryItemCreate(
                content="Out of bounds",
                position=PositionSchema(x=2000.0, y=0.0, z=0.0),
            )


class TestMemoryItemUpdate:
    """Tests for MemoryItemUpdate schema validation."""

    def test_partial_update(self):
        """MemoryItemUpdate allows partial updates."""
        update = MemoryItemUpdate(content="Updated content")
        assert update.content == "Updated content"
        assert update.position is None

    def test_update_position(self):
        """MemoryItemUpdate can update position."""
        update = MemoryItemUpdate(position=PositionSchema(x=5.0, y=6.0, z=7.0))
        assert update.position is not None
        assert update.position.x == 5.0


class TestMemoryItemResponse:
    """Tests for MemoryItemResponse schema."""

    def test_memory_item_response(self):
        """MemoryItemResponse includes SM-2 parameters."""
        now = datetime.now(tz=UTC)
        response = MemoryItemResponse(
            id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            content="Test item",
            image_url=None,
            position_x=1.0,
            position_y=2.0,
            position_z=3.0,
            ease_factor=2.5,
            interval=1,
            repetitions=0,
            last_reviewed_at=None,
            created_at=now,
            updated_at=now,
        )
        assert response.ease_factor == 2.5
        assert response.interval == 1
        assert response.repetitions == 0


# =============================================================================
# ReviewRecordCreate validation tests
# =============================================================================


class TestReviewRecordCreate:
    """Tests for ReviewRecordCreate schema validation."""

    def test_valid_review_record(self):
        """Valid review record passes validation."""
        record = ReviewRecordCreate(
            memory_item_id=uuid.uuid4(),
            quality=5,
            response_time_ms=1500,
        )
        assert record.quality == 5
        assert record.response_time_ms == 1500

    def test_quality_below_minimum(self):
        """Quality below 0 is rejected."""
        with pytest.raises(ValidationError):
            ReviewRecordCreate(
                memory_item_id=uuid.uuid4(),
                quality=-1,
                response_time_ms=1000,
            )

    def test_quality_above_maximum(self):
        """Quality above 5 is rejected."""
        with pytest.raises(ValidationError):
            ReviewRecordCreate(
                memory_item_id=uuid.uuid4(),
                quality=6,
                response_time_ms=1000,
            )

    def test_all_quality_values_valid(self):
        """Quality values 0-5 are all valid."""
        for q in range(6):
            record = ReviewRecordCreate(
                memory_item_id=uuid.uuid4(),
                quality=q,
                response_time_ms=1000,
            )
            assert record.quality == q

    def test_response_time_zero(self):
        """Response time of 0 is rejected (must be positive)."""
        with pytest.raises(ValidationError):
            ReviewRecordCreate(
                memory_item_id=uuid.uuid4(),
                quality=3,
                response_time_ms=0,
            )

    def test_response_time_negative(self):
        """Negative response time is rejected."""
        with pytest.raises(ValidationError):
            ReviewRecordCreate(
                memory_item_id=uuid.uuid4(),
                quality=3,
                response_time_ms=-100,
            )

    def test_response_time_exceeds_maximum(self):
        """Response time exceeding 300,000ms (5 min) is rejected."""
        with pytest.raises(ValidationError):
            ReviewRecordCreate(
                memory_item_id=uuid.uuid4(),
                quality=3,
                response_time_ms=300001,
            )

    def test_response_time_at_maximum(self):
        """Response time at exactly 300,000ms is valid."""
        record = ReviewRecordCreate(
            memory_item_id=uuid.uuid4(),
            quality=3,
            response_time_ms=300000,
        )
        assert record.response_time_ms == 300000


class TestReviewRecordResponse:
    """Tests for ReviewRecordResponse schema."""

    def test_review_record_response(self):
        """ReviewRecordResponse can be created from a dict."""
        now = datetime.now(tz=UTC)
        response = ReviewRecordResponse(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            memory_item_id=uuid.uuid4(),
            quality=4,
            response_time_ms=2000,
            reviewed_at=now,
        )
        assert response.quality == 4


class TestReviewSessionResponse:
    """Tests for ReviewSessionResponse schema."""

    def test_review_session_response(self):
        """ReviewSessionResponse includes review records."""
        now = datetime.now(tz=UTC)
        response = ReviewSessionResponse(
            id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            total_items=5,
            completed_items=3,
            started_at=now,
            completed_at=None,
            review_records=[],
        )
        assert response.total_items == 5
        assert response.completed_at is None
        assert response.review_records == []

    def test_review_session_with_records(self):
        """ReviewSessionResponse can include nested review records."""
        now = datetime.now(tz=UTC)
        record = ReviewRecordResponse(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            memory_item_id=uuid.uuid4(),
            quality=5,
            response_time_ms=800,
            reviewed_at=now,
        )
        response = ReviewSessionResponse(
            id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            total_items=1,
            completed_items=1,
            started_at=now,
            completed_at=now,
            review_records=[record],
        )
        assert len(response.review_records) == 1
        assert response.review_records[0].quality == 5
