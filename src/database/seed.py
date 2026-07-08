"""Seed catalog, admin account, and warranty clause vectors."""

from datetime import datetime

from auth import hash_password
from database.connection import get_connection
from services.ai_pipeline import build_clause_embedding


def seed_data() -> None:
    """Insert deterministic sample data when the database is empty."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'admin'")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            """INSERT INTO users (username, password_hash, role, full_name, email, created_at)
               VALUES (?, ?, 'admin', ?, ?, ?)""",
            ("admin", hash_password("admin123"), "System Admin", "admin@company.com", datetime.utcnow().isoformat()),
        )

    cur.execute("SELECT COUNT(*) AS c FROM products")
    if cur.fetchone()["c"] == 0:
        products = [
            ("Company X Washing Machine WX-200", "Home Appliance", "Company X", "WX-200", 24999.0),
            ("Company X Refrigerator RF-450", "Home Appliance", "Company X", "RF-450", 32999.0),
            ("Company X Smart TV ST-55", "Electronics", "Company X", "ST-55", 45999.0),
            ("Company X Laptop LP-14 Pro", "Electronics", "Company X", "LP-14P", 68999.0),
            ("Company X Microwave MW-30", "Home Appliance", "Company X", "MW-30", 8999.0),
        ]
        cur.executemany(
            "INSERT INTO products (name, category, manufacturer, model_number, price, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [(name, cat, maker, model, price, datetime.utcnow().isoformat()) for name, cat, maker, model, price in products],
        )
        cur.execute("SELECT id, model_number FROM products")
        product_ids = {row["model_number"]: row["id"] for row in cur.fetchall()}
        warranty_templates = [
            (product_ids["WX-200"], 24, "Motor and drum defects; electrical faults from normal use; free repair labor for manufacturing defects.", "Water damage from misuse, physical/accidental damage, rust from improper drainage, unauthorized repairs, consumables after 12 months."),
            (product_ids["RF-450"], 36, "Compressor covered for full term; cooling system defects; electrical faults from normal use.", "Physical damage, power surges without surge protector, cosmetic dents/scratches, food spoilage claims."),
            (product_ids["ST-55"], 12, "Panel defects, internal circuit failure, manufacturing defects in display.", "Screen cracks, water damage, burn-in from static images, third-party accessory failures."),
            (product_ids["LP-14P"], 12, "Motherboard, RAM, keyboard manufacturing defects; battery covered if capacity drops below 80% within 6 months.", "Accidental damage, liquid spills, software issues, battery degradation after 6 months, unauthorized part replacement."),
            (product_ids["MW-30"], 12, "Heating element and internal electrical faults from normal use.", "Physical damage, unsafe containers causing damage, unauthorized repairs."),
        ]
        cur.executemany(
            """INSERT INTO warranty_templates (product_id, duration_months, coverage_details, exclusions, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            [(pid, months, cov, exc, datetime.utcnow().isoformat()) for pid, months, cov, exc in warranty_templates],
        )

    cur.execute("SELECT COUNT(*) AS c FROM warranty_clauses")
    if cur.fetchone()["c"] == 0:
        cur.execute("SELECT id, coverage_details, exclusions, conditions FROM warranty_templates")
        for template in cur.fetchall():
            for clause_type, text in (
                ("coverage", template["coverage_details"]),
                ("exclusion", template["exclusions"]),
                ("condition", template["conditions"]),
            ):
                for clause in [part.strip() for part in text.split(";") if part.strip()]:
                    cur.execute(
                        """INSERT INTO warranty_clauses (template_id, clause_type, clause_text, embedding, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            template["id"],
                            clause_type,
                            clause,
                            build_clause_embedding(clause),
                            datetime.utcnow().isoformat(),
                        ),
                    )

    conn.commit()
    conn.close()
