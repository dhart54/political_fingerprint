# AGENTS.md — Political Behavior Fingerprint Platform

This file defines the operational rules, architecture, and guardrails for Codex CLI and any coding agents working in this repository.

Codex must follow this document unless explicitly overridden by the user.

---

# Core Product Identity (LOCKED)

This is a curiosity-led, trust-anchored civic analytics platform.

Primary promise:
"In 60 seconds, understand how this politician actually behaves."

This platform:

- Maps observable legislative behavior
- Uses deterministic analysis only
- Does NOT make moral judgments
- Does NOT rank politicians
- Does NOT infer motives or causality

Explicitly prohibited:

- Corruption claims
- Donor → vote causal claims
- Ranking language ("most extreme", "worst", etc.)
- Predictive modeling
- Net worth analysis
- Composite influence scoring

If a requested feature violates this, STOP and ask for clarification.

---

# MVP Scope (STRICT)

MVP includes ONLY:

1. Behavioral Fingerprint
   - Based on categorized policy votes only
   - Exclude procedural votes
   - Last 2-year rolling window
   - 8 issue domains
   - Raw % of categorized votes cast
   - Explicit 0% shown
   - Chamber median overlay default
   - Party toggle affects overlay only

2. Stability / Drift
   - Deterministic vector comparison only
   - No narrative inference

3. Plain-language summary
   - Descriptive only
   - Cached
   - Based only on deterministic data

4. ZIP code lookup
   - Returns House rep and both Senators

Do not implement phase-2 features unless explicitly instructed.

---

# Tech Stack (LOCKED)

Backend:

- Python 3.11+
- FastAPI
- Postgres (Supabase)

Frontend:

- Next.js (latest stable)
- Tailwind CSS

Deployment targets:

- Backend → Render
- Frontend → Vercel

Cost constraint:

- Must remain <$50/month
- Prefer precomputed aggregates over runtime computation

---

# Repository Structure (Authoritative)

Codex must maintain this structure exactly:

/backend
/app
/api
/classification
/etl
/metrics
/summaries
/db
/tests
/migrations

/frontend
/app
/components
/lib

/docs
/scripts

---

# Engineering Principles

Always prioritize:

1. Determinism
2. Transparency
3. Reproducibility
4. Low operational cost
5. Simplicity

Avoid:

- Premature abstraction
- Overengineering
- Hidden logic
- Magic constants without explanation

---

# Database Rules

All computed outputs must be stored in tables:

- fingerprints
- chamber_medians
- drift_scores
- vote_classifications
- summaries

API endpoints must read from precomputed tables, not compute on request.

---

# ETL Rules

ETL must be:

- Idempotent
- Deterministic
- Versioned (classification_version)
- Runnable locally

---

# Summary Generation Rules

Summary text must be:

Allowed:

- Descriptive
- Statistical
- Neutral

Forbidden words:

- corrupt
- extreme
- radical
- worst
- best
- biased
- bought

If these appear, rewrite summary.

---

# Development Workflow

Before major changes:

1. Create git commit checkpoint
2. Implement change
3. Run tests
4. Verify locally

Always add tests for:

- classification logic
- drift math
- API responses

---

# Commands Codex should use

Backend dev:
cd backend
uvicorn app.main:app --reload

Frontend dev:
cd frontend
npm run dev

Tests:
cd backend
pytest

---

# Codex Operational Behavior Rules

Codex must:

- Prefer modifying existing files over creating duplicates
- Keep changes minimal and targeted
- Not refactor unrelated code
- Not introduce new dependencies without justification

If uncertain about architecture decisions, ask before implementing.

---

# Methodology Documentation Requirement

Any logic implemented must also be reflected in:

/docs/methodology.md

---

# End of AGENTS.md
