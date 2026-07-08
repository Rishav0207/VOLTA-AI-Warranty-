"""Audit and activity logging repository."""

import json

from database.connection import get_connection
from utils.dates import utc_now_iso


def record_audit(actor_user_id: int | None, action: str, entity_type: str, entity_id: int | None, metadata: dict | None = None) -> None:
    """Persist an immutable audit event."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO audit_logs (actor_user_id, action, entity_type, entity_id, metadata, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (actor_user_id, action, entity_type, entity_id, json.dumps(metadata or {}), utc_now_iso()),
    )
    conn.commit()
    conn.close()


def record_activity(user_id: int | None, activity: str, ip_address: str | None = None, user_agent: str | None = None) -> None:
    """Persist a user activity event."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO user_activity_logs (user_id, activity, ip_address, user_agent, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, activity, ip_address, user_agent, utc_now_iso()),
    )
    conn.commit()
    conn.close()
