"""
Security utilities for authentication and authorization.

Provides password hashing and JWT token utilities.
Note: Primary authentication is handled by Supabase Auth.
These utilities are for additional backend security if needed.
"""

import os
from datetime import datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Note:
        bcrypt has a maximum password length of 72 bytes.
        Passwords longer than 72 bytes are truncated.
    """
    # bcrypt requires bytes and has 72-byte limit
    password_bytes = password.encode("utf-8")
    # Truncate to bcrypt's 72-byte maximum
    password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches hash

    Note:
        bcrypt has a maximum password length of 72 bytes.
        Passwords are truncated to match the hash behavior.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        # Truncate to bcrypt's 72-byte maximum (must match hash_password)
        password_bytes = password_bytes[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (default: ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_supabase_jwt(token: str) -> dict[str, Any] | None:
    """
    Verify a Supabase JWT token.

    Supabase uses JWT tokens for authentication. This function verifies
    the token signature and extracts the user information.

    Args:
        token: Supabase JWT token

    Returns:
        Decoded token payload or None if invalid

    Note:
        In production, you should use Supabase's JWT secret from environment variables.
        The secret is available in your Supabase project settings under API > JWT Secret.
    """
    supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", SECRET_KEY)

    try:
        return jwt.decode(token, supabase_jwt_secret, algorithms=[ALGORITHM])
    except JWTError:
        # Fallback to default secret to maintain compatibility with tokens
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return None
