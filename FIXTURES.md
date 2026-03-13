# FIXTURES.md — Local Deterministic Test Dataset Spec (MVP)

This file defines the REQUIRED local fixture dataset used to validate the MVP end-to-end
without relying on live external APIs.

Codex must implement these fixtures exactly and ensure ETL + API + UI work against them.

Goal:

- Exercise every edge case (procedural exclusion, domain classification, explicit zeros, drift, medians, ZIP lookup, summary caching)
- Keep the dataset small and human-auditable

All fixture files must live under:

/backend/fixtures/

Recommended format: JSON (one file per entity) with stable IDs.

---

## 1) Fixture Entities Overview

Create these files:

/backend/fixtures/legislators.json
/backend/fixtures/bills.json
/backend/fixtures/roll_calls.json
/backend/fixtures/votes_cast.json
/backend/fixtures/vote_subject_tags.json (optional helper for classification)
/backend/fixtures/zip_district_map.csv (or .json)

The ETL must be able to ingest fixtures and populate DB tables.

---

## 2) Legislators Fixture (3 total)

Purpose:

- Provide chamber diversity
- Provide party diversity
- Ensure chamber median calculations are meaningful with a small sample

Create 3 legislators:

1. House Democrat

- bioguide_id: "H000001"
- name_display: "Alex Morgan"
- chamber: "house"
- state: "NC"
- district: "04"
- party: "D"
- in_office: true

2. Senate Republican

- bioguide_id: "S000001"
- name_display: "Jordan Lee"
- chamber: "senate"
- state: "NC"
- district: null
- party: "R"
- in_office: true

3. Senate Democrat

- bioguide_id: "S000002"
- name_display: "Taylor Nguyen"
- chamber: "senate"
- state: "NC"
- district: null
- party: "D"
- in_office: true

Notes:

- Use deterministic UUIDs or stable string IDs in fixtures and map them during ingest.

---

## 3) Issue Domains Coverage Requirement (8 domains)

The fixture roll calls MUST include at least one ELIGIBLE, clearly-classifiable policy vote
for EACH of the 8 domains:

1 ECONOMY_TAXES
2 HEALTH_SOCIAL
3 EDUCATION_WORKFORCE
4 ENVIRONMENT_ENERGY
5 NATIONAL_SECURITY_FOREIGN
6 IMMIGRATION_BORDER
7 JUSTICE_PUBLIC_SAFETY
8 INFRASTRUCTURE_TECH_TRANSPORT

Additionally:

- Include at least 2 procedural votes that MUST be excluded.
- Include at least 2 “low confidence / uncategorized” votes that MUST be marked ineligible (threshold test).
- Ensure at least one legislator has explicit 0% in at least 2 domains (by having no eligible votes in those domains).

---

## 4) Bills Fixture (12 total)

Create 12 bills with obvious cues for classification:

- committee names strongly aligned to a domain
- titles with clear keywords
- short summaries with clear keywords

Each bill must include:

- congress: 118 (or any constant)
- bill_type: "hr" or "s"
- bill_number: unique int
- title
- summary
- committee
- subjects: array of strings (optional)

Mapping (suggested):

- 8 bills: one per domain
- 2 bills: procedural-related (used only to create roll calls that should be excluded)
- 2 bills: ambiguous/uncategorized (should fail threshold)

---

## 5) Roll Calls Fixture (14 total)

Create 14 roll calls:

- 10 policy votes tied to bills (8 domain bills + 2 extra domain votes)
- 2 procedural votes (excluded)
- 2 low-confidence votes (ineligible)

Each roll call must include:

- chamber ("house" or "senate")
- rollcall_number
- vote_date (ISO timestamp)
- question (string)
- description (string)
- bill_ref (bill key used in fixtures)
- source_url (can be placeholder)

### 5.1 Procedural Roll Calls (2)

These MUST be flagged as procedural by eligibility rules:

A) Senate cloture vote:

- question includes "Cloture"
- description includes "cloture motion"

B) House motion to recommit / motion to table:

- question includes "Motion to Recommit" or "Motion to Table"

These must NOT appear in fingerprints, medians, or drift.

### 5.2 Low Confidence Roll Calls (2)

These MUST be marked is_eligible=false due to low classification confidence.
Examples:

- bill title "A bill to designate a commemorative week"
- bill summary vague and no committee match

These must NOT appear in fingerprints, medians, or drift.

