# AGENTS.md — Political Behavior Fingerprint Platform

This file defines the operational rules, architecture, and guardrails for Codex CLI and any coding agents working in this repository.

Codex must follow this document unless explicitly overridden by the user.

---

# Core Product Identity (LOCKED)

This is a curiosity-led, trust-anchored civic analytics platform.

Primary promise:
"In 60 seconds, understand how this politician actually behaves."

Long-term north star:
"Who represents me, how are they acting on the issues I care about, and what can I do next?"

This platform:

- Maps observable legislative behavior
- Helps users inspect current officials first and, secondarily, upcoming candidates by ZIP code and election context
- Uses deterministic analysis only
- Does NOT make moral judgments
- Does NOT rank politicians
- Does NOT infer motives or causality
- Lets users compare their own stated issue preferences against observable voting records
- Separates recorded governing behavior from lower-confidence stated candidate positions
- Helps users take neutral civic actions such as contact, ask, thank, or track, without electoral persuasion

Explicitly prohibited:

- Corruption claims
- Donor → vote causal claims
- Ranking language ("most extreme", "worst", etc.)
- Predictive modeling
- Net worth analysis
- Composite influence scoring
- Prescriptive voting advice ("vote for", "vote against", "should vote for")
- Personalized electoral persuasion
- Treating campaign statements as equivalent to recorded governing behavior
- Auto-generating persuasive constituent messages that tell users what position to take

If a requested feature violates this, STOP and ask for clarification.

---

# Product Scope

The original MVP is complete. Product v2 may build beyond the MVP when the work preserves the locked product identity and deterministic methodology.

---

# Current v2 Product Direction — Readiness-First Accountability Profile

The current v2 product direction is a readiness-first accountability profile.

- The product is an evidence-based accountability profile, not an ideology score.
- The representative page should lead with the strongest reviewed issue reads.
- Limited evidence should remain visible but cautious.
- Position-by-issue, vote interpretation, readiness labels, grouped evidence, and evidence drilldown are current v2 surfaces.
- LLMs may draft cached/source-grounded explanations, but must not decide eligibility, vote meaning, alignment, readiness, or evidence tier.

---

Core product surfaces:

0. Representative Accountability Dashboard
   - Primary v2 surface
   - Starts from current House representative and both Senators by ZIP code
   - Centers issue evidence, interpreted vote meaning, readiness, grouped evidence, and source-backed accountability
   - Election context remains secondary to the current representative record

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

5. Position by Issue
   - Shows recorded yea/nay behavior within issue domains
   - Descriptive only
   - Does not infer ideology, motive, or causal explanations

6. User-defined issue alignment
   - Users may select issue domains and preference directions
   - Alignment must be computed from stored votes, stored classifications, and deterministic vote-interpretation records
   - Alignment language must be evidence-based: aligned, not aligned, mixed, or insufficient evidence
   - Alignment must never become a politician ranking or voting recommendation

7. Evidence drilldown
   - Every alignment or vote-direction claim must be traceable to underlying roll calls, bill metadata, vote position, classification reason, and source URL when available

8. Vote interpretation
   - Interpretation of what yea/nay meant may be stored and surfaced only when source-grounded
   - Ambiguous or unsupported vote meaning must be marked insufficient evidence
   - LLMs may help draft cached plain-language explanations, but may not decide vote classification, eligibility, vote meaning, or alignment

9. Civic action / contact layer
   - Lets users contact, ask, thank, or track current representatives from evidence pages
   - Actions must be user-directed and neutral in framing
   - The product may help summarize the underlying evidence and provide contact metadata
   - The product must not tell users what position to take or generate electoral persuasion
   - Tracked actions must be clearly separate from vote classification, interpretation, and alignment math

10. Ballot and candidate expansion
   - ZIP lookup may expand from current officials to upcoming races when reliable election data is available
   - Election and challenger context is secondary to current representative accountability
   - Incumbents and prior officeholders should be evaluated first through recorded governing behavior
   - New candidates may use sourced stated positions only when no governing record exists
   - Stated-position reads must be clearly labeled as lower confidence than recorded votes
   - Candidate comparison must remain evidence-tiered, neutral, and non-prescriptive

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
- vote_interpretations

User-specific alignment may be computed on request from precomputed vote_interpretations and the user's explicit preferences, because preferences are session inputs. Heavy shared aggregates must still be precomputed.

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

Summary and explainer text must be:

Allowed:

- Descriptive
- Statistical
- Neutral
- Source-grounded
- Explicit about insufficient evidence

Forbidden words:

- corrupt
- extreme
- radical
- worst
- best
- biased
- bought

If these appear, rewrite summary.

Forbidden directives:

- "you should vote for"
- "you should vote against"
- "support this candidate"
- "oppose this candidate"

If these appear, rewrite the text into neutral evidence language.

---

# Development Workflow

Use milestone-sized branches for related product work.

- Work on milestone branches.
- Do not open PRs unless the user explicitly asks.
- Do not stop after one small task if the milestone is not complete.
- A milestone is complete only when the user-facing outcome is materially achieved, tests/build pass, and a progress summary is provided.
- If a task takes only a few minutes and is not risky, continue to the next related milestone item instead of opening a PR.
- Keep changes cohesive to the active milestone.
- Do not broaden rollout, add new interpretation data, or change product claims unless explicitly requested.

Always add or update tests for:

- classification logic
- drift math
- API responses
- issue readiness, vote-card, alignment/copy, grouped evidence, or profile behavior when those surfaces change

---

# Approval Boundaries

Allowed without asking:

- in-repo code edits for the active milestone
- tests/build
- docs/review packets tied to the milestone

Ask first before:

- backend/API behavior changes
- database migrations
- counting/alignment logic changes
- dependency installs/upgrades
- deploys
- destructive git commands
- process/port killing
- local launch script creation
- source enrichment ingestion

---

# Stopping And Reporting Rules

When stopping, report:

- what changed
- product outcome achieved
- files changed
- tests/build status
- blockers
- whether the user should continue, review, or request PR

---

# Commands Codex should use

Windows direct backend command:

```powershell
cd backend
.\.venv_win\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Do not use `uvicorn --reload` as the default Codex/Windows path.

Frontend:

```powershell
cd frontend
npm run dev
```

If the Codex-managed shell hits Next.js `spawn EPERM`, report it and stop. The user may run local launch manually from normal Windows PowerShell or a VS Code terminal. Do not create or patch local launch scripts unless explicitly requested.

Tests:

```powershell
cd backend
pytest
```

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
