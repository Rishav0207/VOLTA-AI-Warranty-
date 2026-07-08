"""Customer product and service-request routes."""

import json

from fastapi import APIRouter, Depends, HTTPException

import schemas
from database.connection import get_connection
from repositories.audit_repository import record_audit
from repositories.product_repository import get_customer_product, get_product_with_warranty, list_customer_products
from repositories.service_request_repository import fetch_service_request, list_service_requests
from schemas.intelligence import AIExplanation
from security.auth import require_role
from services.ai_pipeline import analyze_warranty_claim
from services.analytics_service import warranty_health
from services.qr_service import new_qr_token
from utils.dates import add_months_approx, parse_date, utc_now_iso

router = APIRouter()


def _customer_product_out(row: dict) -> schemas.CustomerProductOut:
    """Map a registered-product row to its response model."""
    return schemas.CustomerProductOut(
        id=row["id"],
        product_name=row["product_name"],
        model_number=row["model_number"],
        serial_number=row["serial_number"],
        purchase_date=row["purchase_date"],
        warranty_start=row["warranty_start"],
        warranty_end=row["warranty_end"],
        warranty_active=row["warranty_end"] >= utc_now_iso()[:10],
        qr_token=row.get("qr_token"),
        warranty_health=warranty_health(row),
    )


def _service_out(row: dict) -> schemas.ServiceRequestOut:
    """Map a service-request row to a response model."""
    explanation = None
    if row.get("ai_analysis"):
        try:
            explanation = AIExplanation(**json.loads(row["ai_analysis"]))
        except Exception:
            explanation = None
    return schemas.ServiceRequestOut(**row, ai_explanation=explanation)


@router.post("/customer/register-product", response_model=schemas.CustomerProductOut)
async def register_product(payload: schemas.RegisterProductRequest, user: dict = Depends(require_role("customer"))) -> schemas.CustomerProductOut:
    """Register a product, compute warranty dates, and assign a QR token."""
    product = get_product_with_warranty(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product or warranty template not found.")
    purchase_date = parse_date(payload.purchase_date)
    warranty_end = add_months_approx(purchase_date, product["duration_months"])
    now = utc_now_iso()
    qr_token = new_qr_token()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO customer_products
           (user_id, product_id, serial_number, purchase_date, warranty_start, warranty_end,
            qr_token, invoice_number, seller, gst_number, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user["user_id"],
            payload.product_id,
            payload.serial_number,
            purchase_date.isoformat(),
            purchase_date.isoformat(),
            warranty_end.isoformat(),
            qr_token,
            payload.invoice_number,
            payload.seller,
            payload.gst_number,
            now,
            now,
        ),
    )
    customer_product_id = cur.lastrowid
    cur.execute(
        """INSERT INTO product_history (customer_product_id, event_type, details, created_at)
           VALUES (?, 'registration', ?, ?)""",
        (customer_product_id, f"Registered {product['name']} with serial {payload.serial_number}", now),
    )
    conn.commit()
    conn.close()
    record_audit(user["user_id"], "product_registered", "customer_product", customer_product_id, {"product_id": payload.product_id})
    row = get_customer_product(customer_product_id)
    return _customer_product_out(row)


@router.get("/customer/my-products", response_model=list[schemas.CustomerProductOut])
async def my_products(user: dict = Depends(require_role("customer"))) -> list[schemas.CustomerProductOut]:
    """Return the current customer's registered products."""
    return [_customer_product_out(row) for row in list_customer_products(user["user_id"])]


@router.post("/customer/service-requests", response_model=schemas.ServiceRequestOut)
async def create_service_request(payload: schemas.CreateServiceRequest, user: dict = Depends(require_role("customer"))) -> schemas.ServiceRequestOut:
    """Create a service request and attach an explainable AI analysis."""
    product = get_customer_product(payload.customer_product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Registered product not found.")
    if product["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="This product is not registered to you.")
    analysis = analyze_warranty_claim(product, payload.issue_description)
    now = utc_now_iso()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO service_requests
           (customer_product_id, user_id, issue_description, status, ai_analysis, fraud_score,
            approval_probability, created_at, updated_at)
           VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?)""",
        (
            payload.customer_product_id,
            user["user_id"],
            payload.issue_description,
            analysis.model_dump_json(),
            analysis.fraud_risk_score,
            analysis.estimated_approval_probability,
            now,
            now,
        ),
    )
    request_id = cur.lastrowid
    cur.execute(
        """INSERT INTO warranty_claim_history (service_request_id, status, notes, created_at)
           VALUES (?, 'pending', 'Claim created with AI analysis', ?)""",
        (request_id, now),
    )
    cur.execute(
        """INSERT INTO product_history (customer_product_id, event_type, details, created_at)
           VALUES (?, 'claim_created', ?, ?)""",
        (payload.customer_product_id, payload.issue_description, now),
    )
    conn.commit()
    conn.close()
    record_audit(user["user_id"], "service_request_created", "service_request", request_id, {"status": analysis.coverage_status})
    return _service_out(fetch_service_request(request_id))


@router.get("/customer/service-requests", response_model=list[schemas.ServiceRequestOut])
async def my_service_requests(user: dict = Depends(require_role("customer"))) -> list[schemas.ServiceRequestOut]:
    """Return the current customer's service requests."""
    return [_service_out(row) for row in list_service_requests(user_id=user["user_id"])]