---

## 6) Votes Cast Fixture

Every legislator must have recorded votes for each roll call (yea/nay/present/not_voting).
Purpose:

- Ensure API can compute included totals
- Ensure “not_voting” exists but still counts as a vote cast record (depending on how you define "cast"; for MVP, keep it in votes_cast but only include those roll calls that are eligible; the vote position does not affect category emphasis).

Rules:

- For eligible roll calls, all 3 legislators must have a vote record (yea/nay/present/not_voting).
- For procedural and low-confidence roll calls, also include vote records to prove they are correctly excluded.

Recommended pattern:

- Alex Morgan (House D): participates in all House roll calls; no Senate roll calls (unless you model cross-chamber, which you should not). For simplicity:
  - House roll calls: Alex votes.
  - Senate roll calls: Alex has no votes_cast rows.

- Jordan Lee (Senate R): votes on all Senate roll calls.
- Taylor Nguyen (Senate D): votes on all Senate roll calls.

This tests chamber-specific median logic correctly.

---

## 7) Window + Drift Construction (Critical)

The roll_call vote_date values MUST be arranged to create meaningful drift.

Define "now" at computation time as runtime current date, but fixtures must include dates relative to last 730 days.

Requirement:

- Create at least 6 eligible roll calls in the "early" half (older 365 days)
- Create at least 6 eligible roll calls in the "recent" half (newer 365 days)

Construct drift:

- For Jordan Lee (Senate R), early votes emphasize ECONOMY_TAXES and NATIONAL_SECURITY_FOREIGN.
- Recent votes emphasize IMMIGRATION_BORDER and JUSTICE_PUBLIC_SAFETY.
  This should yield a non-trivial L1 drift score (e.g., > 0.3).

For Taylor Nguyen (Senate D), keep emphasis relatively stable across halves (drift < 0.15).

For Alex Morgan (House D), keep total eligible votes below threshold 20 to trigger insufficient_data drift.

This ensures all drift code paths are exercised:

- stable
- drifting
- insufficient data

---

## 8) Expected Fingerprint Outcomes (Assertions)

Codex must add tests asserting:

1. Explicit zeros:

- At least one legislator has 0% in at least 2 domains, and API returns those domains with vote_share = 0.0 and vote_count = 0.

2. Procedural exclusion:

- Procedural roll calls do not appear in vote_classifications as eligible.
- They contribute 0 to fingerprints totals.

3. Low-confidence exclusion:

- Low-confidence roll calls are is_eligible=false.
- They contribute 0 to fingerprints totals.

4. Median overlay correctness:

- chamber_medians exist for:
  - senate: all, D, R
  - house: all, D, R (even if small; if only one party exists, median should equal that party’s only member, but still compute deterministically)

5. Drift:

- Jordan Lee drift_value > 0.3 (approx)
- Taylor Nguyen drift_value < 0.15 (approx)
- Alex Morgan drift marked insufficient_data

Codex may compute exact drift values from fixture counts and assert exact floats (preferred) or range checks.

---

## 9) ZIP Lookup Fixture

Create zip mapping fixture that supports at least 2 ZIPs:

ZIP 27701 (Durham, NC) -> House district NC-04, Senators are both NC senators.

ZIP 27601 (Raleigh, NC) -> House district NC-04 (or choose a different district if you want), Senators same.

Implement zip_district_map fixture with columns:

- zip
- state
- district

Lookup endpoint must return:

- House rep = Alex Morgan (NC-04)
- Senators = Jordan Lee + Taylor Nguyen

---

## 10) Summary Cache Fixture Expectations

Summary generation must work even without an API key.

Rules:

- On first request to /legislators/{id}/summary:
  - If cached summary missing, generate fallback deterministic summary and store in summaries table.
- On subsequent requests:
  - Return cached summary (no regeneration).

Codex must add an API test verifying cache behavior (e.g., created_at unchanged on second call).

---

## 11) Fixture Ingest Requirements

Codex must implement:

POST /etl/run-all (protected with ETL_API_KEY)
OR a CLI command:
python -m app.etl.run_all --fixtures

Ingest behavior:

- Upsert bills, roll_calls, legislators
- Insert votes_cast
- Classify roll calls
- Compute fingerprints, medians, drift
- Generate summaries only on request (not in ETL)

All operations must be idempotent.

---

## End of FIXTURES.md
