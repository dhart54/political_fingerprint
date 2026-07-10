# ZIP Multi-Row Read-Only Coverage And Route-Path Evaluation V1

## Summary

- `zip_district_mappings` remains inert after PR #81.
- Public ZIP lookup behavior remains unchanged.
- `/lookup/zip/{zip}` still delegates to `get_zip_lookup_response`.
- `/lookup/zip/{zip}/races` still delegates to `get_zip_race_response`.
- Both DB-backed ZIP paths still use `_get_db_zip_record`, which reads `zip_district_map`.
- No public API query reads `zip_district_mappings`.

## Read-Only Postcheck

Command used:

```text
python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env
```

Results:

| Check | Value |
| --- | --- |
| Migration applied by postcheck | no |
| Contract checks passed | yes |
| `zip_district_map` exists | yes |
| `zip_district_mappings` exists | yes |
| `zip_district_mappings` row count | `0` |
| Unique ZIP count | `0` |
| Auto-select eligible count | `0` |
| Raw DB URL/password recorded | no |

## Current Route Behavior

`/lookup/zip/{zip}`:

- Route file: `backend/app/api/lookup.py`
- Delegates to: `get_zip_lookup_response`
- DB helper path: `_get_db_zip_lookup_response` -> `_get_db_zip_record`
- Current table: `zip_district_map`
- New table read: no
- Current DB source posture: `stale_or_unknown`, `single_row`, cannot represent multiple districts

`/lookup/zip/{zip}/races`:

- Route file: `backend/app/api/lookup.py`
- Delegates to: `get_zip_race_response`
- DB helper path: `_get_db_zip_race_response` -> `_get_db_zip_record`
- Current table: `zip_district_map`
- New table read: no
- Future implication: race lookup must switch in lockstep with the canonical multi-row ZIP resolver or stay explicitly compatibility-only, because it also needs one safe state/district before querying races.

## Future Route Switch Design

Design-only flag:

```text
ZIP_MULTI_ROW_LOOKUP_ENABLED=false
```

Default behavior remains the current compatibility path. When false, both `/lookup/zip/{zip}` and `/lookup/zip/{zip}/races` continue to use `zip_district_map`.

The future enabled path should only read `zip_district_mappings` after a later milestone approves source-backed data, validates production coverage, defines rollback, and keeps the old path available until parity and monitoring pass.

## Future Single-District Ready Gate

A future `single_district_ready` result must require all of the following:

- `source_currentness === "current"`
- `confidence` is `source_backed` or `reviewed`
- `source_name` present
- `source_type` present
- `source_retrieved_at` present
- `source_effective_date` present
- `source_version` present
- `fixture_sample_only === false`
- `stale_or_unknown_source === false`
- exactly one state
- exactly one district
- source can represent multi-district ZIPs
- source can represent multi-state ZIPs
- ambiguity detection level is source-backed, preferably `multi_row_source`
- current House member metadata gate passes
- no duplicate current House member match
- frontend classifier returns `single_district_ready`

Design gap: the current frontend classifier is safe for current stale/fixture production payloads, but it should not be the only gate for a future source-backed route switch because its source-known heuristic does not require confidence.

## Current-Member Metadata Gaps

- Term/currentness checks must be explicit before a ZIP can auto-select a House member.
- Vacancies must produce a non-ready or manual-search state.
- Duplicate current House matches for one state/district must block auto-select.
- Stale legislator metadata must block auto-select even when ZIP source metadata is current.
- Senate results remain state-level and should keep the Senate state-level caveat.

## UI Behavior Gaps

- Stale or fixture/sample ZIP results may still show labeled loaded official cards even when auto-select is blocked.
- A later UI milestone should decide whether stale/sample results hide official cards entirely or require manual search only.

## Unsupported ZIP Payload Gap

- The frontend currently normalizes a 404 into an unsupported shape.
- The backend should own a standardized unsupported ZIP payload contract before broad rollout.

## Safety Confirmations

- No migration was rerun.
- No seed data was loaded.
- No national ZIP data was ingested.
- No route switch was made.
- No address lookup was added.
- No provider integration was added.
- No frontend runtime behavior changed.
- No production data was mutated.

## Recommended Next Milestone

ZIP Multi-Row Source-Backed Ingestion Preflight V1: select and approve a source, define bounded seed/ingestion caps and rollback, implement backend-owned unsupported payload contract, and keep `ZIP_MULTI_ROW_LOOKUP_ENABLED=false`.
