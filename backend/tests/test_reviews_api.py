"""Tests for Review API endpoints (review-queue, review, stats)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from memory_palace.models.memory_item import MemoryItem

# Use the shared conftest fixtures: client, auth_headers, db_session, test_user


@pytest.fixture
def room_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    """Create a room and return its ID."""
    resp = client.post("/api/rooms", json={"name": "Review Test Room"}, headers=auth_headers)
    return resp.json()["id"]


@pytest.fixture
def item_id(client: TestClient, room_id: str, auth_headers: dict[str, str]) -> str:
    """Create a memory item and return its ID."""
    resp = client.post(
        f"/api/rooms/{room_id}/items",
        json={
            "content": "The capital of Japan is Tokyo",
            "position": {"x": 1.0, "y": 0.0, "z": 2.0},
        },
        headers=auth_headers,
    )
    return resp.json()["id"]


# =============================================================================
# Review Queue tests
# =============================================================================


class TestReviewQueue:
    """Tests for GET /api/rooms/{room_id}/review-queue."""

    def test_empty_room_returns_empty_queue(self, client, room_id, auth_headers):
        """Empty room has no items to review."""
        response = client.get(f"/api/rooms/{room_id}/review-queue", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_new_items_appear_in_queue(self, client, room_id, item_id, auth_headers):
        """Items that have never been reviewed appear in the queue."""
        response = client.get(f"/api/rooms/{room_id}/review-queue", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["id"] == item_id

    def test_multiple_new_items_in_queue(self, client, room_id, auth_headers):
        """All new items appear in the queue."""
        for i in range(3):
            client.post(
                f"/api/rooms/{room_id}/items",
                json={
                    "content": f"Item {i}",
                    "position": {"x": float(i), "y": 0, "z": 0},
                },
                headers=auth_headers,
            )

        response = client.get(f"/api/rooms/{room_id}/review-queue", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_reviewed_item_not_in_queue_immediately(self, client, room_id, item_id, auth_headers):
        """An item just reviewed with q=5 should not be in the queue immediately."""
        # Review the item
        client.post(
            f"/api/rooms/{room_id}/review",
            json={
                "memory_item_id": item_id,
                "quality": 5,
                "response_time_ms": 1000,
            },
            headers=auth_headers,
        )

        response = client.get(f"/api/rooms/{room_id}/review-queue", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_queue_nonexistent_room_404(self, client, auth_headers):
        """Queue for a nonexistent room returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{fake_id}/review-queue", headers=auth_headers)
        assert response.status_code == 404

    def test_overdue_items_appear_in_queue(self, client, room_id, db_session, auth_headers):
        """Items past their review interval appear in the queue."""
        # Create an item and manually set it as overdue in the DB
        resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={
                "content": "Overdue item",
                "position": {"x": 0, "y": 0, "z": 0},
            },
            headers=auth_headers,
        )
        item_id = resp.json()["id"]

        # Directly update the DB to make it overdue
        item = db_session.query(MemoryItem).filter_by(id=uuid.UUID(item_id)).first()
        item.last_reviewed_at = datetime.now(tz=UTC) - timedelta(days=10)
        item.interval = 1
        item.repetitions = 1
        db_session.commit()
        db_session.close()

        response = client.get(f"/api/rooms/{room_id}/review-queue", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["id"] == item_id


# =============================================================================
# Review Recording tests
# =============================================================================


class TestReviewRecording:
    """Tests for POST /api/rooms/{room_id}/review."""

    def test_record_review_success(self, client, room_id, item_id, auth_headers):
        """Successfully record a review and get a review record back."""
        response = client.post(
            f"/api/rooms/{room_id}/review",
            json={
                "memory_item_id": item_id,
                "quality": 5,
                "response_time_ms": 1200,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["quality"] == 5
        assert data["response_time_ms"] == 1200
        assert data["memory_item_id"] == item_id
        assert "id" in data
        assert "session_id" in data
        assert "reviewed_at" in data

    def test_review_updates_sm2_parameters(self, client, room_id, item_id, auth_headers):
        """After review, SM-2 parameters on the item are updated."""
        # Review with quality=5
        client.post(
            f"/api/rooms/{room_id}/review",
            json={
                "memory_item_id": item_id,
                "quality": 5,
                "response_time_ms": 800,
            },
            headers=auth_headers,
        )

        # Check the item's updated parameters
        item_resp = client.get(f"/api/rooms/{room_id}/items/{item_id}", headers=auth_headers)
        item_data = item_resp.json()
        assert item_data["repetitions"] == 1
        assert item_data["interval"] == 1
        assert item_data["ease_factor"] > 2.5  # Increased for q=5
        assert item_data["last_reviewed_at"] is not None

    def test_review_quality_0_resets(self, client, room_id, item_id, auth_headers):
        """Quality=0 resets repetitions and interval."""
        # First review with q=5
        client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": 5, "response_time_ms": 500},
            headers=auth_headers,
        )
        # Second review with q=0
        client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": 0, "response_time_ms": 5000},
            headers=auth_headers,
        )

        item_resp = client.get(f"/api/rooms/{room_id}/items/{item_id}", headers=auth_headers)
        item_data = item_resp.json()
        assert item_data["repetitions"] == 0
        assert item_data["interval"] == 1

    def test_review_all_quality_levels(self, client, room_id, auth_headers):
        """Each quality level (0-5) is accepted."""
        for q in range(6):
            resp = client.post(
                f"/api/rooms/{room_id}/items",
                json={"content": f"Q{q} item", "position": {"x": float(q), "y": 0, "z": 0}},
                headers=auth_headers,
            )
            iid = resp.json()["id"]
            review_resp = client.post(
                f"/api/rooms/{room_id}/review",
                json={"memory_item_id": iid, "quality": q, "response_time_ms": 1000},
                headers=auth_headers,
            )
            assert review_resp.status_code == 201
            assert review_resp.json()["quality"] == q

    def test_review_nonexistent_room_404(self, client, item_id, auth_headers):
        """Review with nonexistent room returns 404."""
        fake_room = str(uuid.uuid4())
        response = client.post(
            f"/api/rooms/{fake_room}/review",
            json={"memory_item_id": item_id, "quality": 3, "response_time_ms": 1000},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_review_nonexistent_item_404(self, client, room_id, auth_headers):
        """Review with nonexistent item returns 404."""
        fake_item = str(uuid.uuid4())
        response = client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": fake_item, "quality": 3, "response_time_ms": 1000},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_review_invalid_quality_rejected(self, client, room_id, item_id, auth_headers):
        """Quality outside 0-5 is rejected with 422."""
        response = client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": 6, "response_time_ms": 1000},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_review_negative_quality_rejected(self, client, room_id, item_id, auth_headers):
        """Negative quality is rejected with 422."""
        response = client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": -1, "response_time_ms": 1000},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_review_response_time_zero_rejected(self, client, room_id, item_id, auth_headers):
        """response_time_ms of 0 is rejected (must be > 0)."""
        response = client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": 3, "response_time_ms": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_review_response_time_exceeds_max_rejected(self, client, room_id, item_id, auth_headers):
        """response_time_ms exceeding 300000 is rejected."""
        response = client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": 3, "response_time_ms": 300001},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_review_response_time_max_accepted(self, client, room_id, item_id, auth_headers):
        """response_time_ms of exactly 300000 is accepted."""
        response = client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": 3, "response_time_ms": 300000},
            headers=auth_headers,
        )
        assert response.status_code == 201


# =============================================================================
# Stats tests
# =============================================================================


class TestRoomStats:
    """Tests for GET /api/rooms/{room_id}/stats."""

    def test_stats_empty_room(self, client, room_id, auth_headers):
        """Stats for an empty room."""
        response = client.get(f"/api/rooms/{room_id}/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 0
        assert data["reviewed_items"] == 0
        assert data["mastered_items"] == 0
        assert data["learning_items"] == 0
        assert data["new_items"] == 0
        assert data["total_reviews"] == 0
        assert data["reviews_today"] == 0

    def test_stats_with_new_items(self, client, room_id, item_id, auth_headers):
        """Stats show new items correctly."""
        response = client.get(f"/api/rooms/{room_id}/stats", headers=auth_headers)
        data = response.json()
        assert data["total_items"] == 1
        assert data["new_items"] == 1
        assert data["reviewed_items"] == 0

    def test_stats_after_review(self, client, room_id, item_id, auth_headers):
        """Stats update after a review."""
        client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": item_id, "quality": 4, "response_time_ms": 1500},
            headers=auth_headers,
        )

        response = client.get(f"/api/rooms/{room_id}/stats", headers=auth_headers)
        data = response.json()
        assert data["total_items"] == 1
        assert data["reviewed_items"] == 1
        assert data["new_items"] == 0
        assert data["learning_items"] == 1  # interval < 21
        assert data["total_reviews"] == 1
        assert data["reviews_today"] == 1
        assert data["average_quality"] == 4.0

    def test_stats_multiple_reviews(self, client, room_id, auth_headers):
        """Stats accumulate across multiple reviews."""
        # Create 3 items and review each
        item_ids = []
        for i in range(3):
            resp = client.post(
                f"/api/rooms/{room_id}/items",
                json={"content": f"Stats item {i}", "position": {"x": float(i), "y": 0, "z": 0}},
                headers=auth_headers,
            )
            item_ids.append(resp.json()["id"])

        for iid in item_ids:
            client.post(
                f"/api/rooms/{room_id}/review",
                json={"memory_item_id": iid, "quality": 5, "response_time_ms": 500},
                headers=auth_headers,
            )

        response = client.get(f"/api/rooms/{room_id}/stats", headers=auth_headers)
        data = response.json()
        assert data["total_items"] == 3
        assert data["reviewed_items"] == 3
        assert data["total_reviews"] == 3
        assert data["average_quality"] == 5.0

    def test_stats_nonexistent_room_404(self, client, auth_headers):
        """Stats for nonexistent room returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{fake_id}/stats", headers=auth_headers)
        assert response.status_code == 404

    def test_stats_mastered_items(self, client, room_id, db_session, auth_headers):
        """Items with interval >= 21 are counted as mastered."""
        resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Mastered item", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        iid = resp.json()["id"]

        # Manually set interval >= 21 and mark as reviewed
        item = db_session.query(MemoryItem).filter_by(id=uuid.UUID(iid)).first()
        item.interval = 30
        item.repetitions = 5
        item.last_reviewed_at = datetime.now(tz=UTC)
        db_session.commit()
        db_session.close()

        response = client.get(f"/api/rooms/{room_id}/stats", headers=auth_headers)
        data = response.json()
        assert data["mastered_items"] == 1
        assert data["learning_items"] == 0
