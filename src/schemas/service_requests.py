"""Service-request schemas."""

from pydantic import BaseModel, Field

from schemas.intelligence import AIExplanation


class CreateServiceRequest(BaseModel):
    """Create a warranty service request."""

    customer_product_id: int
    issue_description: str = Field(min_length=5, max_length=2000)


class ServiceRequestOut(BaseModel):
    """Warranty claim/service request response."""

    id: int
    customer_product_id: int
    product_name: str
    customer_name: str
    issue_description: str
    status: str
    ai_analysis: str | None
    admin_notes: str | None
    created_at: str
    updated_at: str
    fraud_score: int = 0
    approval_probability: int = 50
    ai_explanation: AIExplanation | None = None


class UpdateServiceRequestStatus(BaseModel):
    """Admin service-request status update."""

    status: str = Field(pattern="^(pending|in_progress|resolved|rejected)$")
    admin_notes: str | None = Field(default=None, max_length=2000)
