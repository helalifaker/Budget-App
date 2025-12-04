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
    Verify a Supabase JWT token with proper issuer and audience validation.

    Supabase uses JWT tokens for authentication. This function verifies:
    - Token signature using SUPABASE_JWT_SECRET
    - Issuer claim (iss) matches Supabase auth endpoint
    - Audience claim (aud) is "authenticated"
    - Token expiration (exp)

    Args:
        token: Supabase JWT token

    Returns:
        Decoded token payload or None if invalid

    Note:
        In production, you should use Supabase's JWT secret from environment variables.
        The secret is available in your Supabase project settings under API > JWT Secret.
    """
    import logging
    logger = logging.getLogger(__name__)

    supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "").strip().strip('"').strip("'")
    supabase_url = os.getenv("SUPABASE_URL", "").strip().strip('"').strip("'")

    # Debug: Print env var status
    logger.info(
        f"JWT env present: {bool(supabase_jwt_secret)}, "
        f"secret length: {len(supabase_jwt_secret) if supabase_jwt_secret else 0}, "
        f"SUPABASE_URL: {supabase_url or 'NOT SET'}"
    )

    if not supabase_jwt_secret:
        logger.error(
            "SUPABASE_JWT_SECRET not configured. "
            "Get JWT secret from Supabase Dashboard > Settings > API > JWT Secret. "
            "Add it to backend/.env.local as: SUPABASE_JWT_SECRET=your-secret-here"
        )
        return None

    # Build issuer URL from SUPABASE_URL
    # Format: https://[project-id].supabase.co/auth/v1
    if supabase_url:
        # Remove trailing slash and append /auth/v1
        issuer = f"{supabase_url.rstrip('/')}/auth/v1"
        logger.debug(f"Using issuer from SUPABASE_URL: {issuer}")
    else:
        # Fallback: use default for project ssxwmxqvafesyldycqzy
        issuer = "https://ssxwmxqvafesyldycqzy.supabase.co/auth/v1"
        logger.warning(
            "SUPABASE_URL not set, using default issuer. "
            "Set SUPABASE_URL in backend/.env.local for proper issuer validation."
        )

    audience = "authenticated"
    algorithms = ["HS256"]

    # Debug: Decode token without verification to inspect claims
    try:
        header = jwt.get_unverified_header(token)
        payload_unverified = jwt.get_unverified_claims(token)
        logger.info(
            f"Token inspection (unverified): "
            f"alg={header.get('alg')}, "
            f"aud={payload_unverified.get('aud')}, "
            f"iss={payload_unverified.get('iss')}, "
            f"sub={payload_unverified.get('sub', 'N/A')[:20]}..."
        )
    except Exception as e:
        logger.warning(f"Failed to decode token for inspection: {e}")

    # Verify token with all checks
    try:
        payload = jwt.decode(
            token,
            supabase_jwt_secret,
            algorithms=algorithms,
            audience=audience,
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )
        user_id = payload.get("sub", "unknown")
        email = payload.get("email", "unknown")
        logger.info(
            f"✅ JWT verified successfully. User: {user_id}, Email: {email}, "
            f"Issuer: {payload.get('iss', 'N/A')}, Audience: {payload.get('aud', 'N/A')}"
        )
        return payload
    except JWTError as e:
        logger.error(
            f"❌ JWT verification failed: {repr(e)}. "
            f"Expected issuer: {issuer}, Expected audience: {audience}"
        )
        logger.debug(f"Token preview (first 50 chars): {token[:50]}...")
        return None
