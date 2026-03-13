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

LLMs may only generate descriptive summaries from deterministic inputs.

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

API endpoints must read ONLY from:

fingerprints
chamber_medians
drift_scores
summaries

Never compute on request.

---

# Cost Control Rule

Prefer:

precompute once → read many times

Avoid:

recompute per request

---

# Test Requirements

Codex must implement tests for:

classification correctness
drift correctness
API response structure

---

# End of SKILLS.md
