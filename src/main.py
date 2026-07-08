"""FastAPI application entrypoint for VOLTA."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.router import router as api_v1_router
from api.v1.admin import admin_list_service_requests, admin_update_service_request
from api.v1.auth import login, refresh_token, register_customer
from api.v1.customer import create_service_request, my_products, my_service_requests, register_product
from api.v1.intelligence import ocr_extract_text, product_health, product_qr, scan_qr, semantic_query
from api.v1.products import product_detail, products
from config import get_settings
from database import init_db, seed_data
from middleware.rate_limit import RateLimitMiddleware
from utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="AI-assisted warranty, claims, fraud, QR, OCR, and analytics platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
app.include_router(api_v1_router)


@app.on_event("startup")
def startup() -> None:
    """Initialize database schema and seed deterministic demo data."""
    init_db()
    seed_data()
    logger.info("VOLTA backend started")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return consistent validation errors."""
    return JSONResponse(status_code=422, content={"error": "validation_error", "details": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected exceptions and return a stable response envelope."""
    logger.exception("Unhandled request failure: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "internal_server_error", "message": "Unexpected server error."})


@app.get("/")
async def root() -> dict:
    """Return a basic API status payload."""
    return {"status": "ok", "message": "VOLTA AI Warranty Intelligence Platform API running.", "version": "2.0.0"}


@app.get("/health")
async def health() -> dict:
    """Return health status for Docker and CI checks."""
    return {"status": "healthy", "service": "volta-api"}


# Backward-compatible route aliases used by the existing Streamlit frontend.
app.add_api_route("/auth/register", register_customer, methods=["POST"], response_model=dict)
app.add_api_route("/auth/login", login, methods=["POST"])
app.add_api_route("/auth/refresh", refresh_token, methods=["POST"])
app.add_api_route("/products", products, methods=["GET"])
app.add_api_route("/products/{product_id}", product_detail, methods=["GET"])
app.add_api_route("/customer/register-product", register_product, methods=["POST"])
app.add_api_route("/customer/my-products", my_products, methods=["GET"])
app.add_api_route("/customer/service-requests", create_service_request, methods=["POST"])
app.add_api_route("/customer/service-requests", my_service_requests, methods=["GET"])
app.add_api_route("/admin/service-requests", admin_list_service_requests, methods=["GET"])
app.add_api_route("/admin/service-requests/{request_id}", admin_update_service_request, methods=["PATCH"])
app.add_api_route("/admin/analytics", __import__("api.v1.admin", fromlist=["analytics"]).analytics, methods=["GET"])
app.add_api_route("/ai/search", semantic_query, methods=["POST"])
app.add_api_route("/ocr/extract", ocr_extract_text, methods=["POST"])
app.add_api_route("/products/{customer_product_id}/qr", product_qr, methods=["GET"])
app.add_api_route("/products/{customer_product_id}/health", product_health, methods=["GET"])
app.add_api_route("/qr/{qr_token}", scan_qr, methods=["GET"])
