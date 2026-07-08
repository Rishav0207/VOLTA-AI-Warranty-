"""Dashboard analytics and warranty health calculations."""

from datetime import datetime

from database.connection import get_connection
from schemas.intelligence import DashboardAnalytics, WarrantyHealth


def warranty_health(product: dict) -> WarrantyHealth:
    """Compute a warranty health score from age, repairs, claims, and remaining coverage."""
    today = datetime.utcnow().date()
    end = datetime.strptime(product["warranty_end"], "%Y-%m-%d").date()
    remaining_days = (end - today).days
    conn = get_connection()
    claims = conn.execute(
        "SELECT COUNT(*) AS c FROM service_requests WHERE customer_product_id = ? AND deleted_at IS NULL",
        (product["id"],),
    ).fetchone()["c"]
    repairs = conn.execute(
        "SELECT COUNT(*) AS c FROM repair_history WHERE customer_product_id = ?",
        (product["id"],),
    ).fetchone()["c"]
    conn.close()
    score = 70 + min(25, max(0, remaining_days) // 30) - claims * 8 - repairs * 6
    score = max(0, min(100, score))
    label = "Excellent" if score >= 80 else "Watch" if score >= 55 else "At Risk"
    recommendation = "Warranty is healthy." if score >= 80 else "Review documents and plan preventive service."
    return WarrantyHealth(score=score, label=label, remaining_days=remaining_days, service_recommendation=recommendation)


def admin_analytics() -> DashboardAnalytics:
    """Return admin dashboard metrics."""
    conn = get_connection()
    scalar = lambda sql: conn.execute(sql).fetchone()["c"]
    users = scalar("SELECT COUNT(*) AS c FROM users WHERE deleted_at IS NULL")
    products = scalar("SELECT COUNT(*) AS c FROM products WHERE deleted_at IS NULL")
    registered = scalar("SELECT COUNT(*) AS c FROM customer_products WHERE deleted_at IS NULL")
    claims = scalar("SELECT COUNT(*) AS c FROM service_requests WHERE deleted_at IS NULL")
    open_claims = scalar("SELECT COUNT(*) AS c FROM service_requests WHERE status IN ('pending','in_progress') AND deleted_at IS NULL")
    fraud_alerts = scalar("SELECT COUNT(*) AS c FROM service_requests WHERE fraud_score >= 60 AND deleted_at IS NULL")
    resolved = scalar("SELECT COUNT(*) AS c FROM service_requests WHERE status = 'resolved' AND deleted_at IS NULL")
    closed = scalar("SELECT COUNT(*) AS c FROM service_requests WHERE status IN ('resolved','rejected') AND deleted_at IS NULL")
    top = [
        {"manufacturer": row["manufacturer"], "count": row["c"]}
        for row in conn.execute(
            """SELECT p.manufacturer, COUNT(*) AS c
               FROM customer_products cp JOIN products p ON p.id = cp.product_id
               GROUP BY p.manufacturer ORDER BY c DESC LIMIT 5"""
        ).fetchall()
    ]
    monthly = [
        {"month": row["month"], "count": row["c"]}
        for row in conn.execute(
            """SELECT substr(created_at, 1, 7) AS month, COUNT(*) AS c
               FROM customer_products GROUP BY substr(created_at, 1, 7)
               ORDER BY month DESC LIMIT 12"""
        ).fetchall()
    ]
    conn.close()
    return DashboardAnalytics(
        users=users,
        products=products,
        registered_products=registered,
        claims=claims,
        open_claims=open_claims,
        fraud_alerts=fraud_alerts,
        approval_rate=round((resolved / closed) * 100, 2) if closed else 0.0,
        top_manufacturers=top,
        monthly_registrations=monthly,
    )
