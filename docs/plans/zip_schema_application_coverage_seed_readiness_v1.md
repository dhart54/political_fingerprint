# Milestone Plan: ZIP Schema Application, Coverage, And Seed Readiness V1

## Intent

- Immediate task: prove the additive `zip_district_mappings` schema can be verified, reported on, and prepared for a tiny reviewed seed format without changing public lookup behavior.
- Larger-goal alignment: prepare controlled ZIP expansion while preserving the PR #76/#77/#79 gates for source currentness, ambiguity, fixture/sample rows, stale/unknown sources, and auto-select safety.

## Outcome

- Operational result: static schema verification, optional read-only DB coverage reporting, a non-production seed sample and validator, payload-readiness tests, and a focused review packet.

## Scope And Boundaries

- In scope: migration auto-apply confirmation, static SQL contract verification, read-only coverage report mode labels, seed-readiness validation, non-production seed fixture, focused tests, and review docs.
- Out of scope: production migration, production DB mutation, national ZIP ingestion, address lookup, provider integration, route switch to `zip_district_mappings`, and frontend gate weakening.
- Files/systems likely touched: report generator, seed-readiness helper/tests, seed fixture, ZIP schema/report/payload tests, active plan, and review packet outputs.

## Decision Envelope

- Codex may decide local validator/report structure, static-versus-DB report labels, and non-production seed sample shape.
- Explicit approval required for production credentials, production migration application, seed loading, national ZIP data, address lookup, provider choice, or any public lookup behavior change.

## Definition Of Done

- [x] Migration auto-apply behavior checked and documented.
- [x] `0013_zip_district_mappings.sql` remains additive and static schema contract tests cover required constraints/indexes.
- [x] Report can clearly label repository/static-only, local/test DB read-only, and production read-only modes.
- [x] Seed file format and validator cover required fields, metadata, currentness, confidence, ambiguity, multi-state, duplicate, and auto-select rules.
- [x] Payload readiness tests cover single, ambiguous, multi-state, stale/unknown, fixture/sample, unsupported, and old path states.
- [x] Tests/build/validation recorded.
- [x] Review packet and JSON generated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/zip-schema-application-coverage-seed-readiness-v1` from local `main` after PR #79.
- Production/deployment state: Render start command is documented as `uvicorn app.main:app --host 0.0.0.0 --port $PORT`; no startup migration runner found.
- Tracked working tree: clean before milestone edits.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read applicable rules, recent ZIP plans/review packets, migration/deployment docs, routes, report script, fixtures, and tests.
2. Confirm migrations do not auto-apply on startup/deployment.
3. Add seed-readiness validator and non-production sample fixture.
4. Extend report generator with mode labels, migration auto-apply finding, optional read-only DB coverage, seed validation, and new milestone packet outputs.
5. Add focused seed/report tests and preserve route/frontend behavior.
6. Run requested backend/report/frontend validation.
7. Commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Migration auto-apply was not found: deployment docs use direct `uvicorn`, `backend/app/main.py` only initializes the FastAPI app/routers, and `0013` explicitly says startup does not apply it.
- No reliable temporary Postgres test database support exists in the repository, so isolated schema application remains a documented limitation and static SQL contract tests remain the safe local gate.
- The public lookup route still delegates to `get_zip_lookup_response`, and the read layer still queries `zip_district_map`.

## Decisions And Rationale

- Keep `backend/migrations/0013_zip_district_mappings.sql` unchanged because migrations are not auto-applied.
- Add the seed validator under `backend/app/etl` so it is reusable by reports/tests but not a public API path.
- Make DB coverage report inspection opt-in via `--db-url` and default to repository/static-only mode to avoid accidental production credential use.
- Use `backend/fixtures/zip_reviewed_seed_sample/zip_district_mappings.json` as a tiny non-production seed-format sample with fixture/sample currentness so it cannot be auto-select eligible.

## Deviations Or Corrections

- Isolated database application was not added because no reliable temporary Postgres support is present. Static migration contract coverage is retained and the limitation is recorded in the report packet.

## Validation Results

- `python -m pytest backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py -p no:cacheprovider`: passed, 20/20.
- `python backend\scripts\generate_zip_source_metadata_report.py`: passed; wrote source metadata packet plus `zip_schema_application_coverage_seed_readiness_v1` Markdown/JSON.
- `python -m json.tool docs\review_packets\zip_source_metadata_ambiguity_payload_v1.json`: passed.
- `python -m json.tool docs\review_packets\zip_schema_application_coverage_seed_readiness_v1.json`: passed.
- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 9/9.
- `node --test lib\*.test.mjs` from `frontend`: passed, 84/84 with existing module-type warnings.
- `npm run lint` from `frontend`: passed with 8 existing React hook dependency warnings.
- `npm run build` from `frontend`: passed with the same 8 hook dependency warnings.
- `git diff --check`: passed with expected LF-to-CRLF warnings for touched Python files.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the seed-readiness helper, seed sample fixture, report generator additions, focused tests, and generated docs/review packets from this branch.
- No database rollback is needed because no migration or seed was applied locally or in production.

## Blockers

- None currently. A future production-backed report or migration requires explicit approval and credentials.

## Final Reconciliation

- Definition of done satisfied: yes, including commit, push, and draft PR #80.
- Remaining limitations: no isolated local Postgres schema application; no production coverage truth; no production migration or seed load.
- Recommended next step: explicit production migration preflight/application milestone with rollback and read-only coverage validation, still without route switch or national ingestion.
