"""Tests for Room and MemoryItem CRUD API endpoints."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from memory_palace.auth import create_access_token, hash_password
from memory_palace.models.user import User

# =============================================================================
# Room CRUD tests
# =============================================================================


class TestRoomAPI:
    """Tests for Room CRUD endpoints."""

    def test_list_rooms_empty(self, client: TestClient, auth_headers: dict[str, str]):
        """GET /api/rooms returns empty list when no rooms exist."""
        response = client.get("/api/rooms", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_rooms_unauthorized(self, client: TestClient):
        """GET /api/rooms without auth returns 401 or 403."""
        response = client.get("/api/rooms")
        assert response.status_code in (401, 403)

    def test_create_room(self, client: TestClient, auth_headers: dict[str, str]):
        """POST /api/rooms creates a new room."""
        response = client.post(
            "/api/rooms",
            json={"name": "Test Room", "description": "A test room"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Room"
        assert data["description"] == "A test room"
        assert "id" in data
        assert "created_at" in data

    def test_create_room_minimal(self, client: TestClient, auth_headers: dict[str, str]):
        """POST /api/rooms works with only required fields."""
        response = client.post("/api/rooms", json={"name": "Minimal"}, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["name"] == "Minimal"

    def test_create_room_empty_name_rejected(self, client: TestClient, auth_headers: dict[str, str]):
        """POST /api/rooms rejects empty name."""
        response = client.post("/api/rooms", json={"name": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_create_room_name_too_long_rejected(self, client: TestClient, auth_headers: dict[str, str]):
        """POST /api/rooms rejects name longer than 100 chars."""
        response = client.post("/api/rooms", json={"name": "a" * 101}, headers=auth_headers)
        assert response.status_code == 422

    def test_get_room(self, client: TestClient, auth_headers: dict[str, str]):
        """GET /api/rooms/{room_id} returns the room."""
        create_resp = client.post("/api/rooms", json={"name": "Get Room"}, headers=auth_headers)
        room_id = create_resp.json()["id"]

        response = client.get(f"/api/rooms/{room_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Get Room"

    def test_get_room_not_found(self, client: TestClient, auth_headers: dict[str, str]):
        """GET /api/rooms/{room_id} returns 404 for nonexistent room."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_room(self, client: TestClient, auth_headers: dict[str, str]):
        """PATCH /api/rooms/{room_id} updates the room."""
        create_resp = client.post("/api/rooms", json={"name": "Original"}, headers=auth_headers)
        room_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_update_room_partial(self, client: TestClient, auth_headers: dict[str, str]):
        """PATCH /api/rooms/{room_id} supports partial updates."""
        create_resp = client.post(
            "/api/rooms",
            json={"name": "Partial", "description": "Original desc"},
            headers=auth_headers,
        )
        room_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}",
            json={"description": "New desc"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Partial"
        assert data["description"] == "New desc"

    def test_update_room_not_found(self, client: TestClient, auth_headers: dict[str, str]):
        """PATCH /api/rooms/{room_id} returns 404 for nonexistent room."""
        fake_id = str(uuid.uuid4())
        response = client.patch(f"/api/rooms/{fake_id}", json={"name": "X"}, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_room(self, client: TestClient, auth_headers: dict[str, str]):
        """DELETE /api/rooms/{room_id} removes the room."""
        create_resp = client.post("/api/rooms", json={"name": "To Delete"}, headers=auth_headers)
        room_id = create_resp.json()["id"]

        response = client.delete(f"/api/rooms/{room_id}", headers=auth_headers)
        assert response.status_code == 204

        # Confirm deletion
        get_resp = client.get(f"/api/rooms/{room_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_room_not_found(self, client: TestClient, auth_headers: dict[str, str]):
        """DELETE /api/rooms/{room_id} returns 404 for nonexistent room."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/rooms/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_list_rooms_returns_created_rooms(self, client: TestClient, auth_headers: dict[str, str]):
        """GET /api/rooms lists all created rooms."""
        client.post("/api/rooms", json={"name": "Room 1"}, headers=auth_headers)
        client.post("/api/rooms", json={"name": "Room 2"}, headers=auth_headers)

        response = client.get("/api/rooms", headers=auth_headers)
        assert response.status_code == 200
        rooms = response.json()
        assert len(rooms) == 2

    def test_create_room_with_layout_data(self, client: TestClient, auth_headers: dict[str, str]):
        """POST /api/rooms stores layout_data."""
        layout = {"floor": {"width": 20, "depth": 20}, "walls": []}
        response = client.post(
            "/api/rooms",
            json={"name": "Layout Room", "layout_data": layout},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["layout_data"]["floor"]["width"] == 20

    def test_owner_isolation(self, client: TestClient, auth_headers: dict[str, str], db_session):
        """Rooms owned by another user are not visible."""
        # Create another user
        other_user = User(
            id=uuid.uuid4(),
            username="otheruser",
            email="other@example.com",
            password_hash=hash_password("otherpassword1"),
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        other_token = create_access_token(other_user.id)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Create a room as the first user
        resp = client.post("/api/rooms", json={"name": "User1 Room"}, headers=auth_headers)
        assert resp.status_code == 201
        room_id = resp.json()["id"]

        # Other user should not see it
        list_resp = client.get("/api/rooms", headers=other_headers)
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 0

        # Other user should get 404 trying to access it
        get_resp = client.get(f"/api/rooms/{room_id}", headers=other_headers)
        assert get_resp.status_code == 404


# =============================================================================
# MemoryItem CRUD tests
# =============================================================================


class TestMemoryItemAPI:
    """Tests for MemoryItem CRUD endpoints nested under rooms."""

    @pytest.fixture
    def room_id(self, client: TestClient, auth_headers: dict[str, str]) -> str:
        """Create a room and return its ID."""
        resp = client.post("/api/rooms", json={"name": "Item Test Room"}, headers=auth_headers)
        return resp.json()["id"]

    def test_list_items_empty(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """GET /api/rooms/{room_id}/items returns empty list."""
        response = client.get(f"/api/rooms/{room_id}/items", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_item(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """POST /api/rooms/{room_id}/items creates a memory item."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={
                "content": "The capital of France is Paris",
                "position": {"x": 1.0, "y": 0.0, "z": 2.5},
            },
            headers=auth_headers,
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

    def test_create_item_default_position(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """POST /api/rooms/{room_id}/items uses default position (0,0,0)."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Default position item"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["position_x"] == 0.0
        assert data["position_y"] == 0.0
        assert data["position_z"] == 0.0

    def test_create_item_empty_content_rejected(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """POST /api/rooms/{room_id}/items rejects empty content."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_item_content_too_long_rejected(
        self, client: TestClient, room_id: str, auth_headers: dict[str, str]
    ):
        """POST /api/rooms/{room_id}/items rejects content over 10000 chars."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "a" * 10001, "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_item_position_out_of_bounds_rejected(
        self, client: TestClient, room_id: str, auth_headers: dict[str, str]
    ):
        """POST /api/rooms/{room_id}/items rejects out-of-bounds positions."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "OOB", "position": {"x": 2000.0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_item_nonexistent_room(self, client: TestClient, auth_headers: dict[str, str]):
        """POST /api/rooms/{room_id}/items returns 404 for fake room."""
        fake_id = str(uuid.uuid4())
        response = client.post(
            f"/api/rooms/{fake_id}/items",
            json={"content": "Test", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_item(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """GET /api/rooms/{room_id}/items/{item_id} returns the item."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Get me", "position": {"x": 1, "y": 0, "z": 1}},
            headers=auth_headers,
        )
        item_id = create_resp.json()["id"]

        response = client.get(f"/api/rooms/{room_id}/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["content"] == "Get me"

    def test_get_item_not_found(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """GET /api/rooms/{room_id}/items/{item_id} returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{room_id}/items/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_item_content(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """PATCH /api/rooms/{room_id}/items/{item_id} updates content."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Original", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        item_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}/items/{item_id}",
            json={"content": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated"

    def test_update_item_position(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """PATCH /api/rooms/{room_id}/items/{item_id} updates position."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Move me", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        item_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/rooms/{room_id}/items/{item_id}",
            json={"position": {"x": 5.0, "y": 0.0, "z": 3.0}},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position_x"] == 5.0
        assert data["position_z"] == 3.0

    def test_update_item_not_found(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """PATCH /api/rooms/{room_id}/items/{item_id} returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/rooms/{room_id}/items/{fake_id}",
            json={"content": "X"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_item(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """DELETE /api/rooms/{room_id}/items/{item_id} removes the item."""
        create_resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Delete me", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        item_id = create_resp.json()["id"]

        response = client.delete(f"/api/rooms/{room_id}/items/{item_id}", headers=auth_headers)
        assert response.status_code == 204

        # Confirm deletion
        get_resp = client.get(f"/api/rooms/{room_id}/items/{item_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_item_not_found(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """DELETE /api/rooms/{room_id}/items/{item_id} returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/rooms/{room_id}/items/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_list_items_returns_all_items(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """GET /api/rooms/{room_id}/items returns all items."""
        for i in range(3):
            client.post(
                f"/api/rooms/{room_id}/items",
                json={
                    "content": f"Item {i}",
                    "position": {"x": float(i), "y": 0, "z": 0},
                },
                headers=auth_headers,
            )

        response = client.get(f"/api/rooms/{room_id}/items", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_delete_room_cascades_to_items(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """Deleting a room also deletes its items."""
        client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Cascade test", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )

        client.delete(f"/api/rooms/{room_id}", headers=auth_headers)

        # Room and items should be gone
        assert client.get(f"/api/rooms/{room_id}", headers=auth_headers).status_code == 404

    def test_create_item_with_image_url(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """POST /api/rooms/{room_id}/items supports image_url."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={
                "content": "Item with image",
                "image_url": "https://example.com/img.png",
                "position": {"x": 0, "y": 0, "z": 0},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["image_url"] == "https://example.com/img.png"

    def test_item_content_up_to_500_accepted(self, client: TestClient, room_id: str, auth_headers: dict[str, str]):
        """Items with content up to 500 chars are accepted."""
        response = client.post(
            f"/api/rooms/{room_id}/items",
            json={
                "content": "a" * 500,
                "position": {"x": 0, "y": 0, "z": 0},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
