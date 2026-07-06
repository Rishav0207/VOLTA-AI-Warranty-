"""
FastAPI backend for VOLTA.

Run with:
    uvicorn main:app --reload --port 8000

Routes:
  /auth/register, /auth/login
  /products
  /customer/register-product, /customer/my-products
  /customer/service-requests (GET + POST)
  /admin/service-requests (GET + PATCH)
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import database
import schemas
import ai_service
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
)

app = FastAPI(title="Smart Warranty and Product Service Tracker")

# streamlit runs on a different port so CORS needs to be open for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    database.init_db()
    database.seed_data()


# --- auth ---

@app.post("/auth/register", response_model=dict)
def register_customer(payload: schemas.RegisterCustomerRequest):
    conn = database.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username = ? OR email = ?",
                (payload.username, payload.email))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already registered.")

    cur.execute(
        """INSERT INTO users (username, password_hash, role, full_name, email, created_at)
           VALUES (?, ?, 'customer', ?, ?, ?)""",
        (payload.username, hash_password(payload.password), payload.full_name,
         payload.email, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"message": "Registration successful. Please log in."}


@app.post("/auth/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest):
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (payload.username,))
    user = cur.fetchone()
    conn.close()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")

    token = create_access_token(user["id"], user["username"], user["role"])
    return schemas.LoginResponse(access_token=token, role=user["role"], full_name=user["full_name"])


# --- products (catalog, needs login) ---

@app.get("/products", response_model=List[schemas.ProductOut])
def list_products(user: dict = Depends(get_current_user)):
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [schemas.ProductOut(**dict(row)) for row in rows]


# --- customer routes ---

@app.post("/customer/register-product", response_model=schemas.CustomerProductOut)
def register_product(payload: schemas.RegisterProductRequest,
                      user: dict = Depends(require_role("customer"))):
    conn = database.get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT p.*, w.duration_months FROM products p
                   JOIN warranty_templates w ON w.product_id = p.id
                   WHERE p.id = ?""", (payload.product_id,))
    product = cur.fetchone()
    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="Product or warranty template not found.")

    purchase_date = datetime.strptime(payload.purchase_date, "%Y-%m-%d")
    warranty_end = purchase_date + timedelta(days=30 * product["duration_months"])

    cur.execute(
        """INSERT INTO customer_products
           (user_id, product_id, serial_number, purchase_date, warranty_start, warranty_end, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user["user_id"], payload.product_id, payload.serial_number,
         purchase_date.date().isoformat(), purchase_date.date().isoformat(),
         warranty_end.date().isoformat(), datetime.utcnow().isoformat()),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return schemas.CustomerProductOut(
        id=new_id,
        product_name=product["name"],
        model_number=product["model_number"],
        serial_number=payload.serial_number,
        purchase_date=purchase_date.date().isoformat(),
        warranty_start=purchase_date.date().isoformat(),
        warranty_end=warranty_end.date().isoformat(),
        warranty_active=warranty_end.date() >= datetime.utcnow().date(),
    )


@app.get("/customer/my-products", response_model=List[schemas.CustomerProductOut])
def my_products(user: dict = Depends(require_role("customer"))):
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT cp.*, p.name as product_name, p.model_number
           FROM customer_products cp
           JOIN products p ON p.id = cp.product_id
           WHERE cp.user_id = ?
           ORDER BY cp.created_at DESC""",
        (user["user_id"],),
    )
    rows = cur.fetchall()
    conn.close()

    today = datetime.utcnow().date().isoformat()
    return [
        schemas.CustomerProductOut(
            id=row["id"],
            product_name=row["product_name"],
            model_number=row["model_number"],
            serial_number=row["serial_number"],
            purchase_date=row["purchase_date"],
            warranty_start=row["warranty_start"],
            warranty_end=row["warranty_end"],
            warranty_active=row["warranty_end"] >= today,
        )
        for row in rows
    ]


