# PHASE2_ROADMAP.md — Post-MVP Build Plan

This file defines the recommended execution order for improving the Political Fingerprint platform after MVP completion.

This roadmap does not change the locked MVP scope in `TASKS.md`.

Do not skip steps without a deliberate product decision.

Mark roadmap items complete as they are finished.

---

# Phase A — Real Data Backbone

## Task A.1 — Postgres-backed read layer

Replace fixture-backed API reads with database-backed reads for:

- fingerprints
- chamber_medians
- drift_scores
- summaries
- zip_district_map

Requirements:

- keep current API response shapes stable
- read precomputed tables only
- preserve current deterministic behavior

Completion criteria:

- all current API tests still pass against the database-backed read layer

---

## Task A.2 — Database seed for local development

Create a deterministic seed flow that loads fixture outputs into Postgres for local runs.

Requirements:

- runnable locally
- idempotent
- compatible with current fixture dataset

Completion criteria:

- local database can be populated from fixtures with one command

---

# Phase B — Legislator Discovery

## Task B.1 — Legislator search endpoint

Create:

GET /legislators/search

Requirements:

- search by display name
- return chamber, party, state, and id
- deterministic ordering for ties

Completion criteria:

- frontend can discover legislators without hardcoded ids

---

## Task B.2 — Frontend legislator picker

Add a legislator search and selection flow to the home page.

Requirements:

- user can switch away from the sample legislator
- fingerprint, drift, and summary update together
- current layout remains usable on desktop and mobile

Completion criteria:

- user can select at least 3 fixture legislators through the UI

---

# Phase C — Production ETL

## Task C.1 — Persistent ETL writes

Update ETL to write computed outputs into Postgres tables.

Requirements:

- write vote classifications
- write fingerprints
- write chamber medians
- write drift scores
- preserve classification_version handling

Completion criteria:

- ETL populates the database rather than returning in-memory outputs only

---

## Task C.2 — Summary cache persistence

Move summary caching from in-memory behavior to the `summaries` table.

Requirements:

- cache key uses legislator, window end, and classification_version
- fallback summary remains deterministic when no LLM key is present
- forbidden summary language remains blocked

Completion criteria:

- repeated summary requests reuse stored summary rows

---

## Task C.3 — Live ingestion adapter

Add the first non-fixture ingestion adapter for real legislative source data.

Requirements:

- keep fixture ingestion intact for local validation
- normalize source data into existing schema
- document source assumptions clearly

Completion criteria:

- ETL can run from a real source into the same precomputed tables

---

# Phase D — Product Trust and Usability

## Task D.1 — Data provenance UI

Add visible provenance details near the fingerprint and summary.

Include:

- last updated time
- computation window end
- classification version
- concise methodology link or explainer

Completion criteria:

- users can see when the data was computed and what rules produced it

---

## Task D.2 — Summary UX refinement

Improve the summary presentation without changing its neutrality rules.

Requirements:

- make summary easier to scan
- preserve descriptive-only language
- do not add rankings or causal claims

Completion criteria:

- summary is visually scannable in 10 seconds or less

---

## Task D.3 — Error and empty-state polish

Improve API and UI handling for:

- unknown ZIPs
- missing legislator ids
- missing summaries
- backend unavailable state
- no-data cases

Completion criteria:

- all major user-facing failure states are understandable without reading technical errors

---

# Phase E — Comparison Experience

## Task E.1 — Comparison mode API support

Add backend support for comparing two legislators side by side.

Requirements:

- preserve current single-legislator endpoints
- expose stable comparison response shapes
- avoid ranking language

Completion criteria:

- frontend can request data for two legislators in one comparison flow

---

## Task E.2 — Side-by-side comparison UI

Add a comparison mode for fingerprints, drift, and summaries.

Requirements:

- side-by-side fingerprints
- clear labeling of each legislator
- no “winner” framing

Completion criteria:

- user can compare two legislators without ambiguity

---

# Phase F — Deployment and Operations

## Task F.1 — Render backend deployment

Prepare the FastAPI service for Render.

Requirements:

- production start command
- environment variable documentation
- health check path

Completion criteria:

- backend deploys successfully on Render

---

## Task F.2 — Vercel frontend deployment

Prepare the Next.js app for Vercel.

Requirements:

- production API base URL configuration
- environment documentation
- successful production build in hosted environment

Completion criteria:

- frontend deploys successfully on Vercel

---

## Task F.3 — Monitoring and runbook

Add lightweight operational documentation.

Include:

- deploy steps
- ETL run steps
- rollback notes
- basic failure checks

Completion criteria:

- a new maintainer can deploy and diagnose the MVP without tribal knowledge

---

# Recommended Order

Highest-value sequence:

1. Task B.1
2. Task B.2
3. Task A.1
4. Task A.2
5. Task C.1
6. Task C.2
7. Task D.1
8. Task D.2
9. Task D.3
10. Task F.1
11. Task F.2
12. Task F.3

If the goal is public launch readiness, prioritize deployment tasks immediately after A.1 and A.2.

---

# Completion Condition

Post-MVP Phase 2 is meaningfully complete when:

- users can choose legislators dynamically
- API reads from real precomputed database tables
- ETL writes persistent outputs
- provenance is visible in the UI
- deployment is documented and working

---

# End of PHASE2_ROADMAP.md
