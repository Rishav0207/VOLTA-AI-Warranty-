"""Service request data access."""

from database.connection import get_connection


def fetch_service_request(request_id: int) -> dict | None:
    """Fetch one service request with display fields."""
    conn = get_connection()
    row = conn.execute(
        """SELECT sr.*, p.name AS product_name, u.full_name AS customer_name
           FROM service_requests sr
           JOIN customer_products cp ON cp.id = sr.customer_product_id
           JOIN products p ON p.id = cp.product_id
           JOIN users u ON u.id = sr.user_id
           WHERE sr.id = ? AND sr.deleted_at IS NULL""",
        (request_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_service_requests(user_id: int | None = None, status: str | None = None, limit: int = 100, offset: int = 0) -> list[dict]:
    """List service requests with optional user/status filters."""
    conn = get_connection()
    params: list[object] = []
    query = """SELECT sr.*, p.name AS product_name, u.full_name AS customer_name
               FROM service_requests sr
               JOIN customer_products cp ON cp.id = sr.customer_product_id
               JOIN products p ON p.id = cp.product_id
               JOIN users u ON u.id = sr.user_id
               WHERE sr.deleted_at IS NULL"""
    if user_id is not None:
        query += " AND sr.user_id = ?"
        params.append(user_id)
    if status:
        query += " AND sr.status = ?"
        params.append(status)
    query += " ORDER BY sr.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]
