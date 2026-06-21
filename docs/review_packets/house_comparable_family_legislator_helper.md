# House Comparable Family Legislator Helper

Branch: `codex/house-family-legislator-helper`  
Base: `main` at `6f3f367f074af22b149892ed71c39bdfb9dc541d`

## Summary

This milestone adds a bounded internal backend helper that joins a House legislator to the reviewed versioned comparable-family artifact:

`house-comparable-policy-question-families-v1`

Helper module:

`backend/app/analysis/house_comparable_family_legislator.py`

The helper supports future internal backend/API work for `Record Across Congresses`. It does not expose a public endpoint, frontend component, schema, migration, production write path, or continuity/change label.

## What The Helper Exposes

`get_house_comparable_family_legislator_evidence(legislator_identifier)` returns:

- `legislator_identifier`
- `artifact_version_used`
- `eligible_comparable_families_considered`
- legislator reference metadata
- one row per artifact-eligible comparable family
- explicit non-authorization metadata

Each family row includes:

- `family_id`
- `family_name`
- `issue_domain`
- `comparability_status`
- `governing_question`
- `caveats_and_limitations`
- `family_eligibility_flag`
- `congresses_represented_in_artifact`
- `roll_call_ids_considered_by_congress`
- `counts_by_congress`
- `has_family_vote_in_both_congresses`
- `has_direct_family_vote_in_both_congresses`
- `has_conditional_family_vote_in_both_congresses`
- `record_across_congresses_display_eligible`
- family-level non-authorization metadata

`counts_by_congress` includes:

- `roll_call_ids_considered`
- `cast_substantive_yes_count`
- `cast_substantive_no_count`
- `not_voting_count`
- `present_count`
- `missing_no_record_count`
- `total_artifact_roll_calls`
- `total_cast_substantive_yes_no_rows`

## What It Does Not Expose

The helper does not expose or generate:

- continuity/change claims;
- behavioral movement claims;
- ideological movement claims;
- causal claims;
- changed-position labels;
- stronger/weaker support labels;
- frontend comparison copy;
- public API routes.

The output flags mean only that reviewed family-level evidence exists in both Congresses and may be displayed with caveats. They do not mean continuity, change, consistency, shift, stronger support, weaker support, or ideological movement.

## Counting Rules

The helper reuses the PR #46 accessor:

`load_house_comparable_family_artifact()`

It only considers artifact families where:

- `eligible_for_future_limited_record_across_congresses` is true; and
- `comparability_status` is `directly_comparable` or `conditionally_comparable`.

It excludes:

- `related_but_not_comparable` families;
- ungrouped artifact rows;
- broad-domain-only matching;
- procedural/limited/non-interpreted evidence from Yes/No counts.

For each artifact roll call, the helper joins the selected legislator's `votes_cast` row and reports:

- `yea` as cast substantive Yes only when the roll call is eligible and interpreted;
- `nay` as cast substantive No only when the roll call is eligible and interpreted;
- `not_voting` separately;
- `present` separately;
- no vote row or non-counting row as missing/no-record.

The 118th and 119th counts remain separate.

## Validation Profiles

Production read-only helper checks:

| Profile | Families returned | Display eligible | Direct | Conditional | Notes |
|---|---:|---:|---:|---:|---|
| Valerie P. Foushee | 11 | 11 | 4 | 7 | Strong common-family evidence; no movement labels generated. |
| Aaron Bean | 11 | 11 | 4 | 7 | Strong common-family evidence; no movement labels generated. |
| Adam Smith | 11 | 11 | 4 | 7 | Strong common-family evidence; no movement labels generated. |
| Abraham J. Hamadeh | 11 | 0 | 0 | 0 | 119th-only pattern; 118th missing/no-record preserved. |
| Allred | 11 | 0 | 0 | 0 | 118th-only pattern; 119th missing/no-record preserved. |
| Aumua Amata Coleman Radewagen | 11 | 1 | 0 | 1 | Not-voting/missing burden preserved separately; one conditional family available. |
| James Gallagher | 11 | 0 | 0 | 0 | Sparse/no both-Congress eligible family display. |

For all validation profiles, the helper generated no continuity/change/movement fields.

## Direct SQL Reconciliation

Representative reconciliation:

- Profile: Valerie P. Foushee
- Family: `eco_government_funding_packages`
- Artifact roll calls: 118th `(2235, 2239, 2286, 2858, 2935)`, 119th `(165, 260, 264, 1497, 1513)`

Direct SQL returned:

- 118th: `yea = 1`, `nay = 4`
- 119th: `nay = 5`

The helper returned the same counts:

- 118th: `cast_substantive_yes_count = 1`, `cast_substantive_no_count = 4`
- 119th: `cast_substantive_yes_count = 0`, `cast_substantive_no_count = 5`

The SQL ran in a read-only transaction.

## Tests

Targeted tests:

```text
python -m pytest tests\test_house_comparable_families_accessor.py tests\test_house_comparable_family_legislator.py
```

Result:

```text
25 passed
```

The new test file covers:

- loading through the PR #46 accessor;
- helper output shape;
- valid House legislator counts;
- 118th-only profile;
- 119th-only profile;
- sparse profile;
- not-voting handled separately;
- not-voting excluded from Yes/No counts;
- present handled separately;
- related/ungrouped rows excluded;
- direct versus conditional distinction;
- 118th/119th count separation;
- no continuity/change/movement fields;
- no public endpoint added;
- read-only transaction behavior when the helper owns the connection.

## Permanent Code Files

- `backend/app/analysis/house_comparable_family_legislator.py`: reusable internal helper for joining the versioned family artifact to House legislator vote records.
- `backend/tests/test_house_comparable_family_legislator.py`: targeted contract coverage for counting semantics and product boundaries.

Both remain useful after this milestone because future internal API/accessor work needs the same family-level count contract.

## Product Boundary

This helper is ready for a future internal API/accessor milestone that exposes factual `Record Across Congresses` availability to trusted backend callers.

It is not a public product feature yet, and it does not authorize:

- `Continuity / Change`;
- changed-position labels;
- ideological movement language;
- causal claims;
- frontend comparison copy.

Recommended next milestone: add an internal API-facing adapter or private endpoint only after reviewing exact response naming and copy guardrails for `Record Across Congresses`.
