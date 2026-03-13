# Methodology

## Product Scope and Guardrails

This MVP is a curiosity-led, trust-anchored civic analytics platform focused on observable legislative behavior.

The current product scope is limited to:

- behavioral fingerprint
- stability or drift indicator
- plain-language descriptive summary
- ZIP code lookup for one House representative and two senators

The methodology intentionally does not support:

- corruption claims
- donor-to-vote causal claims
- predictive modeling
- ranking language
- moral judgments
- composite influence scoring

## System Principles

Implemented logic follows these repository-wide priorities:

- determinism
- transparency
- reproducibility
- low operational cost
- simplicity

All metric-producing logic must remain a deterministic function of stored inputs.

## Stack and Deployment Assumptions

The current MVP implementation is built for:

- Python 3.11+ with FastAPI on the backend
- Postgres as the system database
- Next.js with Tailwind CSS on the frontend
- precompute-heavy deployment on Render and Vercel within the locked cost target

## Precomputed Data Rule

API endpoints must read precomputed outputs rather than computing metrics on request.

The authoritative computed outputs are:

- `vote_classifications`
- `fingerprints`
- `chamber_medians`
- `drift_scores`
- `summaries`

## Eligibility Rules

Vote eligibility is deterministic.

Procedural votes are excluded before classification, fingerprinting, median calculation, and drift calculation.

The current procedural exclusion rule marks a roll call as procedural when the vote question or description contains any of these case-insensitive keywords:

- `cloture`
- `motion to proceed`
- `quorum`
- `adjourn`
- `rule`
- `tabling`
- `recommit`
- `reconsider`
- `point of order`

If a procedural keyword is present:

- `is_eligible = false`
- `eligibility_reason = "procedural_vote"`

Otherwise:

- `is_eligible = true`
- `eligibility_reason = "policy_vote"`

## Classification Rules

Policy vote classification is deterministic and uses weighted scoring across three signal types:

- committee match: `+3`
- keyword match: `+2` per matched keyword
- subject-tag match: `+2` per matched subject tag

The classifier evaluates all 8 locked issue domains:

- `ECONOMY_TAXES`
- `HEALTH_SOCIAL`
- `EDUCATION_WORKFORCE`
- `ENVIRONMENT_ENERGY`
- `NATIONAL_SECURITY_FOREIGN`
- `IMMIGRATION_BORDER`
- `JUSTICE_PUBLIC_SAFETY`
- `INFRASTRUCTURE_TECH_TRANSPORT`

Inputs:

- committee name
- bill title
- bill summary
- subject tags

Process:

1. Normalize all text to lowercase.
2. Sum weighted committee, keyword, and subject-tag signals for each domain.
3. Select the highest-scoring domain.
4. If the top score is below `3`, mark the vote ineligible with `eligibility_reason = "low_classification_confidence"`.

Stored outputs:

- `primary_domain`
- `score_breakdown`
- `classification_version`

## Fingerprint Rules

Fingerprint calculation is deterministic and uses only eligible classified policy votes.

Window:

- rolling 730 days ending on the computation date

For each legislator and each locked issue domain:

- `vote_count` = count of eligible votes in that domain within the 730-day window
- `total_votes` = count of all eligible votes across all domains within the same window
- `vote_share` = `vote_count / total_votes`

Explicit-zero rule:

- if `vote_count = 0`, the domain row is still stored
- if `total_votes = 0`, then `vote_share = 0.0`

Fingerprint output always includes all 8 domains and never omits a domain row.

## Drift Rules

Drift is deterministic and uses the same 730-day window as the fingerprint.

Window split:

- early window: older 365 days
- recent window: newer 365 days

For each half-window, compute a domain share vector across the 8 locked issue domains.

Formula:

- `drift = 0.5 × sum(abs(P_recent[D] - P_early[D]))`

Constraints:

- `0 <= drift <= 1`
- if total eligible votes in the full 730-day window are fewer than `20`, then:
  - `insufficient_data = true`
  - `drift_value = null`

No estimation or extrapolation is used.

## ETL Order

The ETL pipeline is deterministic, idempotent in design, and versioned through `classification_version`.

