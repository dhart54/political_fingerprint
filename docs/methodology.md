# Methodology

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
