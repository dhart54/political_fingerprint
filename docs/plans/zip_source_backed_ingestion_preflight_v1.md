# Milestone Plan: ZIP Multi-Row Source-Backed Ingestion Preflight V1

## Intent

- Prepare the source-backed ZIP ingestion path without ingesting data or changing production lookup behavior.
- Define the source contract, bounded future ingestion plan, rollback expectations, unsupported ZIP payload contract, and route-switch gates while keeping `ZIP_MULTI_ROW_LOOKUP_ENABLED=false`.

## Outcome

- Operational result: no production writes and no route behavior change.
- Product/readiness result: a backend-owned unsupported ZIP payload helper exists for future adoption, and the future ingestion/runbook criteria are documented with caps, stop conditions, and stricter auto-select requirements.

## Scope And Boundaries

- In scope: plan, review packet, backend unsupported payload contract helper/tests, static route checks, read-only postcheck, future ingestion/runbook documentation, and source approval criteria.
- Out of scope: national ZIP ingestion, seed loading, production row insertion/update/deletion, migration rerun, public route switch, `ZIP_MULTI_ROW_LOOKUP_ENABLED` enablement, provider API integration, address lookup, frontend runtime changes, fake production metadata, and removal of `zip_district_map`.

## Decision Envelope

- Codex may define the source approval record shape, future dry-run/cap/rollback requirements, and unsupported payload contract helper.
- A future milestone must explicitly approve the actual source/provider, exact data scope, write caps, rollback, confirmation phrase, and any route switch.
- This milestone does not authorize production writes or source-backed ZIP row creation.

## Definition Of Done

- [x] Start from latest `main` after PR #82.
- [x] Confirm `zip_district_mappings` remains empty with postcheck-only/read-only verification.
- [x] Confirm public ZIP routes do not read `zip_district_mappings`.
- [x] Add backend tests for a standardized unsupported ZIP payload contract.
- [x] Preserve current supported ZIP responses.
- [x] Preserve current stale/unknown old-table payloads.
- [x] Keep frontend runtime unchanged.
- [x] Define source approval criteria for future ingestion.
- [x] Define future ingestion caps, dry-run, duplicate/ambiguity detection, rollback, and confirmation phrase.
- [x] Define future route-switch acceptance criteria with `ZIP_MULTI_ROW_LOOKUP_ENABLED=false` by default.
- [x] Generate Markdown and JSON review packets.
- [x] Run focused validation.
- [x] Prepare for commit, push, and draft PR.

## Baseline

- Branch: `codex/zip-source-backed-ingestion-preflight-v1`.
- Base: latest `main` after PR #82 merge commit `404753a7d772cef3d824c755dba0ba2cec742e77`.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read the milestone request, ZIP routes, read layer, migration helper, report scripts, ZIP tests, frontend classifier, and recent ZIP plans/review packets.
2. Run `backend/scripts/apply_zip_district_mappings_migration.py --postcheck-only` against `backend/.env`.
3. Add a backend-owned unsupported ZIP payload helper without wiring it into the current public route.
4. Add tests for unsupported payload shape and preserve current 404/old-table behavior.
5. Create source contract, ingestion runbook, future route-switch criteria, and review packet artifacts.
6. Run focused backend ZIP tests, frontend ZIP lookup tests, JSON validation, and postcheck-only verification.
7. Commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Read-only postcheck
- [x] Implementation
- [x] Validation
- [x] Commit/PR readiness

## Discoveries

- `zip_district_mappings` remains empty: row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- `/lookup/zip/{zip}` and `/lookup/zip/{zip}/races` still resolve ZIP state/district through `zip_district_map`.
- `backend/tests/test_api_lookup.py` asserts unsupported ZIPs currently raise a 404 with detail `"ZIP code not found"`, so returning a standardized payload from the route now would be a public behavior change.
- The safe path for this milestone is to add a backend-owned payload builder and tests, then wire it into the route only in a later behavior-change milestone.

## Decisions And Rationale

- Do not select a concrete external provider in this milestone. Instead, define the source approval record required before ingestion so the later source choice can be reviewed explicitly.
- Do not wire the unsupported helper into `lookup_zip` yet, because the current frontend normalizes 404s and current API behavior should remain unchanged.
- Require future `single_district_ready` eligibility to be enforced by backend and frontend gates, not merely by presence of some source metadata.

## Deviations Or Corrections

- Backend-owned unsupported payload behavior is implemented as a tested helper, not as a public route response, to avoid changing current production behavior.
- Initial backend validation without a `DATABASE_URL` override picked up the real database URL and failed fixture-specific `test_api_lookup.py` expectations. Rerun with `DATABASE_URL=postgresql://invalid` passed and matches the repository's documented fixture-mode pattern.

## Validation Results

- `python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env`: passed; migration was not applied, row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- Initial `python -m pytest backend\tests\test_api_lookup.py backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py backend\tests\test_zip_multi_row_readonly_route_eval.py -p no:cacheprovider`: failed because local environment used live DB rows for fixture-specific assertions.
- `$env:DATABASE_URL='postgresql://invalid'; python -m pytest backend\tests\test_api_lookup.py backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py backend\tests\test_zip_multi_row_readonly_route_eval.py -p no:cacheprovider`: passed, 29/29.
- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 9/9.
- `python -m json.tool docs\review_packets\zip_source_backed_ingestion_preflight_v1.json`: passed.
- `python -m json.tool docs\review_packets\zip_multi_row_readonly_route_eval_v1.json`: passed.

## Production Writes

- Performed: no.
- Read-only production/Supabase inspection: yes, postcheck-only mode.

## Rollback Paths

- Revert the unsupported payload helper, tests, plan, and review packet files from this branch.
- No database rollback is needed because no production write occurs.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: yes.
- Production writes performed: no.
- Route behavior changed: no.
- Frontend runtime changed: no.
- Remaining limitation: concrete source/provider approval and dry-run parser are deferred to the next milestone.
