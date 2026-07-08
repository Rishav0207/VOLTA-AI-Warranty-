"""Password hashing, JWT access tokens, and refresh tokens."""

import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import get_settings
from database.connection import get_connection
from utils.dates import utc_now_iso

bearer_scheme = HTTPBearer()


def hash_password(plain_password: str) -> str:
    """Hash a password with bcrypt."""
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(user_id: int, username: str, role: str) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _hash_token(token: str) -> str:
    """Hash a refresh token before storing it."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(user_id: int) -> str:
    """Create and persist a refresh token."""
    settings = get_settings()
    token = secrets.token_urlsafe(48)
    expires_at = (datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)).isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO refresh_tokens (user_id, token_hash, expires_at, created_at)
           VALUES (?, ?, ?, ?)""",
        (user_id, _hash_token(token), expires_at, utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return token


def exchange_refresh_token(refresh_token: str) -> dict:
    """Validate a refresh token and return the owning user row."""
    conn = get_connection()
    row = conn.execute(
        """SELECT rt.*, u.username, u.role, u.full_name
           FROM refresh_tokens rt
           JOIN users u ON u.id = rt.user_id
           WHERE rt.token_hash = ? AND rt.revoked_at IS NULL""",
        (_hash_token(refresh_token),),
    ).fetchone()
    conn.close()
    if not row or row["expires_at"] < datetime.utcnow().isoformat():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
    return dict(row)


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired. Please refresh or log in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token.") from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type.")
    return payload


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Extract and validate the authenticated user from the Authorization header."""
    return decode_access_token(credentials.credentials)


def require_role(required_role: str):
    """Return a dependency that enforces a user role."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires '{required_role}' role.",
            )
        return user

    return checker
