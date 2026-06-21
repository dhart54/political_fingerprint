# House Record Across Congresses Adapter

Branch: `codex/house-record-across-congresses-adapter`  
Base: `main` at `9d9a327b54ba43b1e197b42f8065914ebf5694d8`

## Summary

This milestone adds an internal response builder for the existing House comparable-family legislator helper:

`backend/app/analysis/house_record_across_congresses.py`

It wraps:

`backend/app/analysis/house_comparable_family_legislator.py`

The adapter produces a stable backend response contract for factual family-level evidence availability under the product framing:

`Record Across Congresses`

No public route, frontend component, schema, migration, or production write path is added.

## Response Contract

Top-level fields:

- `response_kind`
- `product_framing`
- `availability_explanation`
- `legislator_identifier`
- `requested_legislator_identifier`
- `artifact_version`
- `supported_congresses`
- `legislator`
- `summary`
- `non_authorization_metadata`
- `families`

`summary` includes:

- `eligible_comparable_family_count`
- `record_across_congresses_available`
- `display_eligible_family_count`
- `directly_comparable_display_eligible_family_count`
- `conditionally_comparable_display_eligible_family_count`

Each family row includes:

- `family_id`
- `family_name`
- `issue_domain`
- `comparability_status`
- `governing_question`
- `comparability_caveat`
- `record_across_congresses_available`
- `evidence_available_in_both_congresses`
- `unavailable_reason`
- `roll_call_ids_considered_by_congress`
- `family_evidence_counts_by_congress`

Per-Congress counts include:

- `congress`
- `roll_call_ids_considered`
- `cast_substantive_yes_count`
- `cast_substantive_no_count`
- `not_voting_count`
- `present_count`
- `missing_no_record_count`
- `total_artifact_roll_calls`
- `total_cast_substantive_yes_no_rows`

## Field Naming Guardrails

The adapter intentionally uses availability/count language. It asserts that response field names do not contain disallowed terms such as `changed`, `change`, `trend`, `movement`, `shift`, `increased`, `decreased`, `more_supportive`, `less_supportive`, `consistent`, `continuity`, `flip`, or `alignment_change`.

Validation also checked serialized production-shaped responses for those terms. No disallowed terms were present.

## Allowed And Disallowed Meanings

Allowed meanings:

- reviewed family-level evidence availability;
- separated counts for cast substantive Yes/No, not-voting, present, and missing/no-record;
- direct or conditional comparability status from artifact v1;
- caveated display availability for internal review.

Disallowed meanings:

- unsupported cross-Congress inference;
- behavioral or ideological inference;
- causal inference;
- stronger or weaker support inference;
- consistency inference;
- vote recommendation;
- frontend comparison copy.

The adapter's metadata uses neutral internal-safety fields:

- `internal_response_only`
- `public_route_exposed`
- `only_factual_evidence_availability_and_counts`
- `unsupported_inferences_are_not_generated`
- `frontend_copy_not_authorized`
- `voting_recommendation_not_authorized`
- `requires_review_before_public_product_use`

## Internal-Only Boundary

No FastAPI route was added. That is deliberate: the repository does not currently have a clear private-route convention that would guarantee non-public exposure. A plain internal response builder avoids OpenAPI exposure by construction.

The adapter remains useful as a stable contract for future trusted backend callers. Any future route milestone should first define a private routing convention, authentication/exposure boundary, response naming review, and frontend copy guardrails.

## Why No Frontend Work Is Included

This milestone defines a backend contract only. Frontend work would require copy review and rendered validation to ensure users do not read availability/counts as unsupported cross-Congress inference. That review is intentionally reserved for a later milestone.

## Validation Profiles

Production-shaped read-only adapter checks:

| Profile | Response available | Display eligible | Direct | Conditional | Example family | Example notes |
|---|---:|---:|---:|---:|---|---|
| Valerie P. Foushee | true | 11 | 4 | 7 | `eco_government_funding_packages` | 118th yes=1/no=4; 119th yes=0/no=5; caveat preserved. |
| Aaron Bean | true | 11 | 4 | 7 | `eco_government_funding_packages` | 118th yes=4/no=1; 119th yes=5/no=0; caveat preserved. |
| Adam Smith | true | 11 | 4 | 7 | `eco_government_funding_packages` | 118th yes=1/no=4; 119th yes=2/no=3; caveat preserved. |
| Abraham J. Hamadeh | false | 0 | 0 | 0 | `eco_government_funding_packages` | 118th missing/no-record=5; 119th yes=5; no display availability. |
| Allred | false | 0 | 0 | 0 | `eco_government_funding_packages` | 118th yes=1/no=4; 119th missing/no-record=5; no display availability. |
| Aumua Amata Coleman Radewagen | true | 1 | 0 | 1 | `nsf_ukraine_assistance_restrictions` | Conditional caveat preserved; 118th no=9, not-voting=3; 119th no=1. |
| James Gallagher | false | 0 | 0 | 0 | `eco_government_funding_packages` | 118th missing/no-record=5; 119th missing/no-record=5; no display availability. |

For every profile, disallowed term checks returned an empty list.

## Tests

Targeted tests:

```text
python -m pytest tests\test_house_comparable_families_accessor.py tests\test_house_comparable_family_legislator.py tests\test_house_record_across_congresses.py
```

Result:

```text
35 passed
```

The new test file covers:

- response shape;
- response-level product framing;
- explicit non-authorization metadata;
- allowed field names;
- absence of disallowed field names;
- no generated unsupported wording;
- direct and conditional count summaries;
- display eligibility count;
- ineligible profile response;
- caveat preservation;
- separated Yes/No/not-voting/present/missing counts;
- related and ungrouped rows excluded from eligible output;
- required validation profile identifiers;
- no public route or OpenAPI exposure.

## Permanent Code Files

- `backend/app/analysis/house_record_across_congresses.py`: internal response builder for trusted backend consumption.
- `backend/tests/test_house_record_across_congresses.py`: contract tests protecting field naming, availability/count semantics, and no-route exposure.

Both files remain useful after this milestone because future private API or frontend-review milestones can consume the same response shape without re-deciding counting semantics.

## Future Consumption Guidance

Future API/frontend work should:

- consume this adapter rather than rebuilding counts;
- preserve field names centered on availability and counts;
- preserve caveats near family rows;
- keep not-voting, present, and missing/no-record separate from cast substantive Yes/No counts;
- keep related and ungrouped rows outside eligible output;
- avoid copy that implies unsupported cross-Congress inference;
- add private-route exposure only after the repository has an explicit trusted internal-route convention.
