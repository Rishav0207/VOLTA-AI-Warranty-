"""
SQLite connection, schema, and seed data.

Using raw sqlite3 instead of an ORM on purpose, easier to see exactly what
SQL is running. DB file lives at data/warranty_tracker.db, created
automatically on first run.

Tables: users, products, warranty_templates, customer_products,
service_requests, documents.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent / "data" / "warranty_tracker.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Returns a new sqlite3 connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('customer', 'admin')),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    model_number TEXT UNIQUE NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS warranty_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    duration_months INTEGER NOT NULL,
    coverage_details TEXT NOT NULL,   -- plain text list of what's covered
    exclusions TEXT NOT NULL,         -- plain text list of what's NOT covered
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS customer_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    serial_number TEXT NOT NULL,
    purchase_date TEXT NOT NULL,
    warranty_start TEXT NOT NULL,
    warranty_end TEXT NOT NULL,
    created_at TEXT NOT NULL,
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
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(customer_product_id) REFERENCES customer_products(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_request_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY(service_request_id) REFERENCES service_requests(id)
);
"""


def init_db():
    """Create all tables if they don't already exist."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def seed_data():
    """Insert default admin + sample catalog, only if tables are empty. Safe to call every startup."""
    from auth import hash_password  # local import, avoids circular import

    conn = get_connection()
    cur = conn.cursor()

    # --- Seed admin account ---
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            """INSERT INTO users (username, password_hash, role, full_name, email, created_at)
               VALUES (?, ?, 'admin', ?, ?, ?)""",
            (
                "admin",
                hash_password("admin123"),  # CHANGE THIS in a real deployment
                "System Admin",
                "admin@company.com",
                datetime.utcnow().isoformat(),
            ),
        )
        print("Seeded default admin -> username: admin / password: admin123")

    # --- Seed product catalog ---
    cur.execute("SELECT COUNT(*) as c FROM products")
    if cur.fetchone()["c"] == 0:
        products = [
            ("Company X Washing Machine WX-200", "Home Appliance", "WX-200", 24999.0),
            ("Company X Refrigerator RF-450", "Home Appliance", "RF-450", 32999.0),
            ("Company X Smart TV ST-55", "Electronics", "ST-55", 45999.0),
            ("Company X Laptop LP-14 Pro", "Electronics", "LP-14P", 68999.0),
            ("Company X Microwave MW-30", "Home Appliance", "MW-30", 8999.0),
        ]
        cur.executemany(
            "INSERT INTO products (name, category, model_number, price) VALUES (?, ?, ?, ?)",
            products,
        )

        # Warranty templates, one per product (by matching model_number)
        cur.execute("SELECT id, model_number FROM products")
        product_ids = {row["model_number"]: row["id"] for row in cur.fetchall()}

        warranty_templates = [
            (
                product_ids["WX-200"],
                24,
                "Motor and drum defects; electrical faults from normal use; free repair labor for manufacturing defects.",
                "Water damage from misuse, physical/accidental damage, rust from improper drainage, unauthorized repairs, consumables (seals/gaskets after 12 months).",
            ),
            (
                product_ids["RF-450"],
                36,
                "Compressor covered for full term; cooling system defects; electrical faults from normal use.",
                "Physical damage, damage from power surges without surge protector, cosmetic issues (dents/scratches), food spoilage claims.",
            ),
            (
                product_ids["ST-55"],
                12,
                "Panel defects, internal circuit failure, manufacturing defects in display.",
                "Screen physical damage/cracks, water damage, burn-in from static images, third-party accessory failures.",
            ),
            (
                product_ids["LP-14P"],
                12,
                "Motherboard, RAM, keyboard manufacturing defects; battery covered if capacity drops below 80% within 6 months.",
                "Accidental damage, liquid spills, software/OS issues, battery degradation after 6 months, unauthorized part replacement.",
            ),
            (
                product_ids["MW-30"],
                12,
                "Heating element and internal electrical faults from normal use.",
                "Physical damage, use of non-microwave-safe containers causing damage, unauthorized repairs.",
            ),
        ]
        cur.executemany(
            """INSERT INTO warranty_templates
               (product_id, duration_months, coverage_details, exclusions)
               VALUES (?, ?, ?, ?)""",
            warranty_templates,
        )
        print("Seeded product catalog + warranty templates.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_data()
    print(f"Database ready at {DB_PATH}")
