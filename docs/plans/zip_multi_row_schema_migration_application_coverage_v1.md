# Milestone Plan: ZIP Multi-Row Schema Migration Application And Read-Only Coverage V1

## Intent

- Immediate task: apply the additive `zip_district_mappings` migration to the explicitly approved Supabase database referenced by `backend/.env`.
- Larger-goal alignment: establish the empty/new-table contract without loading ZIP data, changing public lookup behavior, or weakening the existing ZIP readiness gates.

## Outcome

- Operational result: `backend/migrations/0013_zip_district_mappings.sql` was applied to the approved Supabase target and verified with read-only post-checks.
- The new table remains empty, and the existing `zip_district_map` compatibility path remains the public lookup path.

## Scope And Boundaries

- In scope: bounded migration preflight, additive migration application, read-only schema/count verification, review packet generation, and a reusable migration application helper.
- Out of scope: seed loading, national ZIP ingestion, provider integration, address lookup, route switch to `zip_district_mappings`, frontend behavior changes, and any migration beyond `0013`.
- Files/systems touched: migration application helper and ZIP migration application review packet outputs.

## Decision Envelope

- User explicitly approved applying `0013_zip_district_mappings.sql` to the Supabase database in `backend/.env`.
- Codex could decide the bounded helper/report shape and read-only verification queries.
- Additional approval remains required for seed loading, national ZIP ingestion, route switch, address lookup, or schema rollback/drop actions.

## Definition Of Done

- [x] Confirm target is the Supabase database referenced by `backend/.env` without recording raw credentials.
- [x] Validate migration SQL is additive and contains no seed/data-load statements.
- [x] Run read-only preflight against the target.
- [x] Apply only `backend/migrations/0013_zip_district_mappings.sql`.
- [x] Verify `zip_district_mappings` exists and `zip_district_map` still exists.
- [x] Verify `zip_district_mappings` row count, unique ZIP count, and auto-select eligible count are all zero.
- [x] Verify required columns, source metadata columns, checks, indexes, and duplicate active source-period unique rule.
- [x] Confirm public lookup behavior remains on the existing `zip_district_map` path.
- [x] Confirm no seed data or national ZIP data was loaded.
- [x] Generate Markdown and JSON review packets.

## Baseline

- Branch: `codex/zip-multi-row-schema-migration-application-coverage-v1`.
- Starting point: clean `main` after PR #80, aside from unrelated untracked artifacts.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read the migration, existing ZIP reports, deployment/database docs, and route/read-layer code.
2. Add a narrow migration application helper that reads `DATABASE_URL` from `backend/.env`, masks credentials in output, and validates the bounded SQL envelope.
3. Run read-only preflight against the approved target.
4. Apply only `0013_zip_district_mappings.sql`.
5. Run read-only post-checks and write the review packet.
6. Validate generated JSON.
7. Commit only focused milestone files and open a draft PR.

## Progress Checklist

- [x] Discovery
- [x] Preflight
- [x] Migration application
- [x] Read-only post-check
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- `backend/.env` contains a Supabase Postgres pooler `DATABASE_URL`; the raw URL/password were not printed or recorded in the review packet.
- `0013_zip_district_mappings.sql` creates `zip_district_mappings` and indexes only; no seed/data-load statements were detected.
- The public lookup route still delegates to `get_zip_lookup_response`, and the read layer still queries `zip_district_map`.

## Decisions And Rationale

- Use an explicit confirmation flag for migration application so the helper cannot accidentally write to the Supabase target.
- Fail preflight if `zip_district_map` is missing or if `zip_district_mappings` already contains rows.
- Keep rollback operationally simple: no route rollback is needed because no route reads `zip_district_mappings`; schema rollback would require separate explicit approval.

## Validation Results

- `python backend\scripts\apply_zip_district_mappings_migration.py --preflight-only --env-path backend\.env --write-review-packet`: passed.
- `python backend\scripts\apply_zip_district_mappings_migration.py --apply --confirm-apply-to-backend-env-supabase --env-path backend\.env --write-review-packet`: passed.
- `python -m json.tool docs\review_packets\zip_multi_row_schema_migration_application_coverage_v1.json`: passed.

## Production Writes

- Performed: yes.
- Scope: additive application of `backend/migrations/0013_zip_district_mappings.sql` to the explicitly approved Supabase database referenced by `backend/.env`.
- Expected effects: create empty `zip_district_mappings` table and indexes while leaving `zip_district_map` unchanged.
- Actual effects: expected effects confirmed; row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- Seed data loaded: no.
- National ZIP data ingested: no.

## Rollback Paths

- Route rollback needed: no, because the public lookup path still reads `zip_district_map`.
- Data rollback needed: no, because no rows were loaded into `zip_district_mappings`.
- Schema rollback: requires a separate explicit approval before any destructive `DROP TABLE` action.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: the table is intentionally empty; no source-backed ZIP ingestion or lookup route switch has been performed.
- Recommended next step: read-only coverage and route-path evaluation before any source-backed ZIP ingestion or lookup route switch.
