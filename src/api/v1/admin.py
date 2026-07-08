"""Admin routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

import schemas
from api.v1.customer import _service_out
from database.connection import get_connection
from repositories.audit_repository import record_audit
from repositories.service_request_repository import fetch_service_request, list_service_requests
from security.auth import require_role
from services.analytics_service import admin_analytics
from utils.dates import utc_now_iso

router = APIRouter()


@router.get("/admin/service-requests", response_model=list[schemas.ServiceRequestOut])
async def admin_list_service_requests(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(require_role("admin")),
) -> list[schemas.ServiceRequestOut]:
    """List all service requests for admins."""
    return [_service_out(row) for row in list_service_requests(status=status, limit=limit, offset=offset)]


@router.patch("/admin/service-requests/{request_id}", response_model=schemas.ServiceRequestOut)
async def admin_update_service_request(
    request_id: int,
    payload: schemas.UpdateServiceRequestStatus,
    user: dict = Depends(require_role("admin")),
) -> schemas.ServiceRequestOut:
    """Update service-request status and record claim history."""
    existing = fetch_service_request(request_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Service request not found.")
    now = utc_now_iso()
    conn = get_connection()
    conn.execute(
        "UPDATE service_requests SET status = ?, admin_notes = ?, updated_at = ? WHERE id = ?",
        (payload.status, payload.admin_notes, now, request_id),
    )
    conn.execute(
        """INSERT INTO warranty_claim_history (service_request_id, status, notes, created_at)
           VALUES (?, ?, ?, ?)""",
        (request_id, payload.status, payload.admin_notes, now),
    )
    if payload.status == "resolved":
        conn.execute(
            """INSERT INTO repair_history (customer_product_id, service_request_id, repair_type, technician_notes, repaired_at)
               VALUES (?, ?, 'warranty_service', ?, ?)""",
            (existing["customer_product_id"], request_id, payload.admin_notes, now),
        )
    conn.commit()
    conn.close()
    record_audit(user["user_id"], "service_request_updated", "service_request", request_id, {"status": payload.status})
    return _service_out(fetch_service_request(request_id))


@router.get("/admin/analytics", response_model=schemas.DashboardAnalytics)
async def analytics(user: dict = Depends(require_role("admin"))) -> schemas.DashboardAnalytics:
    """Return SaaS-style dashboard analytics for admins."""
    return admin_analytics()
