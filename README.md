# VOLTA — Smart Warranty & Service Tracker

I built this as part of my SDAI Himshikhar program at IIT Mandi. The idea is simple: most people (including me) never remember when they bought something or what the warranty actually covers, so when a product breaks you're just guessing whether it's covered or not. VOLTA fixes that — customers register their products when they buy them, and when something goes wrong they file a request and get an instant AI read on whether it's likely covered, based on that product's actual warranty terms. Admins get a dashboard to review and close out all the requests.

## What it's built with
- **Frontend:** Streamlit — went with a neutral, frosted-glass look instead of the usual neon dashboard style
- **Backend:** FastAPI
- **DB:** plain SQLite, no ORM, so I could actually see and control the schema myself
- **AI:** runs locally through Ollama for the warranty analysis, with a rule-based fallback if Ollama isn't running

## Folder structure
```
VOLTA/
│
├── data/
│   └── warranty_tracker.db     # gets created + seeded automatically the first time you run it
│
├── src/                        # FastAPI backend
│   ├── main.py                 # all the API routes
│   ├── database.py             # schema + seed data
│   ├── auth.py                 # login/JWT stuff
│   ├── schemas.py               # request/response models
│   └── ai_service.py            # talks to Ollama for the warranty verdict
│
├── app/                        # Streamlit frontend
│   ├── app.py
│   └── assets/                 # logo + product images
│
├── docs/
│   └── project_report.md       # writeup of how I approached this
│
├── requirements.txt
└── README.md
```

I skipped the `notebooks/` folder from the usual template since there's no data science/EDA part to this — it's an app, not a model.

## How to run it

Run these two commands from the repo root:

### Backend
```bash
cd src && pip install -r ../requirements.txt && uvicorn main:app --reload --port 8000
```

### Frontend
```bash
pip install -r requirements.txt && streamlit run app/app.py
```

The backend will create the local SQLite database on first run, and the frontend will open on the Streamlit URL shown in the terminal.

## How it actually works
1. Login screen with two tabs — login and register (only customers can self-register, admin is seeded in).
2. Customer picks a product from the catalog, registers it with a serial number and purchase date, and the warranty window gets calculated automatically off that product's template.
3. When they raise a service request, the backend sends the issue description + that product's coverage/exclusion text to the local LLM, which comes back with a verdict (`LIKELY_COVERED` / `LIKELY_NOT_COVERED` / `NEEDS_INSPECTION`), an explanation, and a list of documents they'd need.
4. Admin sees every request across all customers, can filter by status, read the same AI verdict, add notes, and move the ticket along.

## Why it looks the way it does
I wanted the UI to feel calmer than the typical cyan-on-black "hacker dashboard" look most of these projects end up with. So everything's frosted glass panels with layered blur, a soft light sheen along the top edge of each card, and toned-down colors — muted silver-grey as the main accent, and soft gold/sage/rust for status states instead of bright yellow/green/red.

## What's done vs. what I still want to add
**Done:** login/auth with JWT and roles, product catalog + registration with auto warranty calc, service requests with AI analysis, admin dashboard with filtering, notes, and status updates.

**Still on my list:**
- actual file upload for proof of purchase / photos (the `documents` table is already there, just not wired up)
- automated tests
- email notifications on status change
- deploying this somewhere instead of just running it locally

## A few honest caveats
- The AI verdict is meant to speed up triage, not replace a human — someone should still sanity-check before rejecting a claim.
- If Ollama isn't running, it falls back to basic keyword matching, which doesn't really understand negation (there's a comment about this in `ai_service.py`). Get Ollama running for it to actually work well.
- Smaller local models are inconsistent about returning clean JSON — `ai_service.py` strips out code fences/preambles and checks the required fields before trusting the output, and falls back to the rule-based method if it can't parse it.
- Change the default admin password before you show this to anyone outside your laptop.
- The JWT secret is set via the `WARRANTY_APP_SECRET` env variable — the code has a dev default baked in, don't ship that as-is.
