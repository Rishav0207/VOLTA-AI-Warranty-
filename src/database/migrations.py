"""Idempotent schema creation and additive migrations."""

from database.connection import get_connection


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('customer', 'admin')),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    manufacturer TEXT NOT NULL DEFAULT 'Company X',
    model_number TEXT UNIQUE NOT NULL,
    price REAL NOT NULL,
    created_at TEXT,
    updated_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS warranty_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    duration_months INTEGER NOT NULL,
    coverage_details TEXT NOT NULL,
    exclusions TEXT NOT NULL,
    conditions TEXT NOT NULL DEFAULT 'Valid invoice, matching serial number, and no unauthorized repair.',
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS warranty_clauses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    clause_type TEXT NOT NULL CHECK(clause_type IN ('coverage', 'exclusion', 'condition')),
    clause_text TEXT NOT NULL,
    embedding TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(template_id) REFERENCES warranty_templates(id)
);

CREATE TABLE IF NOT EXISTS customer_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    serial_number TEXT NOT NULL,
    purchase_date TEXT NOT NULL,
    warranty_start TEXT NOT NULL,
    warranty_end TEXT NOT NULL,
    qr_token TEXT UNIQUE,
    invoice_number TEXT,
    seller TEXT,
    gst_number TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    deleted_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS service_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_product_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    issue_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'in_progress', 'resolved', 'rejected')),
    ai_analysis TEXT,
    admin_notes TEXT,
    fraud_score INTEGER NOT NULL DEFAULT 0,
    approval_probability INTEGER NOT NULL DEFAULT 50,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    FOREIGN KEY(customer_product_id) REFERENCES customer_products(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_request_id INTEGER,
    customer_product_id INTEGER,
    file_name TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    mime_type TEXT,
    size_bytes INTEGER DEFAULT 0,
    metadata TEXT,
    ocr_text TEXT,
    ocr_confidence REAL,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY(service_request_id) REFERENCES service_requests(id),
    FOREIGN KEY(customer_product_id) REFERENCES customer_products(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    metadata TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(actor_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS product_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_product_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(customer_product_id) REFERENCES customer_products(id)
);

CREATE TABLE IF NOT EXISTS warranty_claim_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_request_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(service_request_id) REFERENCES service_requests(id)
);

CREATE TABLE IF NOT EXISTS repair_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_product_id INTEGER NOT NULL,
    service_request_id INTEGER,
    repair_type TEXT NOT NULL,
    cost REAL DEFAULT 0,
    technician_notes TEXT,
    repaired_at TEXT NOT NULL,
    FOREIGN KEY(customer_product_id) REFERENCES customer_products(id),
    FOREIGN KEY(service_request_id) REFERENCES service_requests(id)
);

CREATE TABLE IF NOT EXISTS user_activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    activity TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_customer_products_user ON customer_products(user_id);
CREATE INDEX IF NOT EXISTS idx_customer_products_serial ON customer_products(serial_number);
CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_service_requests_user ON service_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
"""

ADDITIVE_COLUMNS = {
    "users": [
        ("is_active", "INTEGER NOT NULL DEFAULT 1"),
        ("updated_at", "TEXT"),
        ("deleted_at", "TEXT"),
    ],
    "products": [
        ("manufacturer", "TEXT NOT NULL DEFAULT 'Company X'"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
        ("deleted_at", "TEXT"),
    ],
    "warranty_templates": [
        ("conditions", "TEXT NOT NULL DEFAULT 'Valid invoice, matching serial number, and no unauthorized repair.'"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
    ],
    "customer_products": [
        ("qr_token", "TEXT"),
        ("invoice_number", "TEXT"),
        ("seller", "TEXT"),
        ("gst_number", "TEXT"),
        ("updated_at", "TEXT"),
        ("deleted_at", "TEXT"),
    ],
    "service_requests": [
        ("fraud_score", "INTEGER NOT NULL DEFAULT 0"),
        ("approval_probability", "INTEGER NOT NULL DEFAULT 50"),
        ("deleted_at", "TEXT"),
    ],
    "documents": [
        ("customer_product_id", "INTEGER"),
        ("mime_type", "TEXT"),
        ("size_bytes", "INTEGER DEFAULT 0"),
        ("metadata", "TEXT"),
        ("ocr_text", "TEXT"),
        ("ocr_confidence", "REAL"),
    ],
}


def init_db() -> None:
    """Create tables, add missing columns, and prepare indexes."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    for table, columns in ADDITIVE_COLUMNS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for column, definition in columns:
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    conn.commit()
    conn.close()
