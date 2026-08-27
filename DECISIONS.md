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

## 2026-06-05 — Product v2 Direction: Readiness-First Accountability Profile

Decision:

- The original fingerprint/drift/summary/ZIP MVP remains historically locked and complete.
- Product v2 expands the user-facing surface into a readiness-first representative accountability profile.
- The representative page should lead with the strongest reviewed issue reads first, then mixed but interpretable sections, then limited evidence, then not-enough-to-summarize sections.
- Issue sections may include interpreted vote meaning, readiness labels, grouped evidence previews, confidence labels, and evidence drilldowns.
- Limited, ambiguous, procedural, insufficient, and not-voting rows must remain visible where useful, but must not be forced into confident issue patterns.
- "Reviewed evidence" language is preferred over implying comprehensive voting-record coverage.
- This product remains an evidence-based accountability profile, not an ideology score, ranking system, or voting recommendation tool.

Rationale:

- The scale-readiness work showed that evidence quality varies materially by issue domain and vote type.
- A readiness-first experience helps users start where the evidence is strongest while preserving transparency around limited evidence.
- This direction keeps the product useful without overclaiming from sparse or procedural data.

---

## 2026-06-05 — Vote Interpretation and Evidence Readiness Guardrails

Decision:

- Vote interpretation may be surfaced only when source-grounded and stored in deterministic records.
- LLMs may help draft cached plain-language explanations, but must not decide eligibility, domain classification, vote meaning, evidence tier, readiness status, support/opposition counting, or alignment.
- Readiness labels are presentation/evidence-confidence labels, not ideology labels.
- Alignment language may be used only when tied to explicit user preference inputs and stored vote interpretations.
- When no directional user preference is selected, use neutral record/evidence language rather than aligned/not-aligned framing.

Rationale:

- The product must preserve trust by separating source-backed evidence, deterministic classifications, user preferences, and explanatory language.
- Better future source enrichment should move rows from insufficient/contextual toward stronger evidence; it should not weaken the underlying guardrails.

---

## 2026-06-05 — Workflow Direction for Codex Work

Decision:

- Current product work should use milestone branches, not one PR per tiny cleanup.
- Codex should not open PRs unless explicitly instructed.
- A milestone is complete when the user-facing outcome is materially achieved, tests/build pass, and a progress summary is provided.
- Local launch/debugging and dev-tooling work should be separated from product implementation unless explicitly requested.

Rationale:

- The project has moved past original MVP scaffolding into product iteration.
- Milestone-based work reduces micro-PR churn and keeps implementation tied to product outcomes.

---

## 2026-08-26 — Shared Legislative Corpus Boundary V1

Decision:

- Future editorial authoring uses five layers: Shared Action Core, Shared Issue
  Mapping, Member Action Projection, the existing Editorial Semantic IR member
  analytical result, and the existing reviewed presentation/publication stack.
- One exact House action/governed-source version has one member-neutral meaning
  identity. Party and member identity cannot alter that meaning, action stage,
  chamber outcome, package/amendment boundary, or issue organization.
- Political Fingerprint taxonomy is separate from intrinsic action truth, and
  member uniqueness begins with official action projection and downstream
  analytical aggregation.
- The existing Semantic IR compiler is retained behind a deterministic adapter.
- Existing accepted member-scoped artifacts remain historical provenance and
  are not rewritten by storage migration.

Rationale:

- M0 proved 37 Justice actions could be reused across Foushee and Grothman with
  zero regenerated meanings and distinct member results. M14A makes that
  audit-only architecture a typed, fail-closed authoring contract without
  changing accepted semantics, production, publication, or presentation.

---

## 2026-08-26 — Shared Legislative Corpus Boundary V1 integrity correction

Decision:

- Shared Action Core and reusable Member Action Projection artifacts use a
  chamber/Congress namespace; Political Fingerprint domains do not enter their
  artifact identities or storage paths.
- Member Action Projection binds only Shared Action Core action identities,
  digests, and governed member-action evidence. Shared Issue Mapping is a
  separate adapter input and cannot force projection regeneration.
- Shared source roles resolve to the exact action's governed identities, and a
  member-action source must match the core's governed action/outcome identity.

Rationale:

- These corrections enforce the five-layer boundary accepted for M14A without
  changing any of the 37 migrated Justice meanings or the retained Semantic IR
  compiler.

---

## End of DECISIONS.md
