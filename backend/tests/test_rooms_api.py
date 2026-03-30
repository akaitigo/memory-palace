"""Tests for Room and MemoryItem CRUD API endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from memory_palace.database import Base, get_db
from memory_palace.main import app

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm import Session

# Shared engine for all tests — StaticPool ensures the same in-memory DB is reused.
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(bind=_engine)


@pytest.fixture(autouse=True)
def _setup_db():
    """Create all tables before each test and drop after."""
    Base.metadata.create_all(_engine)

    yield

    Base.metadata.drop_all(_engine)


def _override_get_db() -> Generator[Session, None, None]:
    session = _TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# =============================================================================
# Room CRUD tests
# =============================================================================


class TestRoomAPI:
    """Tests for Room CRUD endpoints."""

    def test_list_rooms_empty(self, client: TestClient):
        """GET /api/rooms returns empty list when no rooms exist."""
        response = client.get("/api/rooms")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_room(self, client: TestClient):
        """POST /api/rooms creates a new room."""
        response = client.post(
            "/api/rooms",
            json={"name": "Test Room", "description": "A test room"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Room"
        assert data["description"] == "A test room"
        assert "id" in data
        assert "created_at" in data

    def test_create_room_minimal(self, client: TestClient):
        """POST /api/rooms works with only required fields."""
        response = client.post("/api/rooms", json={"name": "Minimal"})
        assert response.status_code == 201
        assert response.json()["name"] == "Minimal"

    def test_create_room_empty_name_rejected(self, client: TestClient):
        """POST /api/rooms rejects empty name."""
        response = client.post("/api/rooms", json={"name": ""})
        assert response.status_code == 422

    def test_create_room_name_too_long_rejected(self, client: TestClient):
        """POST /api/rooms rejects name longer than 100 chars."""
        response = client.post("/api/rooms", json={"name": "a" * 101})
        assert response.status_code == 422

    def test_get_room(self, client: TestClient):
        """GET /api/rooms/{room_id} returns the room."""
        create_resp = client.post("/api/rooms", json={"name": "Get Room"})
        room_id = create_resp.json()["id"]

        response = client.get(f"/api/rooms/{room_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Room"

    def test_get_room_not_found(self, client: TestClient):
        """GET /api/rooms/{room_id} returns 404 for nonexistent room."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{fake_id}")
        assert response.status_code == 404

    def test_update_room(self, client: TestClient):
        """PATCH /api/rooms/{room_id} updates the room."""
        create_resp = client.post("/api/rooms", json={"name": "Original"})
        room_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_update_room_partial(self, client: TestClient):
        """PATCH /api/rooms/{room_id} supports partial updates."""
        create_resp = client.post(
            "/api/rooms",
            json={"name": "Partial", "description": "Original desc"},
        )
        room_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}",
            json={"description": "New desc"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Partial"
        assert data["description"] == "New desc"

    def test_update_room_not_found(self, client: TestClient):
        """PATCH /api/rooms/{room_id} returns 404 for nonexistent room."""
        fake_id = str(uuid.uuid4())
        response = client.patch(f"/api/rooms/{fake_id}", json={"name": "X"})
        assert response.status_code == 404

    def test_delete_room(self, client: TestClient):
        """DELETE /api/rooms/{room_id} removes the room."""
        create_resp = client.post("/api/rooms", json={"name": "To Delete"})
        room_id = create_resp.json()["id"]

        response = client.delete(f"/api/rooms/{room_id}")
        assert response.status_code == 204

        # Confirm deletion
        get_resp = client.get(f"/api/rooms/{room_id}")
        assert get_resp.status_code == 404

    def test_delete_room_not_found(self, client: TestClient):
        """DELETE /api/rooms/{room_id} returns 404 for nonexistent room."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/rooms/{fake_id}")
        assert response.status_code == 404

    def test_list_rooms_returns_created_rooms(self, client: TestClient):
        """GET /api/rooms lists all created rooms."""
        client.post("/api/rooms", json={"name": "Room 1"})
        client.post("/api/rooms", json={"name": "Room 2"})

        response = client.get("/api/rooms")
        assert response.status_code == 200
        rooms = response.json()
        assert len(rooms) == 2

    def test_create_room_with_layout_data(self, client: TestClient):
        """POST /api/rooms stores layout_data."""
        layout = {"floor": {"width": 20, "depth": 20}, "walls": []}
        response = client.post(
            "/api/rooms",
            json={"name": "Layout Room", "layout_data": layout},
        )
        assert response.status_code == 201
        assert response.json()["layout_data"]["floor"]["width"] == 20


# =============================================================================
# MemoryItem CRUD tests
# =============================================================================


class TestMemoryItemAPI:
    """Tests for MemoryItem CRUD endpoints nested under rooms."""

    @pytest.fixture
    def room_id(self, client: TestClient) -> str:
        """Create a room and return its ID."""
        resp = client.post("/api/rooms", json={"name": "Item Test Room"})
        return resp.json()["id"]

    def test_list_items_empty(self, client: TestClient, room_id: str):
        """GET /api/rooms/{room_id}/items returns empty list."""
        response = client.get(f"/api/rooms/{room_id}/items")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_item(self, client: TestClient, room_id: str):
        """POST /api/rooms/{room_id}/items creates a memory item."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={
                "content": "The capital of France is Paris",
                "position": {"x": 1.0, "y": 0.0, "z": 2.5},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "The capital of France is Paris"
        assert data["position_x"] == 1.0
        assert data["position_z"] == 2.5
        assert data["room_id"] == room_id
        # Check SM-2 defaults
        assert data["ease_factor"] == 2.5
        assert data["interval"] == 1
        assert data["repetitions"] == 0

    def test_create_item_default_position(self, client: TestClient, room_id: str):
        """POST /api/rooms/{room_id}/items uses default position (0,0,0)."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Default position item"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["position_x"] == 0.0
        assert data["position_y"] == 0.0
        assert data["position_z"] == 0.0

    def test_create_item_empty_content_rejected(self, client: TestClient, room_id: str):
        """POST /api/rooms/{room_id}/items rejects empty content."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "", "position": {"x": 0, "y": 0, "z": 0}},
        )
        assert response.status_code == 422

    def test_create_item_content_too_long_rejected(self, client: TestClient, room_id: str):
        """POST /api/rooms/{room_id}/items rejects content over 10000 chars."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "a" * 10001, "position": {"x": 0, "y": 0, "z": 0}},
        )
        assert response.status_code == 422

    def test_create_item_position_out_of_bounds_rejected(self, client: TestClient, room_id: str):
        """POST /api/rooms/{room_id}/items rejects out-of-bounds positions."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "OOB", "position": {"x": 2000.0, "y": 0, "z": 0}},
        )
        assert response.status_code == 422

    def test_create_item_nonexistent_room(self, client: TestClient):
        """POST /api/rooms/{room_id}/items returns 404 for fake room."""
        fake_id = str(uuid.uuid4())
        response = client.post(
            f"/api/rooms/{fake_id}/items",
            json={"content": "Test", "position": {"x": 0, "y": 0, "z": 0}},
        )
        assert response.status_code == 404

    def test_get_item(self, client: TestClient, room_id: str):
        """GET /api/rooms/{room_id}/items/{item_id} returns the item."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Get me", "position": {"x": 1, "y": 0, "z": 1}},
        )
        item_id = create_resp.json()["id"]

        response = client.get(f"/api/rooms/{room_id}/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["content"] == "Get me"

    def test_get_item_not_found(self, client: TestClient, room_id: str):
        """GET /api/rooms/{room_id}/items/{item_id} returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{room_id}/items/{fake_id}")
        assert response.status_code == 404

    def test_update_item_content(self, client: TestClient, room_id: str):
        """PATCH /api/rooms/{room_id}/items/{item_id} updates content."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Original", "position": {"x": 0, "y": 0, "z": 0}},
        )
        item_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}/items/{item_id}",
            json={"content": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated"

    def test_update_item_position(self, client: TestClient, room_id: str):
        """PATCH /api/rooms/{room_id}/items/{item_id} updates position."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Move me", "position": {"x": 0, "y": 0, "z": 0}},
        )
        item_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}/items/{item_id}",
            json={"position": {"x": 5.0, "y": 0.0, "z": 3.0}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position_x"] == 5.0
        assert data["position_z"] == 3.0

    def test_update_item_not_found(self, client: TestClient, room_id: str):
        """PATCH /api/rooms/{room_id}/items/{item_id} returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/rooms/{room_id}/items/{fake_id}",
            json={"content": "X"},
        )
        assert response.status_code == 404

    def test_delete_item(self, client: TestClient, room_id: str):
        """DELETE /api/rooms/{room_id}/items/{item_id} removes the item."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Delete me", "position": {"x": 0, "y": 0, "z": 0}},
        )
        item_id = create_resp.json()["id"]

        response = client.delete(f"/api/rooms/{room_id}/items/{item_id}")
        assert response.status_code == 204

        # Confirm deletion
        get_resp = client.get(f"/api/rooms/{room_id}/items/{item_id}")
        assert get_resp.status_code == 404

    def test_delete_item_not_found(self, client: TestClient, room_id: str):
        """DELETE /api/rooms/{room_id}/items/{item_id} returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/rooms/{room_id}/items/{fake_id}")
        assert response.status_code == 404

    def test_list_items_returns_all_items(self, client: TestClient, room_id: str):
        """GET /api/rooms/{room_id}/items returns all items."""
        for i in range(3):
            client.post(
                f"/api/rooms/{room_id}/items",
                json={
                    "content": f"Item {i}",
                    "position": {"x": float(i), "y": 0, "z": 0},
                },
            )

        response = client.get(f"/api/rooms/{room_id}/items")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_delete_room_cascades_to_items(self, client: TestClient, room_id: str):
        """Deleting a room also deletes its items."""
        client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Cascade test", "position": {"x": 0, "y": 0, "z": 0}},
        )

        client.delete(f"/api/rooms/{room_id}")

        # Room and items should be gone
        assert client.get(f"/api/rooms/{room_id}").status_code == 404

    def test_create_item_with_image_url(self, client: TestClient, room_id: str):
        """POST /api/rooms/{room_id}/items supports image_url."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={
                "content": "Item with image",
                "image_url": "https://example.com/img.png",
                "position": {"x": 0, "y": 0, "z": 0},
            },
        )
        assert response.status_code == 201
        assert response.json()["image_url"] == "https://example.com/img.png"

    def test_item_content_up_to_500_accepted(self, client: TestClient, room_id: str):
        """Items with content up to 500 chars are accepted."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={
                "content": "a" * 500,
                "position": {"x": 0, "y": 0, "z": 0},
            },
        )
        assert response.status_code == 201
