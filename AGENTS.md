# AGENTS.md — Political Behavior Fingerprint Platform

This file defines the operational rules, architecture, and guardrails for Codex CLI and any coding agents working in this repository.

Codex must follow this document unless explicitly overridden by the user.

---

# Core Product Identity (LOCKED)

This is a curiosity-led, trust-anchored civic analytics platform.

Primary promise:
"In 60 seconds, understand how this politician actually behaves."

Long-term north star:
"Who is on my ballot, and what does the evidence show about how they act on the issues I care about?"

This platform:

- Maps observable legislative behavior
- Helps users inspect current officials and, eventually, upcoming candidates by ZIP code and ballot context
- Uses deterministic analysis only
- Does NOT make moral judgments
- Does NOT rank politicians
- Does NOT infer motives or causality
- Lets users compare their own stated issue preferences against observable voting records
- Separates recorded governing behavior from lower-confidence stated candidate positions

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

If a requested feature violates this, STOP and ask for clarification.

---

# Product Scope

The original MVP is complete. Product v2 may build beyond the MVP when the work preserves the locked product identity and deterministic methodology.

Core product surfaces:

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

9. Ballot and candidate expansion
   - ZIP lookup may expand from current officials to upcoming races when reliable election data is available
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
