"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field


class RegisterCustomerRequest(BaseModel):
    """Payload for customer self-registration."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class LoginRequest(BaseModel):
    """Username/password login payload."""

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenPair):
    """Login response returned to the UI."""

    role: str
    full_name: str


class RefreshRequest(BaseModel):
    """Refresh-token exchange payload."""

    refresh_token: str = Field(min_length=20)
