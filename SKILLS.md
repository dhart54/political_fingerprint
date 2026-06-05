# SKILLS.md — Deterministic Civic Fingerprint Implementation Guide

This file defines the exact implementation patterns Codex must use for classification, fingerprints, drift, ETL, and summaries.

Codex must follow these patterns unless explicitly overridden.

---

# Core Principle: Determinism Only

All outputs must be reproducible from stored inputs.

Never use LLM inference for:

- classification
- fingerprint math
- drift math
- eligibility
- vote meaning
- evidence tier
- readiness status
- support/opposition counting
- alignment

LLMs may only help draft cached/source-grounded plain-language explanations from deterministic stored inputs.

---

# Issue Domains (LOCKED)

Use exactly these 8 domains:

ECONOMY_TAXES
HEALTH_SOCIAL
EDUCATION_WORKFORCE
ENVIRONMENT_ENERGY
NATIONAL_SECURITY_FOREIGN
IMMIGRATION_BORDER
JUSTICE_PUBLIC_SAFETY
INFRASTRUCTURE_TECH_TRANSPORT

Store as enum in database.

---

# Vote Eligibility Rules

A vote is eligible ONLY if it is policy-related.

Procedural votes must be excluded.

Procedural keywords include:

cloture
motion to proceed
quorum
adjourn
rule
tabling
recommit
reconsider
point of order

Store:

is_eligible boolean
eligibility_reason text

---

# Classification Algorithm

Classification must use weighted deterministic scoring.

Inputs:

- committee name
- bill title
- bill summary
- subject tags

Process:

1. Assign weights to domain signals
2. Sum weights per domain
3. Select highest score
4. If score below threshold → mark ineligible

Store:

primary_domain
score_breakdown JSON
classification_version

Example score_breakdown:

{
"ENVIRONMENT_ENERGY": {
"committee_match": 3,
"keyword_match": 2
}
}

---

# Fingerprint Calculation

Window: rolling 730 days from current date.

For legislator L and domain D:

vote_share = domain_vote_count / total_eligible_votes

If no votes in domain:

vote_share = 0

Store:

domain_vote_count
vote_share
total_votes

Never compute at request time. Always precompute.

---

# Chamber Median Calculation

For each chamber and domain:

median_share = median(vote_share across legislators)

Also compute for:

- All legislators
- Democrats only
- Republicans only

Store separately.

---

# Drift Calculation

Split window into:

early = older 365 days
recent = newer 365 days

Compute share vectors:

P_early[D]
P_recent[D]

Drift formula:

drift = 0.5 × sum(|P_recent[D] − P_early[D]|)

Range:

0 = no change
1 = complete change

If total votes < 20:

mark insufficient_data

Store drift_value and vote counts.

---

# ETL Order of Operations

Correct ETL sequence:

1. ingest roll_calls
2. ingest votes_cast
3. ingest bills
4. compute eligibility
5. compute classification
6. compute fingerprints
7. compute medians
8. compute drift

Each step must be idempotent.

---

# Summary Generation Pattern

Summary inputs:

- fingerprint vector
- drift value
- total votes
- top domains

Summary must:

- describe emphasis
- describe stability/drift
- describe vote volume

Summary must NOT:

- infer motives
- judge
- rank

Cache summaries in database.

Key:

legislator_id
window_end
classification_version

---

# API Data Flow Rule

Shared heavy metrics must read from precomputed tables:

- fingerprints
- chamber_medians
- drift_scores
- vote_classifications
- summaries

Position-by-issue and evidence drilldown may read from stored deterministic tables such as:

- votes_cast
- roll_calls
- bills
- vote_classifications
- vote_interpretations
- vote_contexts, if present
- stored source fields / source URLs

User-specific alignment may be computed on request only as a lightweight comparison between:

- explicit user-selected preferences
- stored vote_interpretations
- stored votes_cast positions

The API must not perform vote classification, vote interpretation, source inference, or heavy aggregation at request time.

---

# Vote Interpretation Pattern

Vote interpretation records must be source-grounded and stored.

Each interpreted row should identify, where determinable:

- roll_call_id
- support_position
- oppose_position
- interpretation_status
- interpretation_reason
- what_happened
- why_it_mattered
- what_not_to_infer
- source_basis or source_url
- interpretation_version or classification_version

If yea/nay meaning is ambiguous or unsupported, mark ambiguous or insufficient_evidence.

Ambiguous/insufficient/procedural rows must not count toward support/opposition patterns.

Not-voting rows may explain bill substance but must not count as support or opposition.

---

# Readiness-First Profile Pattern

The representative profile should lead with issue areas where reviewed evidence is strongest.

Readiness labels are presentation/evidence-confidence labels, not ideology labels.

Use:

- Strong Evidence
- Mixed But Interpretable
- Limited Evidence
- Not Enough To Summarize

Limited evidence should remain visible but cautious.

Highest vote volume is not necessarily the clearest reviewed issue read.

The app should distinguish "most recorded votes" from "clearest reviewed vote meaning."

---

# Evidence Confidence Labels

Use these evidence confidence labels:

- Reviewed meaning: source-grounded vote meaning is available.
- Limited context: row remains visible but practical effect is limited or procedural.
- Needs source support: row lacks enough source detail for confident interpretation.
- Not counted: row does not count toward support/opposition due to not-voting, ambiguity, insufficiency, or procedural status.

---

# Grouped Evidence Pattern

Related evidence rows may be grouped using stable bill/measure identifiers first.

Normalized title/measure text may be a fallback.

Broad issue domain or issue_facet alone must not be used as a grouping key.

Grouped evidence is for scanability only.

Grouping must not change support/opposition counting, alignment, or interpretation status.

Procedural/amendment groups must not be presented as final policy claims unless source support exists.

---

# User Alignment Pattern

Alignment language may only be used when the user has provided explicit issue preference direction.

When no directional preference is selected, use neutral record/evidence language.

Alignment labels must be evidence-based and limited to terms like aligned, not aligned, mixed, or insufficient evidence.

Alignment must not rank politicians, infer ideology, or recommend votes.

---

# Cost Control Rule

Prefer:

precompute once → read many times

Avoid:

recompute per request

---

# Test Requirements

Codex must implement tests for:

- classification correctness
- drift correctness
- API response structure
- vote interpretation status handling
- ambiguous/insufficient rows excluded from support/opposition patterns
- not-voting rows excluded from support/opposition
- readiness grouping/order
- grouped evidence preserving counts
- no forbidden recommendation/motive/ranking language

---

# End of SKILLS.md
