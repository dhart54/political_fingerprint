# ZIP Schema Application, Coverage, And Seed Readiness V1

## Summary

- Public lookup behavior changed: no
- Production migration applied: no
- Production seed loaded: no
- National ZIP data ingested: no
- Address lookup added: no
- Provider integration added: no

## Migration Auto-Apply Finding

No deployment/startup auto-apply migration runner was found; production migration remains a future manual approval step.

## Migration Application Status

| check | value |
| --- | --- |
| migration_file | backend/migrations/0013_zip_district_mappings.sql |
| migration_applied_anywhere | no |
| migration_applied_local_or_test | no |
| migration_applied_production | no |
| future_production_migration_requires_manual_approval | yes |

## Schema Application And Verification

| check | value |
| --- | --- |
| isolated_database_application_performed | no |
| isolated_database_limitation | No reliable temporary Postgres test database support is present in the repository; schema verification remains static SQL contract coverage. |
| static_schema_contract | `{"all_required_columns_present": true, "all_required_indexes_present": true, "all_source_metadata_columns_present": true, "can_represent_multiple_districts_per_zip": true, "confidence_check_values_present": {"inferred": true, "low": true, "reviewed": true, "source_backed": true, "unknown": true}, "controlled_confidence_check_present": true, "controlled_source_currentness_check_present": true, "indexes_present": {"source_currentness": true, "source_name": true, "source_version": true, "zip": true, "zip_state_district": true}, "migration_exists": true, "migration_file": "backend/migrations/0013_zip_district_mappings.sql", "old_table_compatibility_only": true, "old_table_untouched": true, "required_columns_present": {"confidence": true, "congress": true, "created_at": true, "cycle": true, "district": true, "district_type": true, "id": true, "is_primary": true, "notes": true, "provider_record_id": true, "source_currentness": true, "source_effective_date": true, "source_name": true, "source_retrieved_at": true, "source_type": true, "source_version": true, "state": true, "updated_at": true, "valid_from": true, "valid_to": true, "zip": true}, "source_currentness_check_values_present": {"current": true, "expired": true, "fixture_sample": true, "stale_or_unknown": true, "unsupported": true}, "source_metadata_columns_present": {"confidence": true, "source_currentness": true, "source_effective_date": true, "source_name": true, "source_retrieved_at": true, "source_type": true, "source_version": true}, "surrogate_id_primary_key": true, "table_found": true, "unique_active_source_period_rule": true, "zip_format_check": true, "zip_not_primary_key": true}` |
| zip_district_map_untouched | yes |

## Read-Only Coverage Report

- Mode: `repository/static only`
- DB table status: `not_inspected`
- Old route still gated: yes
- New-table route switch absent: yes

## Seed Format And Readiness

- Seed file: `backend/fixtures/zip_reviewed_seed_sample/zip_district_mappings.json`
- Required fields: `["zip", "state", "district", "source_name", "source_type", "source_retrieved_at", "source_effective_date", "source_version", "source_currentness", "confidence", "is_primary", "district_type", "congress", "cycle", "valid_from", "valid_to", "provider_record_id", "notes"]`
- Valid: yes
- Auto-select eligible ZIPs: 0
- Loaded into production: no

## Payload Readiness Results

| case | classification |
| --- | --- |
| single_current_source_backed_zip | single_district_ready |
| same_state_multi_district_zip | ambiguous_zip |
| multi_state_zip | multi_state_zip |
| missing_metadata | stale_or_unknown_source |
| fixture_sample | fixture_sample_only |
| unsupported_zip | unsupported_zip |
| old_zip_district_map_path | stale_or_unknown_source |

## Route Behavior Unchanged

| check | value |
| --- | --- |
| lookup_route_file | backend/app/api/lookup.py |
| read_layer_file | backend/app/api/precomputed.py |
| lookup_route_calls_get_zip_lookup_response | yes |
| current_lookup_route_uses_old_gated_path | yes |
| new_table_route_switch_absent | yes |
| production_api_new_table_read_references | `[]` |
| old_table_query_present | yes |
| new_table_query_present | no |
| db_path_source_currentness | stale_or_unknown |
| db_path_auto_select_blocked | yes |

## Old DB Path Gated

| check | value |
| --- | --- |
| source_currentness | stale_or_unknown |
| stale_or_unknown_source | yes |
| auto_select_blocked | yes |
| reason | The old zip_district_map table lacks source metadata and remains compatibility-only. |

## Known Limitations

- This report is repository/local-accessible only and does not certify production coverage truth.
- Current DB ZIP schema cannot store multiple districts for one ZIP.
- Current DB ZIP schema cannot store source name, retrieval date, effective date, or version.
- Fixture ZIP files are sample coverage and do not include source metadata.
- No provider or national ZIP data source has been selected or ingested.
- The new multi-row table is drafted locally but is not applied to production.
- Default report mode is repository/static only; DB table presence and row counts require an explicit read-only DB URL.
- No reliable temporary Postgres fixture is present in the repository, so local migration application remains statically verified.
- The reviewed seed sample is non-production and is not loaded into any database.
- The public lookup route still reads the compatibility zip_district_map path.
- The backend route still returns 404 for unsupported ZIPs; the frontend converts that failure into a local unsupported payload with data_source none, empty district_mappings, and null officials.

## No-Go Items Honored

- No address lookup.
- No Census, Google, Smarty, Cicero, or other provider integration.
- No national ZIP data ingestion.
- No local or production database mutation.
- No production migration application.
- No /lookup/zip/{zip} route switch to zip_district_mappings.
- No production seed load.
- No fake DB source metadata.
- No House auto-select for stale/unknown, fixture/sample, ambiguous, multi-state, unsupported, or uncertain-member states.
- No vote interpretation, Record Across, issue read, or profile copy changes.

## Recommended Next Milestone

ZIP Multi-Row Schema Migration Application And Read-Only Coverage V1: explicitly approve and apply the additive zip_district_mappings migration, verify the empty/new-table contract with read-only coverage checks, keep the old lookup path gated, and still avoid national ZIP ingestion or address lookup.
