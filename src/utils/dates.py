"""Date helpers used by services and repositories."""

from datetime import date, datetime, timedelta


def utc_now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.utcnow().replace(microsecond=0).isoformat()


def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD date string."""
    return datetime.strptime(value, "%Y-%m-%d").date()


def add_months_approx(start: date, months: int) -> date:
    """Add warranty months using the legacy app's 30-day month approximation."""
    return start + timedelta(days=30 * months)
