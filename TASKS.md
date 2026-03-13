# TASKS.md — Master Build Plan (MVP)

This file defines the exact execution order Codex must follow to build the Political Behavior Fingerprint Platform from scratch.

Codex must complete tasks in order.

Do not skip steps.

Mark tasks complete as they are finished.

---

# Phase 0 — Repository Initialization

## Task 0.1 — Initialize project [COMPLETED]

- Initialize git repository
- Create required directory structure:

/backend
/backend/app
/backend/tests
/backend/migrations

/frontend
/frontend/app
/frontend/components
/frontend/lib

/docs
/scripts

- Create README.md
- Create .gitignore
- Create .env.example files

Completion criteria:

- Repo builds cleanly
- Structure matches AGENTS.md

---

# Phase 1 — Backend Foundation

## Task 1.1 — FastAPI scaffold [COMPLETED]

Create:

backend/app/main.py

Requirements:

- FastAPI server
- GET /health endpoint
- CORS enabled for localhost frontend

Completion criteria:

curl http://localhost:8000/health returns:

{"status":"ok"}

---

## Task 1.2 — Backend environment setup [COMPLETED]

Create:

backend/requirements.txt or pyproject.toml

Include:

fastapi
uvicorn
psycopg
pytest
python-dotenv

Completion criteria:

Backend runs locally.

---

## Task 1.3 — Database connection module [COMPLETED]

Create:

backend/app/db.py

Requirements:

- Reads DATABASE_URL
- Provides reusable connection/session

Completion criteria:

Connection test passes.

---

# Phase 2 — Database Schema

## Task 2.1 — Create migrations [COMPLETED]

Create migration files defining:

Tables:

- legislators
- bills
- roll_calls
- votes_cast
- vote_classifications
- fingerprints
- chamber_medians
- drift_scores
- summaries
- zip_district_map

Enums:

- issue_domain
- vote_position
- chamber

Completion criteria:

Migrations apply successfully.

---

# Phase 3 — Classification Engine

## Task 3.1 — Procedural exclusion rules [COMPLETED]

Create:

backend/app/classification/eligibility.py

Implement:

is_procedural()

Add tests.

Completion criteria:

Tests pass.

---

## Task 3.2 — Domain classification engine [COMPLETED]

Create:

backend/app/classification/classifier.py

Implement deterministic scoring.

Add tests.

Completion criteria:

Tests pass.

---

# Phase 4 — Metrics Engine

## Task 4.1 — Fingerprint calculation [COMPLETED]

Create:

backend/app/metrics/fingerprint.py

Completion criteria:

Correct vote share outputs.

---

## Task 4.2 — Drift calculation [COMPLETED]

Create:

backend/app/metrics/drift.py

Completion criteria:

Drift matches formula.

---

# Phase 5 — ETL Pipeline

## Task 5.1 — ETL scaffold [COMPLETED]

Create:

backend/app/etl/

Modules:

ingest.py
classify.py
compute.py

Completion criteria:

ETL runs without errors.

---

## Task 5.2 — Fixture dataset [COMPLETED]

Create:

backend/fixtures/

Include:

- legislators.json
- bills.json
- roll_calls.json
- votes.json

Completion criteria:

Fixture ETL populates database.

---

# Phase 6 — API Layer

## Task 6.1 — Fingerprint endpoint

Create:

GET /legislators/{id}/fingerprint

Completion criteria:

Returns fingerprint vector.

---

## Task 6.2 — Drift endpoint

Create:

GET /legislators/{id}/drift

Completion criteria:

Returns drift value.

---

## Task 6.3 — Summary endpoint

Create:

GET /legislators/{id}/summary

Completion criteria:

Returns cached summary.

---

## Task 6.4 — ZIP lookup endpoint

Create:

GET /lookup/zip/{zip}

Completion criteria:

Returns legislators.

---

# Phase 7 — Frontend Foundation

## Task 7.1 — Next.js scaffold

Create Next.js app.

Completion criteria:

Frontend runs locally.

---

## Task 7.2 — API connectivity

Frontend can call backend.

Completion criteria:

Health endpoint visible in UI.

---

# Phase 8 — Fingerprint UI

## Task 8.1 — Radar chart component

Create:

FingerprintRadar component.

Completion criteria:

Displays fingerprint and median overlay.

---

## Task 8.2 — Drift indicator

Create:

DriftIndicator component.

Completion criteria:

Displays drift score.

---

## Task 8.3 — Summary display

Display summary text.

Completion criteria:

Summary visible.

---

# Phase 9 — ZIP Lookup UI

Create ZIP input and legislator pages.

Completion criteria:

Lookup works end-to-end.

---

# Phase 10 — Documentation

## Task 10.1 — Methodology doc

Create:

docs/methodology.md

Completion criteria:

Matches AGENTS.md and SKILLS.md.

---

# Phase 11 — Testing and Validation

Ensure tests exist for:

- classification
- drift
- API endpoints

Completion criteria:

All tests pass.

---

# Completion Condition (MVP Complete)

MVP is complete when:

- ETL populates database
- API returns fingerprint and drift
- Frontend displays fingerprint and drift
- ZIP lookup works
- Summary works
- Tests pass

---

# End of TASKS.md
