# Milestone Plan: ZIP Source Metadata And Ambiguity Payload V1

## Objective

- Immediate task: standardize ZIP lookup source metadata and ambiguity payloads so the frontend can distinguish production-ready, fixture/sample, stale/unknown, ambiguous, and unsupported ZIP states.
- Larger-goal alignment: keep the ZIP expansion path safe before any national ZIP ingestion, address lookup, or production write.
- User-visible or operational result: additive ZIP lookup metadata, local read-only coverage reports, focused tests, and a draft PR.

## Scope

- In scope: backend ZIP lookup payload metadata, fixture split-ZIP payloads, frontend ZIP lookup state classification, read-only local metadata coverage report, deterministic JSON/Markdown review packets, focused tests, and PR creation.
- Out of scope: address lookup, provider integration, national ZIP data ingestion, schema migration, production DB mutation, broad member coverage expansion, vote interpretation changes, Record Across changes, and public profile copy changes.
- Files/systems likely touched: `backend/app/api/precomputed.py`, `backend/scripts/generate_zip_source_metadata_report.py`, focused backend tests, `frontend/lib/zipLookupState.mjs`, frontend helper tests, generated review packet outputs, and this plan.

## Safety Gates

- Missing ZIP source metadata remains unsafe.
- Database ZIP rows without source/date/version/currentness metadata must return `source_currentness: "stale_or_unknown"` and `stale_or_unknown_source: true`.
- Fixture ZIP rows must return `source_currentness: "fixture_sample"` and `fixture_sample_only: true`.
- House auto-select remains limited to `single_district_ready`.
- No production writes, schema changes, address collection, provider calls, or data ingestion.

## Checklist

- [x] Recent ZIP ambiguity/UI design docs inspected.
- [x] Active plan created.
- [x] Backend ZIP lookup payload metadata standardized.
- [x] Frontend classifier updated for explicit currentness metadata.
- [x] Read-only metadata report generator added.
- [x] Review packet Markdown/JSON generated.
- [x] Focused backend and frontend tests added/updated.
- [x] Validation run.
- [x] Commit, push, and draft PR opened.

## Discoveries

- PR #76 already added additive `data_source`, `lookup_metadata`, and `district_mappings` fields, but the metadata contract is partial.
- Current `zip_district_map.zip` is a primary key, so the DB schema cannot store multiple district rows for one ZIP.
- Current DB ZIP rows expose no source name, retrieval date, effective date, or version, so DB lookup must remain `stale_or_unknown_source`.
- Repository fixture ZIP files have ZIP/state/district rows only; they do not include source metadata.
- The frontend already blocks auto-select for fixture, ambiguous, multi-state, unsupported, stale/unknown, and uncertain-member states.

## Validation Plan

- `python -m pytest backend\tests\test_db_read_layer.py backend\tests\test_zip_source_metadata_report.py -p no:cacheprovider`
- `python backend\scripts\generate_zip_source_metadata_report.py`
- `python -m json.tool docs\review_packets\zip_source_metadata_ambiguity_payload_v1.json`
- From `frontend`: `node --test lib\zipLookupState.test.mjs`
- From `frontend`: `node --test lib\*.test.mjs`
- From `frontend`: `npm run lint`
- From `frontend`: `npm run build`

## Validation Results

- `python -m pytest backend\tests\test_db_read_layer.py backend\tests\test_zip_source_metadata_report.py -p no:cacheprovider`: passed, 10/10.
- `python backend\scripts\generate_zip_source_metadata_report.py`: passed; wrote Markdown and JSON review packets.
- `python -m json.tool docs\review_packets\zip_source_metadata_ambiguity_payload_v1.json`: passed.
- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 9/9.
- `node --test lib\*.test.mjs` from `frontend`: passed, 84/84 with existing module-type warnings.
- `npm run lint` from `frontend`: passed with 8 existing React hook dependency warnings.
- `npm run build` from `frontend`: passed with the same 8 hook dependency warnings.
- `npx playwright test tests/zip-lookup-state.spec.mjs` from `frontend`: sandbox run hit `spawn EPERM`; rerun with elevated browser subprocess permission passed, 4/4, with existing `NO_COLOR`/`FORCE_COLOR` warnings.

## Rollback Paths

- Revert the additive ZIP payload helpers, frontend classifier/test updates, report generator/tests, generated review packets, and this plan from the branch.

## Blockers

- None currently. Production metadata truth still requires a future explicitly authorized read-only production report with credentials.
