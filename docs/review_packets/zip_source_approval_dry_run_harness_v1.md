# ZIP Source Approval And Dry-Run Import Harness V1

## Summary

- Added a no-write dry-run parser/report harness for local ZIP/ZCTA source-like files.
- Source decision: `approved_for_local_dry_run_only`.
- Production ingestion is not approved by this packet.
- Public lookup behavior remains unchanged and `ZIP_MULTI_ROW_LOOKUP_ENABLED` remains false.

## Source Approval Decision

- Candidate: U.S. Census Bureau 119th Congressional District to 2020 ZCTA Relationship File
- Type: `official_government_relationship_file`
- URL/retrieval path: https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html
- Retrieval date: `2026-07-10`
- Effective date: `119th Congress / 2020 ZCTA vintage; exact production effective date not approved`
- Source version: `119th-congressional-district-to-2020-zcta-relationship-file`
- Production ingestion approved: `False`

Rationale:
- The Census relationship file candidate is official and can represent many-to-many geography relationships.
- The candidate is appropriate for parser and ambiguity-report dry runs using local sample data.
- Production ingestion is not approved until exact license/terms, effective date, file version, and technical layout are recorded without inference.

Limitations:
- ZIP Codes are delivery routes, not exact boundaries.
- ZCTAs are Census-created approximations and do not represent every valid USPS ZIP Code.
- ZIP-only lookup can at most surface possible district mappings, not a definitive address-level representative.
- Auto-select must remain blocked for ambiguous, multi-state, stale, fixture, or metadata-incomplete rows.

Production approval blockers:
- `exact_license_or_terms_not_recorded`
- `exact_effective_date_not_recorded`
- `exact_download_file_and_checksum_not_recorded`
- `technical_record_layout_not_bound_to_parser`

## Dry-Run Report Summary

- Input: `backend/fixtures/zip_source_dry_run_sample/census_119_cd_zcta_sample.csv`
- Row count: `11`
- Accepted row count: `7`
- Rejected row count: `4`
- Unique ZIP/ZCTA count: `4`
- State count: `2`
- Unique state-district pair count: `4`
- Same-state multi-district count: `1`
- Multi-state count: `1`
- Duplicate active row count: `1`
- Missing required metadata count: `1`
- Invalid ZIP/ZCTA format count: `1`
- Invalid state count: `1`
- Invalid district count: `1`
- Future auto-select eligible ZIP count: `0`
- Any row auto-select eligible under strict gates: `False`
- Explicit no DB write: `True`

Confidence distribution:
- `source_backed`: `11`

Currentness distribution:
- `current`: `11`

## Rejected Rows
- line `9` `9999X` `NC` `04`: invalid_zip_zcta_format
- line `10` `09993` `NORTH` `04`: invalid_state
- line `11` `09994` `NC` ``: invalid_district
- line `12` `09995` `NC` `06`: missing_required_metadata

## Safety Confirmations
- script_has_no_database_dependency: `True`
- script_fail_closed_without_dry_run_flag: `True`
- report_only_output: `True`
- no_insert_update_delete_truncate_drop_or_copy_executed: `True`
- zip_district_mappings_expected_to_remain_empty: `True`
- public_lookup_behavior_expected_unchanged: `True`

## Validation
- `python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env`: passed; Read-only; migration_applied false; row count 0; unique ZIP count 0; auto-select eligible count 0.
- `python backend\scripts\dry_run_zip_source_import.py --dry-run --input backend\fixtures\zip_source_dry_run_sample\census_119_cd_zcta_sample.csv --output docs\review_packets\zip_source_approval_dry_run_harness_v1.json --markdown-output docs\review_packets\zip_source_approval_dry_run_harness_v1.md`: passed; Generated no-write dry-run JSON and Markdown packets.
- `$env:DATABASE_URL='postgresql://invalid'; python -m pytest backend\tests\test_api_lookup.py backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py backend\tests\test_zip_multi_row_readonly_route_eval.py backend\tests\test_zip_source_dry_run_import.py -p no:cacheprovider`: passed; 33 passed.
- `python -m json.tool docs\review_packets\zip_source_approval_dry_run_harness_v1.json`: passed; Valid JSON.
- `python -m json.tool docs\review_packets\zip_source_backed_ingestion_preflight_v1.json`: passed; Valid JSON.

## Recommended Next Milestone

ZIP Source Retrieval Approval And Bounded Dry-Run With Official File V1: pin the exact Census file, terms/license, version, and effective date; run the harness against a reviewed local official file; keep the database empty and the public route unchanged.
