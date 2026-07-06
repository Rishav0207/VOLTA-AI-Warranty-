"""
Password hashing + JWT login stuff.

Login flow: verify password -> issue a JWT with {user_id, username, role, exp}
-> frontend sends it back as "Authorization: Bearer <token>" on every request
-> get_current_user / require_role check it before doing anything sensitive.
"""

import os
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# load this from an env var in prod, don't hardcode it
SECRET_KEY = os.environ.get("WARRANTY_APP_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 12

bearer_scheme = HTTPBearer()


def hash_password(plain_password: str) -> str:
    # bcrypt caps input at 72 bytes
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: extracts and validates the logged-in user from the request."""
    token = credentials.credentials
    return decode_access_token(token)


def require_role(required_role: str):
    """FastAPI dependency factory: use as Depends(require_role('admin'))"""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires '{required_role}' role.",
            )
        return user

    return checker
