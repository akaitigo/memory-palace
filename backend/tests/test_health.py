"""Health check endpoint tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_health_check_returns_ok(client: TestClient):
    """Health endpoint returns 200 with status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "memory-palace"


def test_health_check_invalid_method(client: TestClient):
    """Health endpoint rejects POST requests with 405."""
    response = client.post("/api/health")
    assert response.status_code == 405
