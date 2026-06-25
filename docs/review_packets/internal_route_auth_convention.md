# Internal Route Auth Convention

Branch: `codex/internal-route-auth-convention`  
Base: `main` at `c9dd20348015cb0a722f37d6e58422f3737abf49`

## Summary

This milestone defines a minimal private/internal route convention and mounts the first guarded internal endpoint for House `Record Across Congresses`.

Endpoint:

```text
GET /internal/record-across-congresses/house/{legislator_identifier}
```

Implementation paths:

- `backend/app/internal_auth.py`
- `backend/app/api/internal_record_across.py`
- `backend/app/main.py`

The endpoint reuses the PR #50 transport:

```text
build_internal_house_record_across_congresses_response(...)
```

It does not duplicate adapter, helper, or artifact-accessor logic.

## Design Note

What makes a route private/internal in this project?

- It is mounted under `/internal/...`.
- It is guarded by an internal-only request header.
- It is excluded from public OpenAPI with `include_in_schema=False`.
- It is not called by frontend runtime code.
- It is documented as unsupported for public/user-facing use.

How is access guarded?

- The server reads `INTERNAL_API_TOKEN` from environment configuration.
- Requests must send the same value in `X-Internal-API-Token`.
- Comparison uses `hmac.compare_digest`.

How does it fail closed?

- Missing `INTERNAL_API_TOKEN`: `401`.
- Empty/blank `INTERNAL_API_TOKEN`: `401`.
- Missing request header: `401`.
- Wrong request header: `401`.
- The response body is generic: `{"detail": "Unauthorized"}`.

How is it excluded from public OpenAPI?

- The router is created with `include_in_schema=False`.
- The endpoint decorator also sets `include_in_schema=False`.
- Tests validate the route is absent from `app.openapi()["paths"]`.

How are secrets configured?

- Secret name: `INTERNAL_API_TOKEN`.
- Request header: `X-Internal-API-Token`.
- No secret value is committed to the repository.
- Deployment secret configuration is not changed in this milestone.

How are secrets avoided in logs and code?

- The secret is only read from `os.getenv`.
- The provided token is only compared.
- Neither value is logged, returned, or included in docs/tests as a real secret.

How do tests prove unauthorized access fails?

- Tests cover missing environment token, empty environment token, missing request token, and incorrect request token.

How does deployment verification prove no public exposure?

- Production OpenAPI must not include `/internal/...`.
- Normal unauthenticated public access to the internal path must return `401`.
- Existing public health and coverage endpoints must continue to work.

Can this convention be reused?

- Yes. Future internal-only routes can use `Depends(require_internal_api_token)`, mount under `/internal/...`, and set `include_in_schema=False`.

## Endpoint Behavior

The route accepts a House legislator identifier and returns the PR #50 transport response shape:

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

The response preserves:

- product framing `Record Across Congresses`;
- explicit non-authorization metadata;
- family rows with caveats;
- direct and conditional family counts;
- separated cast substantive Yes/No, not-voting, present, and missing/no-record counts;
- roll-call IDs considered by Congress.

Unknown or unavailable legislator identifiers return `404` with generic `Record unavailable`.

## Product Boundary

The route must not generate or expose:

- continuity/change labels;
- behavioral or ideological movement claims;
- causal or motive claims;
- changed-position labels;
- stronger/weaker support labels;
- consistency labels;
- trend labels;
- frontend comparison copy.

It returns factual availability and counts only.

## Validation Profiles

Production-shaped route validation used `TestClient`, a temporary local token, and the configured read-only data path.

| Profile | Unauthorized | Authorized | Display eligible | Direct | Conditional | Example |
|---|---:|---:|---:|---:|---:|---|
| Valerie P. Foushee | 401 | 200 | 11 | 4 | 7 | `eco_government_funding_packages`; caveat preserved. |
| Aaron Bean | 401 | 200 | 11 | 4 | 7 | `eco_government_funding_packages`; caveat preserved. |
| Adam Smith | 401 | 200 | 11 | 4 | 7 | `eco_government_funding_packages`; caveat preserved. |
| Abraham J. Hamadeh | 401 | 200 | 0 | 0 | 0 | 118th missing/no-record preserved. |
| Allred | 401 | 200 | 0 | 0 | 0 | 119th missing/no-record preserved. |
| Aumua Amata Coleman Radewagen | 401 | 200 | 1 | 0 | 1 | `nsf_ukraine_assistance_restrictions`; 118th not-voting=3 preserved separately. |
| James Gallagher | 401 | 200 | 0 | 0 | 0 | Missing/no-record preserved in both Congresses. |

## Tests

Targeted tests:

```text
python -m pytest tests\test_app_config.py tests\test_internal_record_across_route.py tests\test_house_comparable_families_accessor.py tests\test_house_comparable_family_legislator.py tests\test_house_record_across_congresses.py tests\test_house_record_across_congresses_transport.py
```

Result:

```text
52 passed
```

Full backend suite was run because routing changed:

```text
python -m pytest
```

Result: not green in this local environment. The failures were not in the new internal route tests. Observed issues:

- fixture API tests read production-shaped database data instead of fixture-only expectations;
- tests using `tmp_path` hit Windows permission errors under the default pytest temp root;
- rerun with `--basetemp .pytest_tmp_internal_route_full` still ended with a Windows permission error during pytest temp cleanup.

The `.pytest_tmp_internal_route_full` directory was removed during resume and is not part of the milestone diff.

The targeted route/transport tests remained green.

## OpenAPI And Public Exposure

Validated locally:

- internal route is absent from `app.openapi()["paths"]`;
- no public non-`/internal` route contains `record`, `congress`, `comparable`, or `family`;
- unauthenticated access fails closed.

Production deployment verification must repeat:

- `/health`;
- `/coverage/metadata`;
- `/openapi.json` absence;
- unauthenticated internal path returns `401`.

Authorized production route testing is only possible if `INTERNAL_API_TOKEN` is configured in the deployment environment. This milestone does not change deployment secrets.

## Downstream Use

Allowed:

- trusted backend use with `INTERNAL_API_TOKEN`;
- future frontend prototype after a separate rendered validation milestone;
- future internal routes using the same guard pattern.

Disallowed:

- public user-facing route consumption;
- frontend runtime consumption before prototype validation;
- exposing the internal token;
- unsupported continuity/change/movement/trend/consistency claims.

## Frontend Scope

No frontend runtime code changed. The endpoint is transport-only and does not add UI or product copy.

## Permanent Files

- `backend/app/internal_auth.py`: reusable minimal internal token guard.
- `backend/app/api/internal_record_across.py`: guarded internal endpoint wrapping PR #50 transport.
- `backend/tests/test_internal_record_across_route.py`: guard, OpenAPI, response, and profile tests.

These remain useful because future internal-only routes can reuse the guard and the endpoint can support a later frontend prototype milestone after deployment secret setup and rendered validation.

## Next Recommendation

Configure `INTERNAL_API_TOKEN` in the backend deployment environment, then run an authorized production probe. After that, a separate frontend prototype milestone can consume the internal endpoint with the PR #49 copy guardrails and rendered review.
