# ZIP Multi-Row Source-Backed Ingestion Preflight V1

## Summary

This milestone prepares the source-backed ZIP ingestion path without ingesting rows or changing production lookup behavior.

- Added a backend-owned unsupported ZIP payload helper for future route adoption.
- Kept `/lookup/zip/{zip}` and `/lookup/zip/{zip}/races` on the existing `zip_district_map` compatibility path.
- Confirmed `zip_district_mappings` remains empty with read-only postcheck.
- Defined the future source approval contract, ingestion caps, rollback expectations, and route-switch acceptance criteria.
- Kept `ZIP_MULTI_ROW_LOOKUP_ENABLED=false` as design-only; no flag was enabled or wired.

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

- `/lookup/zip/{zip}` still resolves through `get_zip_lookup_response`.
- `/lookup/zip/{zip}/races` still resolves through `get_zip_race_response`.
- Both DB-backed ZIP paths still use the old `zip_district_map` compatibility table.
- No public API route reads or joins `zip_district_mappings`.
- Supported ZIP responses are unchanged.
- Old-table DB ZIP payloads remain `stale_or_unknown_source`.

## Backend-Owned Unsupported Payload Contract

This milestone adds `app.api.precomputed.build_unsupported_zip_lookup_response` as a backend-owned contract helper, but does not wire it into the public route yet.

Reason: current public behavior returns a 404 for unsupported ZIPs. Returning the standardized payload from `/lookup/zip/{zip}` would be a behavior change and should be done in a later route-contract milestone.

Contract shape:

```json
{
  "zip": "99999",
  "state": null,
  "district": null,
  "status": "unsupported_zip",
  "lookup_state": "unsupported_zip",
  "data_source": "none",
  "lookup_metadata": {
    "source_type": "none",
    "source_name": null,
    "source_retrieved_at": null,
    "source_effective_date": null,
    "source_version": null,
    "source_currentness": "unsupported",
    "fixture_sample_only": false,
    "stale_or_unknown_source": false,
    "member_metadata_uncertain": false,
    "can_represent_multiple_districts": false,
    "ambiguity_detection_level": "none",
    "confidence": "unknown"
  },
  "district_mappings": [],
  "house_rep": null,
  "senators": []
}
```

Unsupported means not loaded or not resolvable by current coverage. It does not claim the ZIP is invalid.

## Source Approval Contract

No concrete external provider is selected in this milestone. A future ingestion milestone must approve a source record with:

- source name
- source type
- source URL or retrieval location
- retrieval date
- effective date
- source version
- confidence mapping
- currentness mapping
- ability to represent multi-district ZIPs
- ability to represent multi-state ZIPs
- treatment of PO boxes, unique ZIPs, and military ZIPs if applicable
- known limitations

Minimum source acceptance:

- The source can represent multi-district and multi-state ZIPs.
- Currentness and confidence mappings are reviewed before ingestion.
- Limitations are documented before any write.
- Source metadata can populate every required `zip_district_mappings` source field.

## Future Ingestion Caps

A future write milestone must define exact caps before writing:

- dry-run required first
- row-count cap
- unique-ZIP cap
- state cap or pilot-state cap
- duplicate detection
- ambiguity detection
- rollback created before write
- production write confirmation phrase: `APPLY ZIP SOURCE-BACKED INGESTION TO APPROVED SUPABASE TARGET`

No ingestion cap is exercised here because this milestone performs no writes.

## Future Route-Switch Acceptance Criteria

- `ZIP_MULTI_ROW_LOOKUP_ENABLED=false` by default.
- Source-backed rows loaded and reviewed in a separate bounded write milestone.
- Backend emits `confidence`.
- Backend emits `source_currentness`.
- Backend emits all required source metadata.
- Ambiguous and multi-state ZIPs are represented explicitly.
- Unsupported ZIP payload is standardized by backend before broad rollout.
- Current House member metadata gate exists.
- Duplicate current House member matches block auto-select.
- Stale member metadata blocks auto-select.
- Frontend classifier requires strict currentness/confidence before auto-select.

## Strict Future Auto-Select Gate

Future `single_district_ready` must require:

- `source_currentness === "current"`
- `confidence` is `source_backed` or `reviewed`
- `source_name`, `source_type`, `source_retrieved_at`, `source_effective_date`, and `source_version` are present
- `fixture_sample_only === false`
- `stale_or_unknown_source === false`
- exactly one state
- exactly one district
- ambiguity detection level is `multi_row_source`
- current House member metadata gate passes
- duplicate current House member matches block auto-select

## Safety Confirmations

- No migration rerun.
- No seed load.
- No national ZIP ingestion.
- No production ZIP row insert, update, or delete.
- No route switch.
- No address lookup.
- No provider integration.
- No frontend runtime behavior change.
- No production data mutation.
- Old `zip_district_map` compatibility path remains in place.

## Validation

- `python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env`: passed; read-only, migration not applied, row count `0`.
- Initial focused backend ZIP test run without a `DATABASE_URL` override picked up live DB rows and failed fixture-specific `test_api_lookup.py` expectations.
- `$env:DATABASE_URL='postgresql://invalid'; python -m pytest backend\tests\test_api_lookup.py backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py backend\tests\test_zip_multi_row_readonly_route_eval.py -p no:cacheprovider`: passed, 29/29.
- `node --test lib\zipLookupState.test.mjs`: passed, 9/9.
- `python -m json.tool docs\review_packets\zip_source_backed_ingestion_preflight_v1.json`: passed.
- `python -m json.tool docs\review_packets\zip_multi_row_readonly_route_eval_v1.json`: passed.

## Recommended Next Milestone

ZIP Source Approval And Dry-Run Import Harness V1: explicitly approve a concrete ZIP source, add a no-write parser/dry-run report with exact caps, and keep `ZIP_MULTI_ROW_LOOKUP_ENABLED=false`.
