"""Public Pydantic schema exports."""

from .auth import LoginRequest, LoginResponse, RefreshRequest, RegisterCustomerRequest, TokenPair
from .intelligence import (
    AIExplanation,
    DashboardAnalytics,
    FraudSignal,
    OCRExtractionResponse,
    QRCodeResponse,
    SemanticSearchRequest,
    SemanticSearchResult,
    WarrantyHealth,
)
from .products import CustomerProductOut, ProductDetailOut, ProductOut, RegisterProductRequest
from .service_requests import CreateServiceRequest, ServiceRequestOut, UpdateServiceRequestStatus

__all__ = [
    "AIExplanation",
    "CustomerProductOut",
    "CreateServiceRequest",
    "DashboardAnalytics",
    "FraudSignal",
    "LoginRequest",
    "LoginResponse",
    "OCRExtractionResponse",
    "ProductDetailOut",
    "ProductOut",
    "QRCodeResponse",
    "RefreshRequest",
    "RegisterCustomerRequest",
    "RegisterProductRequest",
    "SemanticSearchRequest",
    "SemanticSearchResult",
    "ServiceRequestOut",
    "TokenPair",
    "UpdateServiceRequestStatus",
    "WarrantyHealth",
]
