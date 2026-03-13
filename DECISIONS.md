# DECISIONS.md — Architectural & Product Decisions (MVP)

This file is the authoritative log of decisions already made for the MVP.
Codex must NOT revisit these choices unless explicitly instructed.

Format: Date — Decision — Rationale.

---

## 2026-02-28 — Product Identity (LOCKED)

Decision:

- Build a curiosity-led, trust-anchored civic analytics platform mapping observable legislative behavior.
- Not an outrage site, not a corruption accusation engine, not a partisan ranking system.

Rationale:

- Trust and clarity come from transparent, deterministic methodology and neutral presentation.

---

## 2026-02-28 — MVP Scope (LOCKED)

Decision:
MVP includes ONLY:

1. Behavioral Fingerprint (hero)
2. Stability/Drift indicator
3. Plain-language descriptive summary (cached)
4. ZIP code lookup (rep + 2 senators)

Explicitly excluded:

- Corruption claims
- Donor → vote causal claims
- Composite influence score
- Net worth overlays
- Predictive modeling
- Ranking language ("most extreme", "worst", etc.)
- Moral framing

Rationale:

- Establish trust and comprehension before any expansions.

---

## 2026-02-28 — Data Rules (LOCKED)

Decision:

- Categorized policy votes only
- Exclude procedural votes
- Last 2 years (rolling 730 days)
- Raw % of total categorized votes cast per domain
- Zero emphasis explicitly shown as 0%
- Default comparison overlay is chamber median
- Party toggle changes overlay only (All/D/R)

Rationale:

- Deterministic, interpretable, and resistant to subjective framing.

---

## 2026-02-28 — Issue Taxonomy (LOCKED for MVP)

Decision:
Use exactly 8 stable, broad domains:

1. Economy & Taxes
2. Health & Social Services
3. Education & Workforce
4. Environment & Energy
5. National Security & Foreign Policy
6. Immigration & Border Policy
7. Justice & Public Safety
8. Infrastructure, Tech & Transportation

Rationale:

- Broad, recognizable, stable across time; avoids culture-war coding.

---

## 2026-02-28 — Drift Metric (LOCKED for MVP)

Decision:

- Drift is deterministic L1 distance:
  drift = 0.5 × sum(|P_recent[D] − P_early[D]|)
- Window split: early 365 days + recent 365 days
- Insufficient data threshold: total eligible votes < 20

Rationale:

- Interpretable, bounded [0,1], and deterministic.

---

## 2026-02-28 — Architecture (LOCKED)

Decision:

- Backend: FastAPI (Python 3.11+)
- Frontend: Next.js + Tailwind
- Database: Supabase Postgres
- Deployment: Render (API) + Vercel (Frontend)
- Cost target: <$50/month

Rationale:

- Low-ops, scalable, and aligns with precompute/read-many design.

---

## 2026-02-28 — Precompute Rule (LOCKED)

Decision:

- All computed outputs must be precomputed and stored:
  - fingerprints
  - chamber_medians
  - drift_scores
  - vote_classifications
  - summaries (cached)
- API must read from these tables only.

Rationale:

- Cost control, performance, and reproducibility.

---

## 2026-02-28 — Classification Approach (LOCKED for MVP)

Decision:

- Deterministic scoring using:
  - committee mapping weights
  - keyword pattern weights
  - subject tag weights (when available)
- Low confidence classifications are marked ineligible (not forced into a domain)
- Store score_breakdown JSON and classification_version

Rationale:

- Transparent, auditable, and reproducible.

---

## 2026-02-28 — Summary Generation (LOCKED for MVP)

Decision:

- LLM is permitted ONLY for plain-language summaries.
- Summaries must be descriptive only, cached, and never affect metrics.
- Provide deterministic fallback summary when no API key is present.

Rationale:

- Improves comprehension while maintaining trust and determinism.

---

## 2026-02-28 — Fixtures-First Development (LOCKED)

Decision:

- Build against local fixtures defined in FIXTURES.md before adding live data sources.

Rationale:

- Prevents early pipeline instability and ensures deterministic correctness.

---

## End of DECISIONS.md
