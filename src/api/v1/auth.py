"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Request

import schemas
from database.connection import get_connection
from repositories.audit_repository import record_activity, record_audit
from security.auth import create_access_token, create_refresh_token, exchange_refresh_token, hash_password, verify_password

router = APIRouter()


@router.post("/auth/register", response_model=dict)
async def register_customer(payload: schemas.RegisterCustomerRequest, request: Request) -> dict:
    """Register a customer account."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ? OR email = ?", (payload.username, payload.email))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already registered.")
    cur.execute(
        """INSERT INTO users (username, password_hash, role, full_name, email, created_at)
           VALUES (?, ?, 'customer', ?, ?, datetime('now'))""",
        (payload.username, hash_password(payload.password), payload.full_name, payload.email),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    record_audit(user_id, "customer_registered", "user", user_id, {"username": payload.username})
    record_activity(user_id, "register", request.client.host if request.client else None, request.headers.get("user-agent"))
    return {"message": "Registration successful. Please log in."}


@router.post("/auth/login", response_model=schemas.LoginResponse)
async def login(payload: schemas.LoginRequest, request: Request) -> schemas.LoginResponse:
    """Authenticate a user and return access and refresh tokens."""
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND deleted_at IS NULL", (payload.username,)).fetchone()
    conn.close()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    access_token = create_access_token(user["id"], user["username"], user["role"])
    refresh_token = create_refresh_token(user["id"])
    record_activity(user["id"], "login", request.client.host if request.client else None, request.headers.get("user-agent"))
    return schemas.LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user["role"],
        full_name=user["full_name"],
    )


@router.post("/auth/refresh", response_model=schemas.TokenPair)
async def refresh_token(payload: schemas.RefreshRequest) -> schemas.TokenPair:
    """Exchange a refresh token for a new token pair."""
    token_row = exchange_refresh_token(payload.refresh_token)
    return schemas.TokenPair(
        access_token=create_access_token(token_row["user_id"], token_row["username"], token_row["role"]),
        refresh_token=create_refresh_token(token_row["user_id"]),
    )
