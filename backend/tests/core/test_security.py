"""
Tests for security utilities.

Covers:
- Password hashing and verification
- JWT token creation and decoding
- Supabase JWT verification
- Edge cases and error handling
"""

import os
from datetime import timedelta
from unittest.mock import patch

import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    verify_supabase_jwt,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing produces valid hash."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_different_hash(self):
        """Test that same password produces different hashes."""
        password = "test_password_123"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)

        # bcrypt includes salt, so hashes should be different
        assert hashed1 != hashed2

        # But both should verify correctly
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True

    def test_hash_password_empty_string(self):
        """Test hashing empty password."""
        hashed = hash_password("")
        assert len(hashed) > 0
        assert verify_password("", hashed) is True

    def test_hash_password_special_characters(self):
        """Test hashing password with special characters."""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_unicode(self):
        """Test hashing password with unicode characters."""
        password = "密码123🔒"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJWTToken:
    """Test JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test creating a JWT access token."""
        data = {"user_id": "123", "email": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        """Test decoding a valid JWT token."""
        data = {"user_id": "123", "email": "test@example.com"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["user_id"] == "123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_decode_access_token_invalid(self):
        """Test decoding an invalid JWT token."""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_decode_access_token_expired(self):
        """Test decoding an expired JWT token."""
        data = {"user_id": "123"}
        # Create token with very short expiration
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # Token should be invalid (expired)
        decoded = decode_access_token(token)
        assert decoded is None

    def test_create_access_token_with_custom_expiration(self):
        """Test creating token with custom expiration."""
        data = {"user_id": "123"}
        token = create_access_token(data, expires_delta=timedelta(hours=2))

        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_token_contains_expiration(self):
        """Test that token contains expiration claim."""
        data = {"user_id": "123"}
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)

    def test_token_preserves_custom_data(self):
        """Test that custom data is preserved in token."""
        data = {
            "user_id": "123",
            "role": "admin",
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["user_id"] == "123"
        assert decoded["role"] == "admin"
        assert decoded["permissions"] == ["read", "write"]


class TestSupabaseJWT:
    """Test Supabase JWT verification."""

    def test_verify_supabase_jwt_with_custom_secret(self):
        """Test Supabase JWT verification with custom secret."""
        from jose import jwt
        from app.core.security import ALGORITHM

        # Create a valid Supabase JWT with proper claims
        secret = "test-supabase-jwt-secret"
        supabase_url = "https://test.supabase.co"
        data = {
            "sub": "user-uuid-123",
            "aud": "authenticated",
            "iss": f"{supabase_url}/auth/v1",  # Required: issuer claim
            "role": "authenticated",
            "email": "test@example.com",
        }

        # Create token with the secret
        token = jwt.encode(data, secret, algorithm=ALGORITHM)

        # Mock os.getenv in the security module where it's actually called
        with patch("app.core.security.os.getenv") as mock_getenv:
            def getenv_side_effect(key, default=""):
                if key == "SUPABASE_JWT_SECRET":
                    return secret
                elif key == "SUPABASE_URL":
                    return supabase_url
                return default

            mock_getenv.side_effect = getenv_side_effect

            # Verify with Supabase function
            decoded = verify_supabase_jwt(token)

            # Should decode successfully
            assert decoded is not None
            assert decoded["sub"] == "user-uuid-123"
            assert decoded["aud"] == "authenticated"
            assert decoded["iss"] == f"{supabase_url}/auth/v1"

    def test_verify_supabase_jwt_invalid_token(self):
        """Test Supabase JWT verification with invalid token."""
        invalid_token = "invalid.token.here"

        # Mock os.getenv to provide a secret (even though token is invalid)
        with patch("app.core.security.os.getenv") as mock_getenv:
            def getenv_side_effect(key, default=""):
                if key == "SUPABASE_JWT_SECRET":
                    return "test-secret"
                elif key == "SUPABASE_URL":
                    return "https://test.supabase.co"
                return default

            mock_getenv.side_effect = getenv_side_effect

            decoded = verify_supabase_jwt(invalid_token)
            assert decoded is None

    def test_verify_supabase_jwt_uses_default_secret(self):
        """Test that Supabase JWT returns None if secret not configured."""
        from jose import jwt
        from app.core.security import ALGORITHM

        data = {"sub": "123", "aud": "authenticated"}
        token = jwt.encode(data, "any-secret", algorithm=ALGORITHM)

        # Mock os.getenv to return empty string (secret not configured)
        with patch("app.core.security.os.getenv") as mock_getenv:
            mock_getenv.return_value = ""

            # Should return None when SUPABASE_JWT_SECRET not set
            decoded = verify_supabase_jwt(token)
            assert decoded is None


class TestSecurityEdgeCases:
    """Test edge cases and error scenarios."""

    def test_hash_password_very_long(self):
        """Test hashing very long password."""
        long_password = "a" * 1000
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed) is True

    def test_verify_password_with_wrong_hash_format(self):
        """Test verification with incorrectly formatted hash."""
        password = "test_password"
        # This is not a valid bcrypt hash
        invalid_hash = "not_a_valid_hash"

        # Should return False, not raise exception
        result = verify_password(password, invalid_hash)
        assert result is False

    def test_token_with_empty_data(self):
        """Test creating token with empty data."""
        token = create_access_token({})
        decoded = decode_access_token(token)

        assert decoded is not None
        assert "exp" in decoded

    def test_token_with_nested_data(self):
        """Test creating token with nested data structures."""
        data = {
            "user": {
                "id": "123",
                "profile": {"name": "Test User"},
            },
        }
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["user"]["id"] == "123"

    def test_multiple_tokens_different_expiration(self):
        """Test creating multiple tokens with different expirations."""
        data = {"user_id": "123"}

        token1 = create_access_token(data, expires_delta=timedelta(minutes=30))
        token2 = create_access_token(data, expires_delta=timedelta(hours=2))

        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)

        assert decoded1 is not None
        assert decoded2 is not None
        # Token2 should expire later
        assert decoded2["exp"] > decoded1["exp"]

