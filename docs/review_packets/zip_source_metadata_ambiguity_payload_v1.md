# ZIP Source Metadata And Ambiguity Payload V1

## Summary

This is repository/local-accessible ZIP metadata only. It is not production coverage truth unless a future read-only production report is generated with credentials.

- Read-only: yes
- Requires production credentials: no
- Fixture ZIP rows inspected: 9
- Fixture unique ZIPs: 4
- DB path source currentness: `stale_or_unknown`
- DB path auto-select blocked: yes
- Fixture path source currentness: `fixture_sample`
- Unsupported payload backend-owned: no

Highest findings:
- Database ZIP rows cannot yet store source name, retrieval date, effective date, or version metadata.
- Database ZIP lookup remains conservatively gated as stale_or_unknown_source.
- Fixture ZIP files do not include source metadata and remain fixture_sample_only.
- The current schema cannot store multiple districts per ZIP because zip is the primary key.
- Frontend auto-select remains blocked unless a payload classifies as single_district_ready.

## Payload Contract

- `data_source`: `database, fixtures, none`
- `lookup_metadata`: all standardized fields are present on ZIP lookup payloads.
- `source_currentness`: `current, stale_or_unknown, fixture_sample, unsupported`
- `ambiguity_detection_level`: `single_row, local_fixture_scan, multi_row_source, none`
- `district_mappings`: array of ZIP/state/district mapping rows plus source type/name/version.
- `house_rep`: object or null.
- `senators`: array.

## DB ZIP Metadata Coverage

| check | value |
| --- | --- |
| schema_file | backend/migrations/0001_initial_schema.sql |
| zip_table_found | yes |
| zip_primary_key | yes |
| can_store_multiple_districts_per_zip | no |
| can_store_source_name | no |
| can_store_source_retrieved_at | no |
| can_store_source_effective_date | no |
| can_store_source_version | no |
| can_store_source_metadata | no |
| current_db_lookup_source_currentness | stale_or_unknown |
| current_db_lookup_stale_or_unknown_source | yes |
| current_db_ambiguity_detection_level | single_row |
| evidence | zip_district_map.zip is the primary key and the table has zip, state, district, created_at, and updated_at columns only. |

## Fixture ZIP Metadata Coverage

| check | value |
| --- | --- |
| fixture_files | `["backend/fixtures/congress_sample/zip_district_map.json", "backend/fixtures/house_clerk_sample/zip_district_map.json", "backend/fixtures/senate_xml_sample/zip_district_map.json", "backend/fixtures/zip_district_map.json"]` |
| fixture_row_count | 9 |
| unique_zips | 4 |
| rows_with_source_name | 0 |
| rows_with_source_retrieved_at | 0 |
| rows_with_source_effective_date | 0 |
| rows_with_source_version | 0 |
| rows_with_all_source_metadata | 0 |
| fixture_zip_files_include_source_metadata | no |
| source_currentness | fixture_sample |
| fixture_sample_only | yes |
| stale_or_unknown_source | yes |
| can_represent_multiple_districts | yes |
| ambiguity_detection_level | local_fixture_scan |
| multi_district_zips | `{"27601": ["NC-02", "NC-04"]}` |
| multi_state_zips | `{}` |
| counts_by_zip | `{"27601": 3, "27701": 4, "77007": 1, "94102": 1}` |

## API Response Contract

| check | value |
| --- | --- |
| backend_lookup_file | backend/app/api/precomputed.py |
| standard_metadata_fields_present | `{"ambiguity_detection_level": true, "can_represent_multiple_districts": true, "fixture_sample_only": true, "member_metadata_uncertain": true, "source_currentness": true, "source_effective_date": true, "source_name": true, "source_retrieved_at": true, "source_type": true, "source_version": true, "stale_or_unknown_source": true}` |
| api_responses_include_standard_metadata_fields | yes |
| district_mappings_field_present | yes |
| district_mapping_source_fields_present | yes |
| db_path_declares_stale_or_unknown | yes |
| fixture_path_declares_fixture_sample | yes |
| db_path_ambiguity_detection_level | single_row |
| fixture_path_ambiguity_detection_level | local_fixture_scan |
| unsupported_payload_backend_owned | no |
| unsupported_payload_frontend_normalized | yes |
| unsupported_route_still_404 | yes |
| unsupported_limitation | The backend route still returns 404 for unsupported ZIPs; the frontend converts that failure into a local unsupported payload with data_source none, empty district_mappings, and null officials. |

## Frontend Gating Implications

| check | value |
| --- | --- |
| classifier_file | frontend/lib/zipLookupState.mjs |
| gates_missing_metadata | yes |
| gates_fixture_sample | yes |
| gates_multiple_districts | yes |
| gates_multiple_states | yes |
| gates_unsupported | yes |
| auto_select_only_single_district_ready | yes |
| current_source_metadata_can_be_ready | yes |
| current_db_path_remains_blocked_from_auto_select | yes |
| db_path_blocked_reason | Backend DB payloads currently set source_currentness to stale_or_unknown and stale_or_unknown_source to true because the schema lacks source metadata fields. |

## Ambiguity Capability By Source

| source | data_source | can_represent_multiple_districts | ambiguity_detection_level | source_currentness | auto_select_house_allowed_today | notes |
| --- | --- | --- | --- | --- | --- | --- |
| database | database | no | single_row | stale_or_unknown | no | Current DB schema stores one row per ZIP and has no source metadata columns. |
| fixtures | fixtures | yes | local_fixture_scan | fixture_sample | no | Local fixture scan can expose split ZIP rows but is sample coverage only. |
| none | none | no | none | unsupported | no | Unsupported ZIPs have no district mappings and no officials. |

## Coverage Checks

| check | passed |
| --- | --- |
| db_schema_can_store_multiple_districts_per_zip | no |
| db_schema_can_store_source_name | no |
| db_schema_can_store_source_retrieved_at | no |
| db_schema_can_store_source_effective_date | no |
| db_schema_can_store_source_version | no |
| fixture_zip_files_include_source_metadata | no |
| api_responses_include_standard_metadata_fields | yes |
| frontend_classifier_gates_missing_metadata | yes |
| current_db_path_remains_blocked_from_auto_select | yes |

## No-Go Items

- No address lookup.
- No Census, Google, Smarty, Cicero, or other provider integration.
- No national ZIP data ingestion.
- No local or production database mutation.
- No fake DB source metadata.
- No House auto-select for stale/unknown, fixture/sample, ambiguous, multi-state, unsupported, or uncertain-member states.
- No vote interpretation, Record Across, issue read, or profile copy changes.

## Known Limitations

- This report is repository/local-accessible only and does not certify production coverage truth.
- Current DB ZIP schema cannot store multiple districts for one ZIP.
- Current DB ZIP schema cannot store source name, retrieval date, effective date, or version.
- Fixture ZIP files are sample coverage and do not include source metadata.
- No provider or national ZIP data source has been selected or ingested.
- The backend route still returns 404 for unsupported ZIPs; the frontend converts that failure into a local unsupported payload with data_source none, empty district_mappings, and null officials.

## Recommended Next Milestone

ZIP Schema And Source Metadata Design V1: decide the DB shape for multi-district ZIP mappings, source name/retrieval/effective/version metadata, and production read-only coverage reporting before any national ZIP ingestion or address lookup.
