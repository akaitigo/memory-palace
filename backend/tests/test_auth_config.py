"""Tests for cached JWT configuration (secret and token expiry)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import jwt
import pytest

from memory_palace.auth import (
    _ALGORITHM,
    _get_access_token_expire_minutes,
    _get_jwt_secret,
    create_access_token,
)


@pytest.fixture(autouse=True)
def _clear_auth_caches():
    """Reset cached JWT config before and after each test to avoid leakage."""
    _get_jwt_secret.cache_clear()
    _get_access_token_expire_minutes.cache_clear()
    yield
    _get_jwt_secret.cache_clear()
    _get_access_token_expire_minutes.cache_clear()


class TestJwtSecretCaching:
    """Tests for the cached _get_jwt_secret helper."""

    def test_reads_secret_from_env(self):
        """The secret is read from JWT_SECRET."""
        with patch.dict("os.environ", {"JWT_SECRET": "secret-one"}):
            assert _get_jwt_secret() == "secret-one"

    def test_value_is_cached_until_cleared(self):
        """The secret is cached and a later env change is ignored until cache_clear."""
        with patch.dict("os.environ", {"JWT_SECRET": "secret-one"}):
            assert _get_jwt_secret() == "secret-one"
        with patch.dict("os.environ", {"JWT_SECRET": "secret-two"}):
            # Still the cached value from the first read.
            assert _get_jwt_secret() == "secret-one"
            _get_jwt_secret.cache_clear()
            # After clearing, the current environment value is read.
            assert _get_jwt_secret() == "secret-two"

    def test_raises_when_unset(self):
        """A missing JWT_SECRET raises RuntimeError and is not cached."""
        with patch.dict("os.environ", {}, clear=True), pytest.raises(RuntimeError, match="JWT_SECRET"):
            _get_jwt_secret()

    def test_exception_not_cached(self):
        """After a failed read, setting the secret makes the next call succeed."""
        with patch.dict("os.environ", {}, clear=True), pytest.raises(RuntimeError, match="JWT_SECRET"):
            _get_jwt_secret()
        with patch.dict("os.environ", {"JWT_SECRET": "recovered"}):
            assert _get_jwt_secret() == "recovered"


class TestAccessTokenExpiry:
    """Tests for the cached _get_access_token_expire_minutes helper."""

    def test_default_is_sixty(self):
        """The default token lifetime is 60 minutes when unset."""
        with patch.dict("os.environ", {}, clear=True):
            assert _get_access_token_expire_minutes() == 60

    def test_custom_value_from_env(self):
        """JWT_EXPIRE_MINUTES overrides the default lifetime."""
        with patch.dict("os.environ", {"JWT_EXPIRE_MINUTES": "120"}):
            assert _get_access_token_expire_minutes() == 120

    def test_value_is_cached_until_cleared(self):
        """The expiry is cached and a later env change is ignored until cache_clear."""
        with patch.dict("os.environ", {"JWT_EXPIRE_MINUTES": "30"}):
            assert _get_access_token_expire_minutes() == 30
        with patch.dict("os.environ", {"JWT_EXPIRE_MINUTES": "90"}):
            assert _get_access_token_expire_minutes() == 30
            _get_access_token_expire_minutes.cache_clear()
            assert _get_access_token_expire_minutes() == 90

    def test_token_reflects_configured_expiry(self):
        """create_access_token applies the configured expiry to the token."""
        user_id = uuid.uuid4()
        secret = "cfg-secret-key-that-is-at-least-32-bytes-long"
        with patch.dict("os.environ", {"JWT_SECRET": secret, "JWT_EXPIRE_MINUTES": "5"}):
            token = create_access_token(user_id)
            payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
            assert payload["exp"] - payload["iat"] == 5 * 60
