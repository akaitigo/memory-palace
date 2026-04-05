"""Tests for daily stats and forgetting curve API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

# Use the shared conftest fixtures: client, auth_headers, db_session, test_user


@pytest.fixture
def room_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    """Create a room and return its ID."""
    resp = client.post("/api/rooms", json={"name": "Stats Test Room"}, headers=auth_headers)
    return resp.json()["id"]


@pytest.fixture
def items_with_reviews(client: TestClient, room_id: str, auth_headers: dict[str, str]) -> list[str]:
    """Create items and record reviews, return item IDs."""
    item_ids = []
    for i in range(3):
        resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": f"Test item {i}", "position": {"x": float(i), "y": 0, "z": 0}},
            headers=auth_headers,
        )
        item_ids.append(resp.json()["id"])

    # Record reviews for each item
    for iid in item_ids:
        client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": iid, "quality": 4, "response_time_ms": 1000},
            headers=auth_headers,
        )

    return item_ids


# =============================================================================
# Daily Stats tests
# =============================================================================


class TestDailyStats:
    """Tests for GET /api/rooms/{room_id}/stats/daily."""

    def test_daily_stats_empty_room(self, client, room_id, auth_headers):
        """Empty room returns entries with zero counts."""
        response = client.get(f"/api/rooms/{room_id}/stats/daily?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        # Should have entries for each day in range
        assert len(data["entries"]) >= 7
        # All entries should have 0 reviews
        for entry in data["entries"]:
            assert entry["review_count"] == 0
            assert entry["average_quality"] is None
            assert entry["correct_rate"] is None

    def test_daily_stats_with_reviews(self, client, room_id, items_with_reviews, auth_headers):
        """Daily stats reflect recorded reviews."""
        response = client.get(f"/api/rooms/{room_id}/stats/daily?days=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Find today's entry
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        today_entries = [e for e in data["entries"] if e["date"] == today]
        assert len(today_entries) == 1
        entry = today_entries[0]
        assert entry["review_count"] == 3
        assert entry["average_quality"] == 4.0
        assert entry["correct_rate"] == 100.0

    def test_daily_stats_default_days(self, client, room_id, auth_headers):
        """Default is 30 days."""
        response = client.get(f"/api/rooms/{room_id}/stats/daily", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) >= 30

    def test_daily_stats_max_days_365(self, client, room_id, auth_headers):
        """Days parameter max is 365."""
        response = client.get(f"/api/rooms/{room_id}/stats/daily?days=365", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) >= 365

    def test_daily_stats_invalid_days_rejected(self, client, room_id, auth_headers):
        """Days > 365 is rejected."""
        response = client.get(f"/api/rooms/{room_id}/stats/daily?days=366", headers=auth_headers)
        assert response.status_code == 422

    def test_daily_stats_zero_days_rejected(self, client, room_id, auth_headers):
        """Days = 0 is rejected."""
        response = client.get(f"/api/rooms/{room_id}/stats/daily?days=0", headers=auth_headers)
        assert response.status_code == 422

    def test_daily_stats_nonexistent_room_404(self, client, auth_headers):
        """Daily stats for nonexistent room returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{fake_id}/stats/daily", headers=auth_headers)
        assert response.status_code == 404

    def test_daily_stats_correct_rate_calculation(self, client, room_id, auth_headers):
        """Correct rate is calculated correctly: quality >= 3 is correct."""
        # Create items with mixed quality scores
        for i, q in enumerate([0, 1, 2, 3, 4, 5]):
            resp = client.post(
                f"/api/rooms/{room_id}/items",
                json={"content": f"Q{q} item", "position": {"x": float(i + 10), "y": 0, "z": 0}},
                headers=auth_headers,
            )
            iid = resp.json()["id"]
            client.post(
                f"/api/rooms/{room_id}/review",
                json={"memory_item_id": iid, "quality": q, "response_time_ms": 1000},
                headers=auth_headers,
            )

        response = client.get(f"/api/rooms/{room_id}/stats/daily?days=1", headers=auth_headers)
        data = response.json()
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        today_entry = next(e for e in data["entries"] if e["date"] == today)
        # 3 out of 6 are correct (quality 3, 4, 5)
        assert today_entry["correct_rate"] == 50.0

    def test_daily_stats_entries_have_date_format(self, client, room_id, auth_headers):
        """Entries have YYYY-MM-DD date format."""
        response = client.get(f"/api/rooms/{room_id}/stats/daily?days=3", headers=auth_headers)
        data = response.json()
        for entry in data["entries"]:
            # Validate date format
            datetime.strptime(entry["date"], "%Y-%m-%d")  # noqa: DTZ007


