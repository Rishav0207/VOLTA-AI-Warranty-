"""SQLite connection factory."""

import sqlite3
from pathlib import Path

from config import get_settings


def _resolve_db_path() -> Path:
    """Resolve and create the configured SQLite database path."""
    path = get_settings().db_path
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


DB_PATH = _resolve_db_path()


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with foreign keys and row dictionaries enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
