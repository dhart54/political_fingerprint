# ZIP Source Retrieval Official-File Dry-Run V1

## Summary

- Parsed the exact pinned official Census national 119th Congressional District-to-2020 ZCTA relationship file.
- Source decision: `approved_for_bounded_dry_run_only`.
- Production ingestion is not approved by this packet.
- Public lookup behavior remains unchanged and `ZIP_MULTI_ROW_LOOKUP_ENABLED` remains false.

## Source Approval Decision

- Candidate: U.S. Census Bureau 119th Congressional District to 2020 ZCTA Relationship File
- Type: `official_government_relationship_file`
- Source page: https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html
- URL/retrieval path: https://www2.census.gov/geo/docs/maps-data/data/rel2020/cd-sld/tab20_cd11920_zcta520_natl.txt
- File name: `tab20_cd11920_zcta520_natl.txt`
- Retrieval date: `2026-07-10`
- Effective date: `119th Congress / 2020 ZCTA vintage; exact production effective date not approved`
- Source version: `119th-congressional-district-to-2020-zcta-relationship-file`
- License/terms basis: Official U.S. Census Bureau public data published as open government data; Census Bureau works created by employees generally are not subject to U.S. copyright. No credential or terms-acceptance gate was present.
- Record layout: https://www.census.gov/programs-surveys/geography/technical-documentation/records-layout/2020-CD-SLD-record-layout.html
- Production ingestion approved: `False`

Rationale:
- The Census relationship file candidate is official and can represent many-to-many geography relationships.
- The candidate is appropriate for parser and ambiguity-report dry runs using local sample data.
- Production ingestion remains outside this no-write milestone even though the exact file and layout are now pinned.

Limitations:
- ZIP Codes are delivery routes, not exact boundaries.
- ZCTAs are Census-created approximations and do not represent every valid USPS ZIP Code.
- ZIP-only lookup can at most surface possible district mappings, not a definitive address-level representative.
- Auto-select must remain blocked for ambiguous, multi-state, stale, fixture, or metadata-incomplete rows.

Production approval blockers:
- `bounded_production_write_plan_not_approved`
- `current_house_member_metadata_gate_not_implemented`
- `duplicate_current_house_member_match_gate_not_implemented`
- `zcta_does_not_cover_all_usps_zip_codes_or_provide_address_level_precision`

## Dry-Run Report Summary

- Input: `.local/zip_source_official/tab20_cd11920_zcta520_natl.txt`
- Input classification: `verified_official_file`
- Official-file identity verified: `True`
- Expected file name: `tab20_cd11920_zcta520_natl.txt`
- Actual file name: `tab20_cd11920_zcta520_natl.txt`
- File name matches: `True`
- Expected file size: `6195997` bytes
- Actual file size: `6195997` bytes
- File size matches: `True`
- Expected SHA-256: `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77`
- Actual SHA-256: `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77`
- SHA-256 matches: `True`
- File size: `6195997` bytes
- SHA-256: `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77`
- Row count: `40397`
- Accepted row count: `39967`
- Rejected row count: `430`
- Unique ZIP/ZCTA count: `33642`
- State count: `51`
- Unique state-district pair count: `436`
- Same-state multi-district count: `5725`
- Multi-state count: `137`
- Duplicate active row count: `0`
- Missing required metadata count: `0`
- Invalid ZIP/ZCTA format count: `250`
- Invalid state count: `154`
- Invalid district count: `34`
- Source-only future auto-select candidate count: `27780`
- Future auto-select eligible ZIP count: `0`
- Any row auto-select eligible under strict gates: `False`
- Explicit no DB write: `True`
- `zip_district_mappings` remains empty: `True`
- Public routes still read `zip_district_map`: `True`

Confidence distribution:
- `source_backed`: `40397`

Currentness distribution:
- `current`: `40397`

## Rejected Rows
- line `2` `` `AL` `01`: invalid_zip_zcta_format
- line `113` `` `AL` `02`: invalid_zip_zcta_format
- line `255` `` `AL` `03`: invalid_zip_zcta_format
- line `571` `` `AL` `06`: invalid_zip_zcta_format
- line `662` `` `AL` `07`: invalid_zip_zcta_format
- line `809` `` `AK` `00`: invalid_zip_zcta_format
- line `1055` `` `AZ` `01`: invalid_zip_zcta_format
- line `1099` `` `AZ` `02`: invalid_zip_zcta_format
- line `1343` `` `AZ` `06`: invalid_zip_zcta_format
- line `1423` `` `AZ` `07`: invalid_zip_zcta_format
- line `1498` `` `AZ` `08`: invalid_zip_zcta_format
- line `1534` `` `AZ` `09`: invalid_zip_zcta_format
- line `1608` `` `AR` `01`: invalid_zip_zcta_format
- line `1892` `` `AR` `02`: invalid_zip_zcta_format
- line `1998` `` `AR` `03`: invalid_zip_zcta_format
- line `2073` `` `AR` `04`: invalid_zip_zcta_format
- line `2308` `` `CA` `01`: invalid_zip_zcta_format
- line `2449` `` `CA` `02`: invalid_zip_zcta_format
- line `2591` `` `CA` `03`: invalid_zip_zcta_format
- line `2720` `` `CA` `04`: invalid_zip_zcta_format

## Safety Confirmations
- script_has_no_database_dependency: `True`
- script_fail_closed_without_dry_run_flag: `True`
- report_only_output: `True`
- no_insert_update_delete_truncate_drop_or_copy_executed: `True`
- zip_district_mappings_expected_to_remain_empty: `True`
- public_lookup_behavior_expected_unchanged: `True`

## Validation
- `python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env`: passed; Read-only; migration_applied false; row count 0; unique ZIP count 0; auto-select eligible count 0.
- `python backend\scripts\dry_run_zip_source_import.py --dry-run --input .local\zip_source_official\tab20_cd11920_zcta520_natl.txt --output docs\review_packets\zip_source_retrieval_official_file_dry_run_v1.json --markdown-output docs\review_packets\zip_source_retrieval_official_file_dry_run_v1.md`: passed; Parsed the ignored local official file and generated no-write JSON and Markdown packets.
- `$env:DATABASE_URL='postgresql://invalid'; python -m pytest backend\tests\test_api_lookup.py backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py backend\tests\test_zip_multi_row_readonly_route_eval.py backend\tests\test_zip_source_dry_run_import.py -p no:cacheprovider`: passed; 36 passed, including pinned identity, spoofed-filename fail-closed, and PR #85 default-path coverage.
- `python -m json.tool docs\review_packets\zip_source_retrieval_official_file_dry_run_v1.json`: passed; Valid JSON.
- `python -m json.tool docs\review_packets\zip_source_approval_dry_run_harness_v1.json`: passed; Valid JSON.

## Recommended Next Milestone

ZIP Source-to-Member Readiness Gate V1: design and validate current House member matching, duplicate-member blocking, stale-member blocking, territory handling, and bounded rollback/preflight artifacts without loading national mappings or switching public routes.
