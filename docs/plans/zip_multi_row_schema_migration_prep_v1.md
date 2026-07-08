# Milestone Plan: ZIP Multi-Row Schema Migration Prep V1

## Milestone Intent

- Immediate task: prepare the additive multi-row ZIP schema contract in repository code, tests, fixtures, and read-only reports without applying a migration or changing public lookup behavior.
- Larger-goal alignment: make a future production-safe ZIP expansion possible while preserving the PR #76/#77 gates.
- Operational outcome: draft migration, synthetic fixtures, route-adjacent payload parity tests, expanded read-only report checks, and a review packet.

## Scope And Boundaries

- In scope: additive `zip_district_mappings` migration draft, synthetic multi-row fixtures, schema/report tests, payload parity tests, report generation, and documentation.
- Out of scope: applying migrations to local or production databases, production writes, national ZIP ingestion, address lookup, provider integration, switching `/lookup/zip/{zip}` to the new table, and frontend behavior changes.
- Expected changed files: migration draft, synthetic fixture, report generator/tests, focused backend tests, active plan, review packet Markdown/JSON, and regenerated ZIP source metadata report outputs.

## Safety Decision

- Migration files are inert repository SQL drafts for deployment purposes: Render starts the backend with `uvicorn app.main:app` and no startup migration runner was found.
- Existing migration/application tooling indicates production migration application is explicit and approval-gated.
- Because `backend/migrations` already contains files through `0012`, this milestone adds `backend/migrations/0013_zip_district_mappings.sql`.

## Definition Of Done

- Recent ZIP schema/source, source metadata, and lookup-state docs are read.
- Current schema, lookup route, read layer, ETL ZIP dedupe, report, and classifier surfaces are inspected.
- Additive migration draft exists and does not drop or alter `zip_district_map`.
- Synthetic fixtures cover single-district, same-state multi-district, multi-state, fixture/sample, stale/unknown, current/source-backed, and duplicate-detection cases.
- Read-only report detects migration existence, multi-row support, source metadata columns, controlled checks, indexes, compatibility-only old table status, route unchanged, and route switch absent.
- Focused tests cover schema contract, fixture validation, report determinism, payload parity, and old DB path gating.
- Requested backend/frontend validation runs are recorded.
- Draft PR is opened.

## Progress Checklist

- [x] Attachment, `AGENTS.md`, and recent ZIP docs read.
- [x] Migration behavior checked.
- [x] ZIP schema/API/ETL/report/frontend surfaces inspected.
- [x] Active plan created.
- [x] Migration draft added.
- [x] Synthetic fixtures added.
- [x] Report generator extended and source report regenerated.
- [x] Focused schema/report/payload tests added.
- [x] Full requested validation run.
- [ ] Commit, push, and draft PR opened.

## Discoveries

- Current `zip_district_map` still uses `zip TEXT PRIMARY KEY`, so it remains compatibility-only for safe lookup gating.
- `backend/app/api/precomputed.py` still reads `FROM zip_district_map`; no `zip_district_mappings` route switch exists.
- ETL merge paths still dedupe ZIP rows by `zip`, so future ingestion work must update ETL before national data is loaded.
- Existing frontend gates already block auto-select unless the payload classifies as `single_district_ready`.

## Decisions And Rationale

- Add a new `zip_district_mappings` table instead of altering `zip_district_map`, matching the approved design recommendation.
- Use a surrogate `id` primary key so multiple rows per ZIP can exist.
- Use a unique active source-period expression index to reject duplicate active rows without blocking legitimate split ZIPs.
- Keep payload parity logic in tests, not the production route, because the milestone explicitly forbids switching public lookup behavior.
- Keep the synthetic fixture under a new sample directory and mark rows as synthetic/test-only.

## Validation Results

- `python -m pytest backend\tests\test_zip_source_metadata_report.py -p no:cacheprovider`: passed, 4/4.
- `python -m pytest backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py -p no:cacheprovider`: passed, 11/11.
- `python backend\scripts\generate_zip_source_metadata_report.py`: passed; wrote Markdown and JSON review packets.
- `python -m json.tool docs\review_packets\zip_source_metadata_ambiguity_payload_v1.json`: passed.
- `python -m json.tool docs\review_packets\zip_multi_row_schema_migration_prep_v1.json`: passed.
- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 9/9.
- `node --test lib\*.test.mjs` from `frontend`: passed, 84/84 with existing module-type warnings.
- `npm run lint` from `frontend`: passed with 8 existing React hook dependency warnings.
- `npm run build` from `frontend`: passed with the same 8 hook dependency warnings.

## Production Writes

- Performed: no.
- Scope: none.
- Production migration applied: no.

## Rollback Paths

- Revert the additive migration draft, synthetic fixture, report generator changes, focused tests, regenerated source report outputs, and review packet docs from this branch.
- No database rollback is required because no local or production database migration is applied.

## Blockers

- None for prep. A future milestone needs explicit approval before applying the additive migration or running credentialed production coverage.

## Final Reconciliation

- Additive schema prep is complete.
- No production or local DB migration was applied.
- Public lookup behavior is unchanged and still uses the old gated `zip_district_map` path.
- Recommended next milestone: ZIP Multi-Row Schema Migration Application And Read-Only Coverage V1.
