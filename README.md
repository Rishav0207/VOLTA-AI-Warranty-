# VOLTA - AI Warranty Intelligence Platform

VOLTA is an AI-assisted warranty and service platform built with FastAPI, Streamlit, SQLite, and a local-first warranty intelligence pipeline. It keeps the original customer/admin workflows intact while adding production-style architecture, explainable AI output, semantic search, QR product pages, OCR invoice extraction, fraud scoring, audit logs, analytics, Docker, and tests.

## Highlights

- Customer registration, JWT login, refresh tokens, role-based access, and rate limiting.
- Product registration with warranty calculation, QR token generation, warranty health scoring, and product timelines through history tables.
- Explainable AI claim analysis with retrieved warranty clauses, confidence score, missing documents, fraud risk, approval probability, predictive insights, and maintenance advice.
- Offline semantic retrieval using deterministic sparse embeddings, with optional Ollama JSON reasoning when available.
- OCR-style invoice text extraction for invoice number, purchase date, seller, serial, model, warranty duration, price, GST, and customer name.
- Admin analytics for users, products, claims, fraud alerts, approval rate, top manufacturers, and monthly registrations.
- Backward-compatible legacy routes plus versioned `/api/v1` routes.

## Architecture

```text
app/ Streamlit UI
src/
  api/v1/          versioned FastAPI routers
  config/          environment settings
  database/        SQLite connections, migrations, seed data
  middleware/      rate limiting
  models/          domain model area
  repositories/    SQL data access
  schemas/         Pydantic request/response contracts
  security/        password hashing, JWT, refresh tokens
  services/        AI, OCR, QR, analytics business logic
  utils/           dates and logging
tests/             API and AI pipeline tests
docs/diagrams/     Mermaid architecture, ER, sequence diagrams
```

See diagrams:

- [Architecture](docs/diagrams/architecture.md)
- [ER Diagram](docs/diagrams/er-diagram.md)
- [Sequence Diagrams](docs/diagrams/sequences.md)

## AI Pipeline

```text
Invoice/OCR Text -> Field Extraction -> Validation -> Clause Chunking
-> Embeddings -> Vector Retrieval -> Prompt Contract -> Ollama LLM
-> Structured JSON -> Confidence/Fraud/Health Output
```

The platform stores warranty clauses as vectorized chunks in SQLite. Query-time retrieval ranks clauses semantically before analysis. If Ollama is unavailable, the deterministic local analyzer still returns a complete, structured response.

## Run Locally

```bash
pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
streamlit run app/app.py
```

Default seeded admin:

```text
username: admin
password: admin123
```

API docs are available at `http://localhost:8000/docs`.

## Configuration

Copy `.env.example` to `.env` and adjust:

```bash
VOLTA_ENV=development
DATABASE_URL=sqlite:///data/warranty_tracker.db
WARRANTY_APP_SECRET=change-this-secret-before-production
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1
ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
RATE_LIMIT_PER_MINUTE=120
```

For enhanced LLM reasoning:

```bash
ollama pull llama3.1
ollama serve
```

## Docker

```bash
docker compose up --build
```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:8501`

## API Surface

Core legacy and versioned routes are both supported:

- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- `GET /products`, `GET /products/{id}`
- `POST /customer/register-product`, `GET /customer/my-products`
- `POST /customer/service-requests`, `GET /customer/service-requests`
- `GET /admin/service-requests`, `PATCH /admin/service-requests/{id}`
- `GET /admin/analytics`
- `POST /api/v1/ai/search`
- `POST /api/v1/ocr/extract`
- `GET /api/v1/products/{customer_product_id}/qr`
- `GET /api/v1/qr/{token}`
- `GET /health`

## Database

The schema includes normalized operational and intelligence tables:

- `users`, `refresh_tokens`, `products`, `warranty_templates`, `warranty_clauses`
- `customer_products`, `service_requests`, `documents`
- `audit_logs`, `product_history`, `warranty_claim_history`, `repair_history`, `user_activity_logs`

Migrations are additive and safe for the existing SQLite database.

## Testing

```bash
PYTHONPATH=src pytest -q
```

Tests cover authentication, refresh tokens, product registration, AI claim creation, semantic search, and OCR extraction.

## Deployment Notes

- Set a strong `WARRANTY_APP_SECRET`.
- Restrict `ALLOWED_ORIGINS` to trusted frontend URLs.
- Mount `data/` as persistent storage.
- Run behind HTTPS in production.
- Replace the default admin password before external demos.

## Future Scope

- Real file upload OCR with Tesseract or a cloud OCR provider.
- FAISS/ChromaDB adapter for large warranty corpora.
- Email/SMS warranty expiry notifications.
- Multi-tenant manufacturer dashboards.
- Object storage for invoice images and ZIP uploads.

## License

Academic MVP / portfolio project. Add an organization-specific license before commercial use.
