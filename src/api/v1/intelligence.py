"""AI intelligence, OCR, QR, search, and health routes."""

from fastapi import APIRouter, Depends, HTTPException

import schemas
from repositories.product_repository import get_by_qr_token, get_customer_product
from security.auth import get_current_user
from services.ai_pipeline import semantic_search
from services.analytics_service import warranty_health
from services.ocr_service import extract_invoice_fields
from services.qr_service import qr_svg

router = APIRouter()


@router.post("/ai/search", response_model=list[schemas.SemanticSearchResult])
async def semantic_query(payload: schemas.SemanticSearchRequest, user: dict = Depends(get_current_user)) -> list[schemas.SemanticSearchResult]:
    """Run semantic search across products, claims, and warranty clauses."""
    return [schemas.SemanticSearchResult(**row) for row in semantic_search(payload.query, payload.limit)]


@router.post("/ocr/extract", response_model=schemas.OCRExtractionResponse)
async def ocr_extract_text(text: str, user: dict = Depends(get_current_user)) -> schemas.OCRExtractionResponse:
    """Extract invoice fields from OCR text or pasted invoice text."""
    return extract_invoice_fields(text)


@router.get("/products/{customer_product_id}/qr", response_model=schemas.QRCodeResponse)
async def product_qr(customer_product_id: int, user: dict = Depends(get_current_user)) -> schemas.QRCodeResponse:
    """Return an SVG QR code for a registered product."""
    product = get_customer_product(customer_product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Registered product not found.")
    return qr_svg(customer_product_id, product["qr_token"])


@router.get("/qr/{qr_token}", response_model=schemas.CustomerProductOut)
async def scan_qr(qr_token: str) -> schemas.CustomerProductOut:
    """Open the mobile-friendly product view behind a scanned QR token."""
    product = get_by_qr_token(qr_token)
    if not product:
        raise HTTPException(status_code=404, detail="QR code not found.")
    return schemas.CustomerProductOut(
        id=product["id"],
        product_name=product["product_name"],
        model_number=product["model_number"],
        serial_number=product["serial_number"],
        purchase_date=product["purchase_date"],
        warranty_start=product["warranty_start"],
        warranty_end=product["warranty_end"],
        warranty_active=product["warranty_end"] >= __import__("datetime").datetime.utcnow().date().isoformat(),
        qr_token=product["qr_token"],
        warranty_health=warranty_health(product),
    )


@router.get("/products/{customer_product_id}/health", response_model=schemas.WarrantyHealth)
async def product_health(customer_product_id: int, user: dict = Depends(get_current_user)) -> schemas.WarrantyHealth:
    """Return the warranty health score for a registered product."""
    product = get_customer_product(customer_product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Registered product not found.")
    return warranty_health(product)