Current operation order:

1. ingest fixture source records
2. evaluate procedural eligibility for each roll call
3. classify eligible policy votes into one primary domain
4. build eligible vote records for legislators
5. compute fingerprints
6. compute chamber medians
7. compute drift scores

In the current fixture-backed implementation, ingestion loads:

- legislators
- bills
- roll calls
- votes cast
- subject tags
- ZIP mappings

## Fixture Dataset

The local fixture dataset lives under `backend/fixtures/` and is the authoritative development dataset before live ingestion is introduced.

Current fixture implementation includes:

- 3 legislators
- 12 bills
- 14 roll calls
- 10 policy roll calls
- 2 procedural roll calls
- 2 low-confidence roll calls
- 2 ZIP mappings

The ETL fixture runner loads the fixture files, classifies roll calls deterministically, builds eligible votes, and computes fingerprints, chamber medians, and drift results in a local deterministic pass.

For this repository state, fixture design prioritizes the `10` policy roll call requirement. Under the locked drift threshold of `20` total eligible votes, that means fixture drift outputs remain `insufficient_data` for all three legislators.

## Fingerprint API

The fingerprint endpoint returns precomputed fingerprint rows only.

Default overlay behavior:

- chamber median overlay uses the `ALL` party grouping by default

Supported overlay toggle:

- `comparison_party=ALL`
- `comparison_party=D`
- `comparison_party=R`

The party toggle changes only the overlay median values. It does not change the legislator fingerprint itself.

## Drift API

The drift endpoint returns precomputed drift rows only.

Returned fields include:

- full 730-day window bounds
- early and recent half-window bounds
- total vote counts
- insufficient-data flag
- drift value

If a legislator is below the locked minimum vote threshold, the endpoint returns:

- `insufficient_data = true`
- `drift_value = null`

## Summary API

The summary endpoint returns cached summary text.

Current behavior:

- on first request, a deterministic fallback summary is generated from precomputed fingerprint and drift outputs
- the generated summary is cached and reused on later requests
- the cache key is based on legislator, window end, and classification version

The fallback summary is descriptive only and includes:

- vote volume
- the largest fingerprint emphasis areas
- drift availability or the insufficient-data condition

The summary layer must remain neutral:

- no causal claims
- no ranking language
- no motive inference
- no forbidden terms such as `corrupt`, `extreme`, `radical`, `worst`, `best`, `biased`, or `bought`

## ZIP Lookup API

The ZIP lookup endpoint returns fixture-backed legislator mappings for the requested ZIP code.

Returned data includes:

- ZIP code
- state
- congressional district
- House representative for that district
- both senators for that state

## Frontend API Connectivity

The frontend home page performs a client-side health check against `NEXT_PUBLIC_API_BASE_URL`.

Current behavior:

- requests `GET /health`
- renders connected, checking, or unavailable status in the UI
- displays the configured API base URL so the active backend target is visible

## Fingerprint Radar UI

The frontend radar chart renders:

- the legislator fingerprint polygon from `vote_share`
- the chamber median overlay polygon from `median_share`

Current UI behavior:

- overlay defaults to `ALL`
- the user can toggle overlay comparison between `ALL`, `D`, and `R`
- the toggle changes only the median overlay, not the fingerprint values

## Drift Indicator UI

The frontend drift indicator renders the drift API result directly.

Current UI behavior:

- shows the deterministic drift value when available
- shows the insufficient-data state explicitly when the backend returns `insufficient_data = true`
- surfaces early and recent vote totals alongside the indicator

## Summary UI

The frontend summary panel renders the cached summary endpoint response directly.

Current UI behavior:

- displays the summary text returned by the backend
- surfaces generation method, window end, classification version, and created timestamp
- does not generate or rewrite summary text on the client

## ZIP Lookup UI

The frontend ZIP lookup panel calls the ZIP lookup API directly from the home page.

Current UI behavior:

- defaults to fixture ZIP `27701` for local verification
- requests `GET /lookup/zip/{zip}`
- renders the returned district, House representative, and both senators
- surfaces request failures explicitly instead of inferring fallback data on the client
