"""Tests for application startup validation (JWT_SECRET, CORS, etc.)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from memory_palace.main import _validate_jwt_secret


class TestJwtSecretValidation:
    """Tests for JWT_SECRET startup validation."""

    def test_raises_when_jwt_secret_not_set(self):
        """Application should refuse to start if JWT_SECRET is missing."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit, match="JWT_SECRET"):
            _validate_jwt_secret()

    def test_raises_when_jwt_secret_empty(self):
        """Application should refuse to start if JWT_SECRET is empty string."""
        with patch.dict(os.environ, {"JWT_SECRET": ""}), pytest.raises(SystemExit, match="JWT_SECRET"):
            _validate_jwt_secret()

    def test_passes_when_jwt_secret_set(self):
        """Application should start normally when JWT_SECRET is configured."""
        with patch.dict(os.environ, {"JWT_SECRET": "a-valid-secret-key-for-testing"}):
            # Should not raise
            _validate_jwt_secret()


class TestCorsConfiguration:
    """Tests for CORS middleware configuration."""

    def test_patch_method_in_allow_methods(self):
        """CORS allow_methods should include PATCH for room/item updates."""
        # Verify PATCH is in allow_methods by creating an app with a known
        # CORS_ORIGINS and checking the preflight response.
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:5173"}):
            from memory_palace.main import create_app  # noqa: PLC0415

            test_app = create_app()
            with TestClient(test_app, raise_server_exceptions=False) as test_client:
                response = test_client.options(
                    "/api/rooms/test-id",
                    headers={
                        "Origin": "http://localhost:5173",
                        "Access-Control-Request-Method": "PATCH",
                    },
                )
                assert response.status_code == 200
                allow_methods = response.headers.get("access-control-allow-methods", "")
                assert "PATCH" in allow_methods
