# CONSTRAINTS.md — System Invariants and Non-Negotiable Rules

This document defines hard invariants that MUST NEVER be violated.

These constraints override implementation convenience.

If a requested change would violate these constraints, Codex must STOP and ask for clarification.

---

# Section 1 — Determinism Requirement (Absolute)

All computed outputs must be deterministic functions of stored database inputs.

The following must NEVER use LLM inference:

- vote eligibility
- vote classification
- fingerprint calculation
- chamber median calculation
- drift calculation

These must be reproducible exactly from database state.

Allowed LLM usage:

- summary generation ONLY
- summaries must be cached
- summaries must not influence any computed metric

---

# Section 2 — Fingerprint Mathematical Definition (Invariant)

Fingerprint is defined as:

For legislator L over window W:

Let:

eligible_votes = all votes where vote_classifications.is_eligible = true

For each domain D:

domain_vote_count(L,D,W) =
count of eligible votes cast by L in domain D during W

total_votes(L,W) =
sum over all domains of domain_vote_count(L,D,W)

Fingerprint share:

vote_share(L,D,W) =
domain_vote_count(L,D,W) / total_votes(L,W)

If domain_vote_count = 0:

vote_share MUST equal 0 exactly.

vote_share MUST NEVER be null.

vote_share MUST NEVER be omitted.

vote_share MUST NEVER be normalized against anything except total_votes.

---

# Section 3 — Eligibility Constraint

A vote MUST be excluded if procedural.

Procedural votes MUST NOT appear in:

- fingerprints
- drift
- medians

Procedural determination must be deterministic and versioned.

vote_classifications.is_eligible is authoritative.

---

# Section 4 — Domain Constraint

Each eligible vote MUST have exactly one primary_domain.

primary_domain MUST be one of the issue_domain enum values.

primary_domain MUST NOT be null for eligible votes.

Ineligible votes MUST NOT have primary_domain.

---

# Section 5 — Drift Mathematical Definition (Invariant)

Window W is split into:

early_window = older half of W
recent_window = newer half of W

Compute share vectors:

P_early[D]
P_recent[D]

Drift is defined as:

drift = 0.5 × sum over domains D of abs(P_recent[D] − P_early[D])

Drift MUST satisfy:

0 ≤ drift ≤ 1

If total eligible votes in W < 20:

drift MUST be marked insufficient_data

drift MUST NOT be estimated or extrapolated.

---

# Section 6 — Chamber Median Definition

For chamber C and domain D:

Collect all legislators in chamber C with total_votes ≥ minimum threshold.

Compute:

median_share(C,D) =
median of vote_share(L,D) across legislators L

Median MUST be computed independently for:

- all legislators
- Democrats
- Republicans

Median MUST be precomputed and stored.

Median MUST NOT be computed at request time.

---

# Section 7 — Precomputation Requirement

The following MUST be stored in database tables:

- fingerprints
- chamber_medians
- drift_scores
- vote_classifications
- summaries

API endpoints MUST read from these tables only.

API endpoints MUST NOT compute these dynamically.

---

# Section 8 — Versioning Requirement

The following MUST include version identifiers:

vote_classifications.classification_version
summaries.classification_version

If classification_version changes:

fingerprints MUST be recomputed
drift_scores MUST be recomputed
summaries MUST be regenerated

---

# Section 9 — Null Handling Constraint

The following MUST NEVER be null:

fingerprints.vote_share
fingerprints.vote_count
fingerprints.total_votes

If no votes exist:

vote_count MUST be 0
vote_share MUST be 0

---

# Section 10 — Time Window Constraint

Fingerprint window MUST be exactly:

rolling 730 days from computation timestamp.

Drift window split MUST be exactly:

early: older 365 days
recent: newer 365 days

No alternative window definitions allowed.

---

# Section 11 — API Contract Stability Constraint

The following API endpoints MUST remain stable:

GET /legislators/{id}/fingerprint
GET /legislators/{id}/drift
GET /legislators/{id}/summary
GET /lookup/zip/{zip}

Response field names MUST NOT change without explicit approval.

---

# Section 12 — Cost Constraint

The system MUST prefer:

precompute once → read many times

The system MUST avoid:

per-request heavy computation

The system MUST remain operable under $50/month hosting cost.

---

# Section 13 — Summary Neutrality Constraint

Summary generation MUST NOT include:

corrupt
extreme
radical
worst
best
biased
bought

Summary MUST be descriptive only.

Summary MUST NOT imply causation.

Summary MUST NOT rank legislators.

---

# Section 14 — Schema Integrity Constraint

Tables:

fingerprints
chamber_medians
drift_scores
vote_classifications

are authoritative outputs.

Other tables MUST NOT duplicate these values.

---

# Section 15 — Failure Behavior Constraint

If required inputs are missing:

System MUST return:

- insufficient_data status

System MUST NOT estimate missing values.

System MUST NOT fabricate data.

---

# End of CONSTRAINTS.md
