"""Product and customer-product schemas."""

from pydantic import BaseModel, Field

from schemas.intelligence import WarrantyHealth


class ProductOut(BaseModel):
    """Catalog product response."""

    id: int
    name: str
    category: str
    model_number: str
    price: float


class ProductDetailOut(ProductOut):
    """Extended catalog product response."""

    manufacturer: str = "Company X"
    duration_months: int | None = None
    coverage_details: str | None = None
    exclusions: str | None = None


class RegisterProductRequest(BaseModel):
    """Register a purchased product for a customer."""

    product_id: int
    serial_number: str = Field(min_length=3, max_length=80)
    purchase_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    invoice_number: str | None = Field(default=None, max_length=80)
    seller: str | None = Field(default=None, max_length=160)
    gst_number: str | None = Field(default=None, max_length=32)


class CustomerProductOut(BaseModel):
    """Registered customer product response."""

    id: int
    product_name: str
    model_number: str
    serial_number: str
    purchase_date: str
    warranty_start: str
    warranty_end: str
    warranty_active: bool
    qr_token: str | None = None
    warranty_health: WarrantyHealth | None = None
