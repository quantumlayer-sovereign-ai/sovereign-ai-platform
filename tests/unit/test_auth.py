"""
Unit tests for JWT authentication module
"""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# Set up test environment
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["DEV_MODE"] = "true"

from api.auth import (
    JWTBearer,
    OptionalJWTBearer,
    TokenData,
    UserContext,
    create_access_token,
    create_dev_token,
    decode_token,
    get_password_hash,
    validate_api_key,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing utilities"""

    @pytest.mark.skip(reason="passlib/bcrypt version incompatibility - bug detection uses 72+ byte password")
    def test_hash_and_verify_password(self):
        """Test password hashing and verification"""
        password = "test123"  # Short password to avoid bcrypt issues
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)

    @pytest.mark.skip(reason="passlib/bcrypt version incompatibility - bug detection uses 72+ byte password")
    def test_verify_wrong_password_fails(self):
        """Test that wrong password fails verification"""
        password = "correct"  # Short password to avoid bcrypt issues
        wrong_password = "wrong"
        hashed = get_password_hash(password)

        assert not verify_password(wrong_password, hashed)


class TestTokenCreation:
    """Tests for JWT token creation"""

    def test_create_access_token(self):
        """Test creating a valid access token"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test creating token with custom expiration"""
        data = {"sub": "user123"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)

        decoded = decode_token(token)
        assert decoded.user_id == "user123"

    def test_create_dev_token(self):
        """Test dev token creation in dev mode"""
        result = create_dev_token("test-user", "test@example.com")

        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert len(result["access_token"]) > 0


class TestTokenDecoding:
    """Tests for JWT token decoding"""

    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        data = {"sub": "user123", "email": "test@example.com", "roles": ["admin"]}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert decoded.user_id == "user123"
        assert decoded.email == "test@example.com"
        assert "admin" in decoded.roles

    def test_decode_token_missing_sub(self):
        """Test that token without 'sub' raises error"""
        data = {"email": "test@example.com"}  # Missing 'sub'
        token = create_access_token(data)

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)

        assert exc_info.value.status_code == 401

    def test_decode_invalid_token(self):
        """Test that invalid token raises error"""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid-token")

        assert exc_info.value.status_code == 401


class TestAPIKeyValidation:
    """Tests for API key validation"""

    def test_validate_api_key_empty_keys(self):
        """Test API key validation with no configured keys"""
        # By default, no keys are configured
        assert not validate_api_key("any-key")

    @patch.dict(os.environ, {"SERVICE_API_KEYS": "key1,key2,key3"})
    def test_validate_valid_api_key(self):
        """Test validating a valid API key"""
        # Need to reimport to pick up new env var
        from api import auth
        auth.SERVICE_API_KEYS = set(os.environ.get("SERVICE_API_KEYS", "").split(",")) - {""}

        assert auth.validate_api_key("key1")
        assert auth.validate_api_key("key2")

    @patch.dict(os.environ, {"SERVICE_API_KEYS": "key1,key2"})
    def test_validate_invalid_api_key(self):
        """Test validating an invalid API key"""
        from api import auth
        auth.SERVICE_API_KEYS = set(os.environ.get("SERVICE_API_KEYS", "").split(",")) - {""}

        assert not auth.validate_api_key("invalid-key")


class TestJWTBearer:
    """Tests for JWTBearer dependency"""

    @pytest.mark.asyncio
    async def test_jwt_bearer_with_valid_token(self):
        """Test JWTBearer accepts valid token"""
        token_data = {"sub": "user123", "email": "test@example.com", "roles": ["user"]}
        token = create_access_token(token_data)

        request = MagicMock()
        request.headers.get.return_value = None  # No API key

        # Mock the parent class call
        bearer = JWTBearer()
        credentials = MagicMock()
        credentials.scheme = "Bearer"
        credentials.credentials = token

        with patch.object(bearer.__class__.__bases__[0], '__call__', new_callable=AsyncMock) as mock_parent:
            mock_parent.return_value = credentials
            result = await bearer(request)

        assert result.user_id == "user123"
        assert result.email == "test@example.com"
        assert not result.is_service_account

    @pytest.mark.asyncio
    async def test_jwt_bearer_with_api_key(self):
        """Test JWTBearer accepts valid API key"""
        request = MagicMock()
        request.headers.get.return_value = "valid-key"

        bearer = JWTBearer()

        with patch("api.auth.validate_api_key", return_value=True):
            result = await bearer(request)

        assert result.user_id == "service-account"
        assert result.is_service_account
        assert "service" in result.roles

    @pytest.mark.asyncio
    async def test_jwt_bearer_rejects_invalid_api_key(self):
        """Test JWTBearer rejects invalid API key"""
        request = MagicMock()
        request.headers.get.return_value = "invalid-key"

        bearer = JWTBearer()

        with patch("api.auth.validate_api_key", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await bearer(request)

        assert exc_info.value.status_code == 401


class TestOptionalJWTBearer:
    """Tests for OptionalJWTBearer dependency"""

    @pytest.mark.asyncio
    async def test_optional_jwt_bearer_returns_none_on_missing_auth(self):
        """Test OptionalJWTBearer returns None when no auth provided"""
        request = MagicMock()
        request.headers.get.return_value = None  # No API key

        bearer = OptionalJWTBearer()

        with patch.object(bearer.__class__.__bases__[0].__bases__[0], '__call__', new_callable=AsyncMock) as mock_parent:
            mock_parent.return_value = None
            result = await bearer(request)

        assert result is None


class TestUserContext:
    """Tests for UserContext model"""

    def test_user_context_creation(self):
        """Test creating a UserContext"""
        context = UserContext(
            user_id="user123",
            email="test@example.com",
            roles=["admin", "user"],
            is_service_account=False
        )

        assert context.user_id == "user123"
        assert context.email == "test@example.com"
        assert len(context.roles) == 2
        assert not context.is_service_account

    def test_user_context_defaults(self):
        """Test UserContext default values"""
        context = UserContext(user_id="user123")

        assert context.user_id == "user123"
        assert context.email is None
        assert context.roles == []
        assert not context.is_service_account
