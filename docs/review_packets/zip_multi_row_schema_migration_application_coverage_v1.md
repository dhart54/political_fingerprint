# ZIP Multi-Row Schema Migration Application And Read-Only Coverage V1

## Summary

- Migration file: `backend\migrations\0013_zip_district_mappings.sql`
- Migration applied: yes
- Production-like migration applied: yes
- Seed data loaded: no
- National ZIP data ingested: no
- Public route switched: no

## Target

- Env file: `backend\.env`
- Host: `aws-1-us-east-1.pooler.supabase.com`
- Database: `postgres`
- Supabase host: yes
- Raw URL recorded: no

## Read-Only Post-Check

- `zip_district_mappings` exists: yes
- `zip_district_map` still exists: yes
- Row count: `0`
- Unique ZIP count: `0`
- Auto-select eligible count: `0`

## Contract Checks

- zip_district_mappings_exists: yes
- zip_district_map_still_exists: yes
- row_count_zero: yes
- unique_zip_count_zero: yes
- auto_select_eligible_count_zero: yes
- all_required_columns_present: yes
- all_source_metadata_columns_present: yes
- controlled_currentness_check_present: yes
- controlled_confidence_check_present: yes
- all_required_indexes_present: yes
- duplicate_active_source_period_rule_present: yes
- public_lookup_still_reads_old_path: yes
- new_table_route_switch_absent: yes

## Route Behavior

- Public lookup still reads old path: yes
- New table route switch absent: yes

## Rollback Posture

- The public lookup route remains on zip_district_map and no rows were loaded into zip_district_mappings.
- Schema rollback: Requires a separate explicit approval before any DROP TABLE action.

## Recommended Next Milestone

ZIP Multi-Row Read-Only Coverage And Route-Path Evaluation V1: keep the old lookup path gated, verify production remains empty/read-only, and only design a future route switch after source-backed data approval.
