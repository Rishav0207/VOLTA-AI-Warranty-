"""
schemas.py
----------
Pydantic models = the "shape" of data going in/out of the API.
FastAPI uses these to validate requests and auto-generate API docs (/docs).
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


# ---------- Auth ----------
class RegisterCustomerRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    role: str
    full_name: str


# ---------- Products ----------
class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    model_number: str
    price: float


# ---------- Customer product registration ----------
class RegisterProductRequest(BaseModel):
    product_id: int
    serial_number: str
    purchase_date: str  # format: YYYY-MM-DD


class CustomerProductOut(BaseModel):
    id: int
    product_name: str
    model_number: str
    serial_number: str
    purchase_date: str
    warranty_start: str
    warranty_end: str
    warranty_active: bool


# ---------- Service requests ----------
class CreateServiceRequest(BaseModel):
    customer_product_id: int
    issue_description: str


class ServiceRequestOut(BaseModel):
    id: int
    customer_product_id: int
    product_name: str
    customer_name: str
    issue_description: str
    status: str
    ai_analysis: Optional[str]
    admin_notes: Optional[str]
    created_at: str
    updated_at: str


class UpdateServiceRequestStatus(BaseModel):
    status: str  # pending | in_progress | resolved | rejected
    admin_notes: Optional[str] = None
