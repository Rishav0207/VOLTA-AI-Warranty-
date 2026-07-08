"""Product and customer-product data access."""

from database.connection import get_connection


def list_products(search: str | None = None, limit: int = 50, offset: int = 0, sort: str = "name") -> list[dict]:
    """Return product catalog rows with optional filtering and pagination."""
    allowed_sort = {"name": "name", "category": "category", "price": "price", "model_number": "model_number"}
    order_by = allowed_sort.get(sort, "name")
    conn = get_connection()
    params: list[object] = []
    query = "SELECT * FROM products WHERE deleted_at IS NULL"
    if search:
        query += " AND (name LIKE ? OR category LIKE ? OR model_number LIKE ? OR manufacturer LIKE ?)"
        needle = f"%{search}%"
        params.extend([needle, needle, needle, needle])
    query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = [dict(row) for row in conn.execute(query, params).fetchall()]
    conn.close()
    return rows


def get_product_with_warranty(product_id: int) -> dict | None:
    """Return a product joined to its warranty template."""
    conn = get_connection()
    row = conn.execute(
        """SELECT p.*, w.id AS warranty_template_id, w.duration_months, w.coverage_details, w.exclusions, w.conditions
           FROM products p
           JOIN warranty_templates w ON w.product_id = p.id
           WHERE p.id = ? AND p.deleted_at IS NULL""",
        (product_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_customer_product(customer_product_id: int) -> dict | None:
    """Return a registered product with product and warranty context."""
    conn = get_connection()
    row = conn.execute(
        """SELECT cp.*, p.name AS product_name, p.model_number, p.category, p.manufacturer,
                  wt.id AS warranty_template_id, wt.duration_months, wt.coverage_details, wt.exclusions, wt.conditions,
                  u.full_name AS customer_name
           FROM customer_products cp
           JOIN products p ON p.id = cp.product_id
           JOIN warranty_templates wt ON wt.product_id = p.id
           JOIN users u ON u.id = cp.user_id
           WHERE cp.id = ? AND cp.deleted_at IS NULL""",
        (customer_product_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_customer_products(user_id: int) -> list[dict]:
    """Return all active registered products for a customer."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT cp.*, p.name AS product_name, p.model_number, p.category, p.manufacturer
           FROM customer_products cp
           JOIN products p ON p.id = cp.product_id
           WHERE cp.user_id = ? AND cp.deleted_at IS NULL
           ORDER BY cp.created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_by_qr_token(qr_token: str) -> dict | None:
    """Return a registered product by QR token."""
    conn = get_connection()
    row = conn.execute(
        """SELECT cp.*, p.name AS product_name, p.model_number, p.category, p.manufacturer
           FROM customer_products cp
           JOIN products p ON p.id = cp.product_id
           WHERE cp.qr_token = ? AND cp.deleted_at IS NULL""",
        (qr_token,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
