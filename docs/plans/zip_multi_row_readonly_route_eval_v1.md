# Milestone Plan: ZIP Multi-Row Read-Only Coverage And Route-Path Evaluation V1

## Intent

- Verify the ZIP expansion safety posture after PR #81 without changing production behavior.
- Design the future multi-row lookup route path behind a default-false flag before any source-backed ZIP ingestion or auto-select behavior exists.

## Outcome

- Operational result: read-only postcheck confirms `zip_district_mappings` remains empty, and static route evaluation confirms public ZIP endpoints still use the old compatibility path.
- Review result: future route-switch criteria are documented as stricter than the current source-known heuristic.

## Scope And Boundaries

- In scope: route/static analysis, read-only DB postcheck, contract tests proving the new table is not wired into public ZIP lookup behavior, future design notes, and review packet outputs.
- Out of scope: migration rerun, seed loading, national ZIP ingestion, provider integration, address lookup, route switch, frontend runtime changes, and production data mutation.

## Decision Envelope

- Codex may decide the static test shape and review packet structure.
- Any future route switch, source-backed ZIP ingestion, backend unsupported payload contract, frontend behavior change, or production data write requires a later explicit milestone.

## Definition Of Done

- [x] Start from latest `main` after PR #81.
- [x] Run read-only postcheck only and stop if `zip_district_mappings` contains rows.
- [x] Confirm `/lookup/zip/{zip}` delegates to `get_zip_lookup_response`.
- [x] Confirm `/lookup/zip/{zip}/races` delegates to `get_zip_race_response`.
- [x] Confirm current read layer still queries `zip_district_map`, not `zip_district_mappings`.
- [x] Add static/contract tests for current route behavior.
- [x] Document future default-false `ZIP_MULTI_ROW_LOOKUP_ENABLED=false` design.
- [x] Document stricter future auto-select eligibility.
- [x] Document current-member metadata, UI behavior, and unsupported payload gaps.
- [x] Generate Markdown and JSON review packets.

## Baseline

- Branch: `codex/zip-multi-row-readonly-route-eval-v1`.
- Base: latest `main` at PR #81 merge commit `ed6b37ed9324008513d5b25e07d7307ad9fcdbc0`.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read the milestone request, plan/runbook docs, ZIP routes, read layer, migration helper, report script, tests, and frontend classifier.
2. Run the migration helper in `--postcheck-only` mode against `backend/.env`.
3. Add focused static route contract tests.
4. Create review packet Markdown/JSON with current posture, future switch design, strict gates, and gaps.
5. Run focused backend ZIP tests, frontend ZIP classifier tests, JSON validation, and read-only postcheck.

## Progress Checklist

- [x] Discovery
- [x] Read-only postcheck
- [x] Implementation
- [x] Validation
- [x] Final reconciliation

## Discoveries

- `zip_district_mappings` exists and remains empty: row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- `/lookup/zip/{zip}` still calls `get_zip_lookup_response`.
- `/lookup/zip/{zip}/races` still calls `get_zip_race_response`.
- Both database ZIP paths still share `_get_db_zip_record`, which selects from `zip_district_map`.
- No `FROM zip_district_mappings` or `JOIN zip_district_mappings` query is wired into `backend/app/api`.
- The current frontend classifier is safe for existing production payloads because the old DB path emits `stale_or_unknown_source`, but its generic source-known heuristic is not strict enough for a future source-backed route switch.

## Decisions And Rationale

- Keep all runtime behavior unchanged.
- Treat `ZIP_MULTI_ROW_LOOKUP_ENABLED=false` as design documentation only in this milestone.
- Require future source-backed route-switch work to implement stricter backend and frontend gates before returning `single_district_ready`.

## Deviations Or Corrections

- None so far.

## Validation Results

- `python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env`: passed; migration was not applied, row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- `python -m pytest backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py backend\tests\test_zip_multi_row_readonly_route_eval.py -p no:cacheprovider`: passed, 23/23.
- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 9/9.
- `python -m json.tool docs\review_packets\zip_multi_row_readonly_route_eval_v1.json`: passed.
- `python -m json.tool docs\review_packets\zip_multi_row_schema_migration_application_coverage_v1.json`: passed.

## Production Writes

- Performed: no.
- Read-only production/Supabase inspection: yes, postcheck-only mode.

## Rollback Paths

- Revert the static tests, plan, and review packet files from this branch.
- No database rollback is needed because this milestone performs no production writes.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: yes.
- Current route behavior unchanged: yes.
- `zip_district_mappings` remains empty: yes.
- Runtime behavior changed: no.
- Remaining limitation: future source-backed route switch must harden backend and frontend gates before any `single_district_ready` auto-select is allowed from `zip_district_mappings`.