@app.post("/customer/service-requests", response_model=schemas.ServiceRequestOut)
def create_service_request(payload: schemas.CreateServiceRequest,
                            user: dict = Depends(require_role("customer"))):
    conn = database.get_connection()
    cur = conn.cursor()

    # Fetch the warranty template tied to this customer's registered product
    cur.execute(
        """SELECT cp.id, cp.user_id, p.name as product_name,
                  wt.coverage_details, wt.exclusions
           FROM customer_products cp
           JOIN products p ON p.id = cp.product_id
           JOIN warranty_templates wt ON wt.product_id = p.id
           WHERE cp.id = ?""",
        (payload.customer_product_id,),
    )
    cp = cur.fetchone()
    if not cp:
        conn.close()
        raise HTTPException(status_code=404, detail="Registered product not found.")
    if cp["user_id"] != user["user_id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="This product is not registered to you.")

    # run it through the AI warranty check
    analysis = ai_service.analyze_service_request(
        coverage_details=cp["coverage_details"],
        exclusions=cp["exclusions"],
        issue_description=payload.issue_description,
    )
    ai_summary = (
        f"Verdict: {analysis['verdict']}\n"
        f"{analysis['explanation']}\n"
        f"Suggested documents: {', '.join(analysis['missing_proof_checklist'])}"
    )

    now = datetime.utcnow().isoformat()
    cur.execute(
        """INSERT INTO service_requests
           (customer_product_id, user_id, issue_description, status, ai_analysis, created_at, updated_at)
           VALUES (?, ?, ?, 'pending', ?, ?, ?)""",
        (payload.customer_product_id, user["user_id"], payload.issue_description,
         ai_summary, now, now),
    )
    conn.commit()
    new_id = cur.lastrowid

    cur.execute("SELECT full_name FROM users WHERE id = ?", (user["user_id"],))
    customer_name = cur.fetchone()["full_name"]
    conn.close()

    return schemas.ServiceRequestOut(
        id=new_id,
        customer_product_id=payload.customer_product_id,
        product_name=cp["product_name"],
        customer_name=customer_name,
        issue_description=payload.issue_description,
        status="pending",
        ai_analysis=ai_summary,
        admin_notes=None,
        created_at=now,
        updated_at=now,
    )


@app.get("/customer/service-requests", response_model=List[schemas.ServiceRequestOut])
def my_service_requests(user: dict = Depends(require_role("customer"))):
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT sr.*, p.name as product_name, u.full_name as customer_name
           FROM service_requests sr
           JOIN customer_products cp ON cp.id = sr.customer_product_id
           JOIN products p ON p.id = cp.product_id
           JOIN users u ON u.id = sr.user_id
           WHERE sr.user_id = ?
           ORDER BY sr.created_at DESC""",
        (user["user_id"],),
    )
    rows = cur.fetchall()
    conn.close()
    return [schemas.ServiceRequestOut(**dict(row)) for row in rows]


# --- admin routes ---

@app.get("/admin/service-requests", response_model=List[schemas.ServiceRequestOut])
def admin_list_service_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    user: dict = Depends(require_role("admin")),
):
    conn = database.get_connection()
    cur = conn.cursor()
    query = """SELECT sr.*, p.name as product_name, u.full_name as customer_name
               FROM service_requests sr
               JOIN customer_products cp ON cp.id = sr.customer_product_id
               JOIN products p ON p.id = cp.product_id
               JOIN users u ON u.id = sr.user_id"""
    params = ()
    if status_filter:
        query += " WHERE sr.status = ?"
        params = (status_filter,)
    query += " ORDER BY sr.created_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [schemas.ServiceRequestOut(**dict(row)) for row in rows]


@app.patch("/admin/service-requests/{request_id}", response_model=schemas.ServiceRequestOut)
def admin_update_service_request(
    request_id: int,
    payload: schemas.UpdateServiceRequestStatus,
    user: dict = Depends(require_role("admin")),
):
    conn = database.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM service_requests WHERE id = ?", (request_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Service request not found.")

    now = datetime.utcnow().isoformat()
    cur.execute(
        """UPDATE service_requests
           SET status = ?, admin_notes = ?, updated_at = ?
           WHERE id = ?""",
        (payload.status, payload.admin_notes, now, request_id),
    )
    conn.commit()

    cur.execute(
        """SELECT sr.*, p.name as product_name, u.full_name as customer_name
           FROM service_requests sr
           JOIN customer_products cp ON cp.id = sr.customer_product_id
           JOIN products p ON p.id = cp.product_id
           JOIN users u ON u.id = sr.user_id
           WHERE sr.id = ?""",
        (request_id,),
    )
    row = cur.fetchone()
    conn.close()
    return schemas.ServiceRequestOut(**dict(row))


@app.get("/")
def root():
    return {"status": "ok", "message": "Smart Warranty Tracker API running."}
