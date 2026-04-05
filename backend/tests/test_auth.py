"""Tests for authentication API endpoints (register, login, me)."""

from __future__ import annotations

from fastapi.testclient import TestClient

# Use the shared conftest fixtures: client, auth_headers, db_session, test_user


class TestRegister:
    """Tests for POST /api/auth/register."""

    def test_register_success(self, client: TestClient):
        """Successful registration returns a JWT token."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, client: TestClient, test_user):
        """Registering with an existing username returns 409."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "different@example.com",
                "password": "password12345",
            },
        )
        assert response.status_code == 409
        assert "Username already taken" in response.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Registering with an existing email returns 409."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",
                "password": "password12345",
            },
        )
        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    def test_register_short_password(self, client: TestClient):
        """Password shorter than 8 chars is rejected."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "shortpw",
                "email": "short@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_register_short_username(self, client: TestClient):
        """Username shorter than 3 chars is rejected."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "ab",
                "email": "ab@example.com",
                "password": "password12345",
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """Invalid email format is rejected."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "invalidemail",
                "email": "not-an-email",
                "password": "password12345",
            },
        )
        assert response.status_code == 422

    def test_register_token_works(self, client: TestClient):
        """Token returned from register can be used to access /api/auth/me."""
        reg_resp = client.post(
            "/api/auth/register",
            json={
                "username": "tokentest",
                "email": "token@example.com",
                "password": "securepassword123",
            },
        )
        token = reg_resp.json()["access_token"]

        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "tokentest"


class TestLogin:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, client: TestClient, test_user):
        """Successful login returns a JWT token."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Wrong password returns 401."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Login with nonexistent user returns 401."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password12345",
            },
        )
        assert response.status_code == 401

    def test_login_token_works(self, client: TestClient, test_user):
        """Token returned from login can be used to access protected endpoints."""
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword123"},
        )
        token = login_resp.json()["access_token"]

        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "testuser"
        assert me_resp.json()["email"] == "test@example.com"


class TestMe:
    """Tests for GET /api/auth/me."""

    def test_me_authenticated(self, client: TestClient, auth_headers):
        """Authenticated user can access /api/auth/me."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_me_unauthenticated(self, client: TestClient):
        """Unauthenticated request to /api/auth/me returns 401 or 403."""
        response = client.get("/api/auth/me")
        assert response.status_code in (401, 403)

    def test_me_invalid_token(self, client: TestClient):
        """Invalid token returns 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert response.status_code == 401
