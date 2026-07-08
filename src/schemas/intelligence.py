"""AI, OCR, search, QR, and analytics schemas."""

from pydantic import BaseModel, Field


class FraudSignal(BaseModel):
    """Single fraud or data-quality signal."""

    code: str
    severity: str
    message: str


class AIExplanation(BaseModel):
    """Explainable warranty intelligence output."""

    coverage_status: str
    confidence_score: int = Field(ge=0, le=100)
    relevant_warranty_clauses: list[str]
    reasoning: str
    applicable_conditions: list[str]
    missing_documents: list[str]
    recommended_next_action: str
    estimated_approval_probability: int = Field(ge=0, le=100)
    fraud_risk_score: int = Field(ge=0, le=100)
    fraud_signals: list[FraudSignal]
    predictive_insights: list[str]
    maintenance_advice: list[str]


class WarrantyHealth(BaseModel):
    """Computed health score for a registered product."""

    score: int = Field(ge=0, le=100)
    label: str
    remaining_days: int
    service_recommendation: str


class SemanticSearchRequest(BaseModel):
    """Natural-language search payload."""

    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class SemanticSearchResult(BaseModel):
    """Semantic search result."""

    entity_type: str
    entity_id: int
    title: str
    snippet: str
    score: float


class OCRExtractionResponse(BaseModel):
    """Structured OCR extraction result."""

    invoice_number: str | None = None
    purchase_date: str | None = None
    seller: str | None = None
    serial_number: str | None = None
    model_number: str | None = None
    warranty_duration: str | None = None
    price: float | None = None
    gst_number: str | None = None
    customer_name: str | None = None
    confidence_score: int = Field(ge=0, le=100)
    extracted_text: str
    highlighted_fields: dict[str, str]


class QRCodeResponse(BaseModel):
    """QR code payload for registered products."""

    product_id: int
    qr_token: str
    product_url: str
    qr_svg: str


class DashboardAnalytics(BaseModel):
    """Admin analytics summary."""

    users: int
    products: int
    registered_products: int
    claims: int
    open_claims: int
    fraud_alerts: int
    approval_rate: float
    top_manufacturers: list[dict[str, int | str]]
    monthly_registrations: list[dict[str, int | str]]