# =============================================================================
# Forgetting Curve tests
# =============================================================================


class TestForgettingCurve:
    """Tests for GET /api/rooms/{room_id}/stats/forgetting-curve."""

    def test_forgetting_curve_empty_room(self, client, room_id, auth_headers):
        """Empty room returns empty items list."""
        response = client.get(f"/api/rooms/{room_id}/stats/forgetting-curve", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_forgetting_curve_unreviewed_items_excluded(self, client, room_id, auth_headers):
        """Items that have never been reviewed are excluded."""
        client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Unreviewed item", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        response = client.get(f"/api/rooms/{room_id}/stats/forgetting-curve", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_forgetting_curve_with_reviewed_items(self, client, room_id, items_with_reviews, auth_headers):
        """Reviewed items have forgetting curve data."""
        response = client.get(f"/api/rooms/{room_id}/stats/forgetting-curve", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3

        for item in data["items"]:
            assert "item_id" in item
            assert "content" in item
            assert "stability" in item
            assert item["stability"] > 0
            assert len(item["curve"]) == 21  # 20 points + 1 for t=0

            # First point should have retention close to 1.0
            assert item["curve"][0]["days_since_review"] == 0
            assert item["curve"][0]["retention"] == 1.0

            # Last point should have retention < 1.0
            last_point = item["curve"][-1]
            assert last_point["retention"] < 1.0
            assert last_point["retention"] > 0

    def test_forgetting_curve_retention_decreases(self, client, room_id, items_with_reviews, auth_headers):
        """Retention should decrease over time (monotonically)."""
        response = client.get(f"/api/rooms/{room_id}/stats/forgetting-curve", headers=auth_headers)
        data = response.json()
        for item in data["items"]:
            curve = item["curve"]
            for i in range(1, len(curve)):
                assert curve[i]["retention"] <= curve[i - 1]["retention"]

    def test_forgetting_curve_nonexistent_room_404(self, client, auth_headers):
        """Forgetting curve for nonexistent room returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/rooms/{fake_id}/stats/forgetting-curve", headers=auth_headers)
        assert response.status_code == 404

    def test_forgetting_curve_content_truncated(self, client, room_id, auth_headers):
        """Content longer than 50 chars is truncated."""
        long_content = "A" * 100
        resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": long_content, "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        iid = resp.json()["id"]
        client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": iid, "quality": 5, "response_time_ms": 500},
            headers=auth_headers,
        )

        response = client.get(f"/api/rooms/{room_id}/stats/forgetting-curve", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 1
        assert len(data["items"][0]["content"]) == 50

    def test_forgetting_curve_stability_formula(self, client, room_id, auth_headers):
        """Stability should equal interval * ease_factor."""
        resp = client.post(
            f"/api/rooms/{room_id}/items",
            json={"content": "Stability test", "position": {"x": 0, "y": 0, "z": 0}},
            headers=auth_headers,
        )
        iid = resp.json()["id"]
        # Review with quality 5
        client.post(
            f"/api/rooms/{room_id}/review",
            json={"memory_item_id": iid, "quality": 5, "response_time_ms": 500},
            headers=auth_headers,
        )

        # Get updated item to check parameters
        item_resp = client.get(f"/api/rooms/{room_id}/items/{iid}", headers=auth_headers)
        item = item_resp.json()

        response = client.get(f"/api/rooms/{room_id}/stats/forgetting-curve", headers=auth_headers)
        data = response.json()
        curve_item = data["items"][0]

        expected_stability = round(item["interval"] * item["ease_factor"], 2)
        assert curve_item["stability"] == expected_stability

    def test_forgetting_curve_max_20_items(self, client, room_id, auth_headers):
        """At most 20 items are returned."""
        # Create and review 25 items
        for i in range(25):
            resp = client.post(
                f"/api/rooms/{room_id}/items",
                json={"content": f"Item {i}", "position": {"x": float(i % 10), "y": 0, "z": float(i // 10)}},
                headers=auth_headers,
            )
            iid = resp.json()["id"]
            client.post(
                f"/api/rooms/{room_id}/review",
                json={"memory_item_id": iid, "quality": 4, "response_time_ms": 500},
                headers=auth_headers,
            )

        response = client.get(f"/api/rooms/{room_id}/stats/forgetting-curve", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) <= 20
