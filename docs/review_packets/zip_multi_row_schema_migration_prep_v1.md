# ZIP Multi-Row Schema Migration Prep V1

## Summary

This milestone prepares the ZIP multi-row schema path without applying it or changing public lookup behavior.

- Migration file added: `backend/migrations/0013_zip_district_mappings.sql`
- Migration applied to local or production DB: no
- Public lookup route switched to new table: no
- National ZIP data ingested: no
- Address lookup added: no
- Frontend behavior changed: no

## Migration File Status

The migration draft adds `zip_district_mappings` as an additive table with a surrogate `id` primary key. It does not drop, alter, or deprecate `zip_district_map` in SQL.

Key contract points:

- `zip` is not a primary key.
- ZIP format check is present.
- Source metadata columns are present.
- `source_currentness` and `confidence` have controlled checks.
- Indexes exist for `zip`, `(zip, state, district)`, `source_currentness`, `source_name`, and `source_version`.
- A unique active source-period rule detects duplicate active rows for the same ZIP/state/district/source/version/period while allowing legitimate split ZIP rows.

## Schema Contract Implemented

Required fields drafted:

- `id`
- `zip`
- `state`
- `district`
- `source_name`
- `source_type`
- `source_retrieved_at`
- `source_effective_date`
- `source_version`
- `source_currentness`
- `confidence`
- `is_primary`
- `district_type`
- `congress`
- `cycle`
- `valid_from`
- `valid_to`
- `provider_record_id`
- `notes`
- `created_at`
- `updated_at`

## Synthetic Fixtures Added

Added `backend/fixtures/zip_multi_row_schema_sample/zip_district_mappings.json`.

Fixture coverage:

- single current/source-backed district
- same-state multi-district ZIP
- multi-state ZIP
- fixture/sample row
- stale/unknown row with intentionally missing source metadata
- current/source-backed row
- intentional duplicate active row for detection

All fixture rows use clearly synthetic source metadata and are not production coverage.

## Payload Parity Tests

`backend/tests/test_zip_lookup_payload_parity.py` builds PR #77-shaped payloads from the synthetic multi-row fixture and verifies:

- current single-district source-backed rows classify as `single_district_ready`
- same-state multi-district rows classify as `ambiguous_zip`
- multi-state rows classify as `multi_state_zip`
- missing source metadata classifies as `stale_or_unknown_source`
- fixture/sample rows classify as `fixture_sample_only`
- unsupported payloads classify as `unsupported_zip`
- old `zip_district_map` DB payloads remain `stale_or_unknown_source`

These tests are route-adjacent only; the production route still reads the old table.

## Read-Only Report Checks

`backend/scripts/generate_zip_source_metadata_report.py` now reports:

- migration exists
- new schema can represent multiple districts per ZIP
- source metadata columns exist
- controlled `source_currentness` and `confidence` checks exist
- required indexes exist
- old table remains compatibility-only
- current lookup route still uses old gated path
- new-table route switch is absent
- synthetic fixture coverage and duplicate detection

The regenerated source metadata report remains repository/local-only, not production coverage truth.

## Production Lookup Unchanged

Confirmed by report/test inspection:

- `backend/app/api/lookup.py` still calls `get_zip_lookup_response`.
- `backend/app/api/precomputed.py` still queries `FROM zip_district_map`.
- No `FROM zip_district_mappings` read path exists.
- DB ZIP payloads remain `source_currentness: "stale_or_unknown"` and `stale_or_unknown_source: true`.
- Frontend auto-select remains limited to `single_district_ready`.

## Old DB Path Gated

The old database path remains unsafe/stale-unknown by design because source/date/version/currentness metadata does not exist on `zip_district_map`.

## Known Limitations

- The migration is drafted only; it has not been applied to any database.
- The new table is not populated.
- ETL paths still dedupe old ZIP fixture bundles by `zip`.
- The public lookup route still cannot read multi-row ZIP mappings from the database.
- This does not certify production coverage truth.

## No-Go Items Honored

- No production or local DB mutation.
- No public lookup route switch.
- No national ZIP ingestion.
- No address lookup.
- No provider integration.
- No frontend behavior change.
- No vote interpretation, Record Across, issue-card, receipt/detail, or profile behavior change.

## Validation

- `python -m pytest backend\tests\test_zip_source_metadata_report.py -p no:cacheprovider`: passed, 4/4.
- `python -m pytest backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py -p no:cacheprovider`: passed, 11/11.
- `python backend\scripts\generate_zip_source_metadata_report.py`: passed; wrote Markdown and JSON review packets.
- `python -m json.tool docs\review_packets\zip_source_metadata_ambiguity_payload_v1.json`: passed.
- `python -m json.tool docs\review_packets\zip_multi_row_schema_migration_prep_v1.json`: passed.
- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 9/9.
- `node --test lib\*.test.mjs` from `frontend`: passed, 84/84 with existing module-type warnings.
- `npm run lint` from `frontend`: passed with 8 existing React hook dependency warnings.
- `npm run build` from `frontend`: passed with the same 8 hook dependency warnings.

## Recommended Next Milestone

**ZIP Multi-Row Schema Migration Application And Read-Only Coverage V1**

- explicitly approve and apply the additive `zip_district_mappings` migration;
- verify the empty/new-table contract with read-only coverage checks;
- keep the old lookup path gated until source-backed rows and parity checks are approved;
- do not ingest national ZIP data;
- do not add address lookup.
