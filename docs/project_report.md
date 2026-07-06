# Project Report: VOLTA — Smart Warranty & Product Service Tracker

## 1. Problem statement
Customers routinely lose track of purchase dates, warranty terms, and coverage
exclusions for the appliances they own, which makes it hard to know whether a
malfunction is likely to be covered before filing a service request. VOLTA
gives customers a single place to register products against a company catalog,
raise a service request when something breaks, and get an immediate,
AI-assisted read on likely warranty coverage — while giving admins a queue to
review, annotate, and resolve those requests.

## 2. Approach
The system is a standard three-layer web app:

- **Data layer** — SQLite, accessed with raw `sqlite3` rather than an ORM so
  the schema (users, products, warranty templates, customer products, service
  requests, documents) stays fully visible in one file (`src/database.py`).
- **API layer** — FastAPI, with JWT-based auth and role checks (`customer` vs
  `admin`) enforced via dependency injection (`src/auth.py`).
- **Presentation layer** — Streamlit, chosen for fast iteration on a data-driven
  UI without hand-rolling a JS frontend, with a custom CSS layer laid on top
  to move it away from Streamlit's default look.

## 3. AI-assisted warranty analysis
When a customer raises a service request, the backend (`src/ai_service.py`)
sends the product's warranty coverage/exclusion text plus the customer's issue
description to a locally-running LLM (via Ollama). The model returns a
structured verdict — `LIKELY_COVERED`, `LIKELY_NOT_COVERED`, or
`NEEDS_INSPECTION` — along with a plain-English explanation and a document
checklist. If Ollama isn't reachable, or the model's output doesn't parse as
valid JSON with the required fields, the service falls back to a rule-based
keyword match rather than failing the request outright.

Running this locally (instead of calling a hosted API) means the analysis
works offline and keeps customer issue descriptions off a third-party service —
a reasonable default for a prototype handling appliance ownership data, though
response quality now depends on the model pulled and the machine it runs on.

## 4. Interface design
The interface direction is a neutral "liquid glass" aesthetic: frosted panels
built from layered `backdrop-filter` blur and saturation, a soft specular
sheen along the top edge of each card (an inset gradient at low opacity), and
an inset highlight/shadow pairing to fake a bit of surface depth without a
heavy drop shadow. The color palette was deliberately desaturated — misted
graphite-silver as the primary interactive tone, with muted gold, sage, and
terracotta reserved for status states (pending / resolved / rejected) — rather
than the saturated cyan/purple combination common in "cyber" dashboard themes,
so the product reads calmer and more materials-driven.

## 5. What's working
- Registration and login for customers, with a seeded admin account.
- Product catalog selection → registration with automatic warranty-window
  calculation from a per-product warranty template.
- Service request submission with AI (or fallback) coverage analysis attached.
- Admin queue: filter by status, review AI analysis, add technician notes,
  and transition ticket status.

## 6. Known limitations and next steps
- No file upload yet for proof-of-purchase or issue photos, though the
  `documents` table already exists in the schema for this.
- No automated tests.
- No deployment target — this runs locally only.
- No email/notification on status change.
- The AI verdict is explicitly a triage aid, not a binding decision; a human
  should still confirm coverage before a claim is rejected.

## 7. Repository layout
See the root `README.md` for the full folder structure and run instructions.
This report intentionally excludes the presentation deck, which is tracked
separately.
