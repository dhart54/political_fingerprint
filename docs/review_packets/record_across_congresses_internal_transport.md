# Record Across Congresses Internal Transport

Branch: `codex/record-across-congresses-internal-transport`  
Base: `main` at `6692cbd290ca11473f9d70fc5c437fbd1cd48886`

## Summary

This milestone adds a no-route internal backend transport callable for the House `Record Across Congresses` adapter:

`backend/app/analysis/house_record_across_congresses_transport.py`

It wraps the PR #48 adapter:

`backend/app/analysis/house_record_across_congresses.py`

The transport returns the existing adapter response shape for trusted backend callers without adding a FastAPI route, public API endpoint, frontend code, schema change, migration, production write, or public OpenAPI exposure.

## Transport Choice

Chosen transport: `no_route_internal_backend_callable`.

A guarded route was not implemented because the repository currently has no established private-route namespace, header guard, token guard, or auth dependency pattern. Inventing a new route guard inside this milestone would create broader auth and configuration questions outside the approved scope.

The safe transport is a direct Python callable:

```text
build_internal_house_record_across_congresses_response(legislator_identifier)
```

It imports and calls the adapter rather than duplicating adapter, helper, or artifact logic.

## Why It Is Private/Internal

The transport is private by absence from HTTP routing:

- no FastAPI router was added;
- `app.include_router(...)` was not changed;
- no endpoint path was introduced;
- no public OpenAPI path is generated;
- trusted backend code must import the callable directly.

This is intentionally narrower than a route guard. It fails closed for public requests because there is no URL to call.

## Guard Behavior

Route guard behavior is not applicable because no route exists.

Effective guard:

- no HTTP mount;
- no OpenAPI exposure;
- no frontend caller;
- no public URL;
- response validation requires `product_framing == "Record Across Congresses"`;
- response field validation rejects disallowed adapter field terms.

Future route work must define a real private-route convention, including authentication/exposure semantics, before adding HTTP transport.

## Response Contract

The transport returns the PR #48 adapter response shape unchanged. Top-level fields include:

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

Family rows preserve:

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

Per-Congress counts preserve:

- `cast_substantive_yes_count`
- `cast_substantive_no_count`
- `not_voting_count`
- `present_count`
- `missing_no_record_count`
- `roll_call_ids_considered`
- `total_artifact_roll_calls`
- `total_cast_substantive_yes_no_rows`

## Response Naming And Copy Safety

Source guardrail:

`docs/review_packets/record_across_congresses_frontend_copy_guardrails.json`

Tests validate that:

- approved copy still uses `Record Across Congresses`;
- approved copy contains none of the disallowed terms;
- transport responses contain none of the disallowed guardrail terms;
- transport field validation rejects disallowed adapter field terms.

The transport does not generate frontend copy. It only returns factual availability and counts.

## OpenAPI And Public-Route Validation

Targeted tests validate:

- no `record-across` route;
- no `record_across` route;
- no public `record`, `congress`, `comparable`, or `family` transport path;
- no OpenAPI path for the internal transport.

Post-merge deployment validation should repeat the production OpenAPI check.

## Validation Profiles

Production-shaped read-only transport checks:

| Profile | Response available | Display eligible | Direct | Conditional | Example family | Notes |
|---|---:|---:|---:|---:|---|---|
| Valerie P. Foushee | true | 11 | 4 | 7 | `eco_government_funding_packages` | 118th yes=1/no=4; 119th yes=0/no=5; caveat preserved. |
| Aaron Bean | true | 11 | 4 | 7 | `eco_government_funding_packages` | 118th yes=4/no=1; 119th yes=5/no=0; caveat preserved. |
| Adam Smith | true | 11 | 4 | 7 | `eco_government_funding_packages` | 118th yes=1/no=4; 119th yes=2/no=3; caveat preserved. |
| Abraham J. Hamadeh | false | 0 | 0 | 0 | `eco_government_funding_packages` | 118th missing/no-record=5; 119th yes=5. |
| Allred | false | 0 | 0 | 0 | `eco_government_funding_packages` | 118th yes=1/no=4; 119th missing/no-record=5. |
| Aumua Amata Coleman Radewagen | true | 1 | 0 | 1 | `nsf_ukraine_assistance_restrictions` | 118th no=9 and not-voting=3; 119th no=1; conditional caveat preserved. |
| James Gallagher | false | 0 | 0 | 0 | `eco_government_funding_packages` | 118th missing/no-record=5; 119th missing/no-record=5. |

For all profiles, product framing remained `Record Across Congresses`, caveats were preserved, and not-voting/missing counts stayed separate from Yes/No counts.

## Tests

Targeted tests:

```text
python -m pytest tests\test_house_comparable_families_accessor.py tests\test_house_comparable_family_legislator.py tests\test_house_record_across_congresses.py tests\test_house_record_across_congresses_transport.py
```

Result:

```text
41 passed
```

Additional validation:

```text
python -m py_compile app\analysis\house_record_across_congresses_transport.py
```

Result: passed.

Full backend tests were not required because no shared route registration or app startup behavior changed.

## Allowed Downstream Uses

Allowed:

- trusted backend imports;
- internal endpoint design review;
- future private-route implementation after auth/exposure design;
- frontend prototype planning using PR #49 approved copy.

Disallowed:

- public route exposure;
- frontend runtime consumption before a rendered prototype milestone;
- continuity/change/movement/trend/consistency labels;
- stronger/weaker support labels;
- motive or causal claims;
- vote recommendations.

## Why Frontend Remains Out Of Scope

No frontend code consumes this transport. PR #49 specifies that runtime UI should come after private transport and rendered validation. This milestone only proves the backend callable and route-exposure boundary.

## Permanent Code Files

- `backend/app/analysis/house_record_across_congresses_transport.py`: no-route internal backend transport callable wrapping the PR #48 adapter.
- `backend/tests/test_house_record_across_congresses_transport.py`: contract tests for adapter equality, route/OpenAPI absence, copy guardrails, profiles, caveats, and separated counts.

Both remain useful after this milestone because a future private endpoint can call the transport without rebuilding adapter logic or re-deciding response semantics.

## Next Recommendation

Recommended next milestone: design the private-route authentication/exposure convention, or explicitly approve an environment-backed internal header guard. Only after that should an HTTP route be added.

If route auth is approved later, keep it excluded from public OpenAPI and reuse this transport as the only response source.
