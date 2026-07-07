# Milestone Plan: ZIP Lookup Ambiguity UI States V1

## Intent

- Immediate task: implement honest lookup states for the existing ZIP lookup flow.
- Larger-goal alignment: prevent ZIP-only evidence from auto-selecting the wrong House member before national ZIP/address rollout.

## Outcome

- User-visible or operational result: ZIP lookup now classifies safe and unsafe states, labels sample/ambiguous/unsupported results, and gates automatic profile selection.

## Scope And Boundaries

- In scope: lookup-state helper, frontend ZIP panel copy and auto-selection rules, additive ZIP lookup payload metadata, focused helper/backend/rendered tests, and review packet.
- Out of scope: address lookup, provider integrations, national ZIP ingestion, schema changes, production or local DB mutation, vote interpretation semantics, member coverage expansion, and Record Across behavior changes.
- Files/systems likely touched: `frontend/lib/zipLookupState.mjs`, `frontend/components/ZipLookupPanel.js`, rendered test harness files, additive backend lookup payload fields, focused tests, this plan, and the review packet.

## Decision Envelope

- Codex may decide and execute: state names, helper shape, UI copy placement, additive payload fields, test fixture shape, and docs wording within the approved milestone.
- Explicit approval required for: address collection, provider/API use, national data ingestion, DB/schema changes, production writes, or changing vote/member interpretation semantics.

## Definition Of Done

- [x] Branch created from clean `main` after PR #75.
- [x] Applicable repo instructions and requested recent docs read.
- [x] Backend lookup/search/schema, frontend lookup/home/API, tests, golden render harness, ZIP fixtures, and legislator fixtures inspected.
- [x] Lookup-state modeling implemented for required states.
- [x] House auto-select gated to `single_district_ready` only.
- [x] Manual representative search fallback remains visible.
- [x] Additive backend metadata added where needed for fixture/sample and local split-ZIP detection.
- [x] Focused helper, backend, and rendered tests added.
- [x] Tests/build/validation recorded.
- [x] Review packet updated.
- [ ] Focused draft PR opened.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/zip-lookup-ambiguity-ui-states-v1` from `main` at PR #75 merge commit `240d388515b0a7e6c1e968c70d4ed3e8c099a172`.
- Production/deployment state, if relevant: no production write, production credential use, address lookup, or data ingestion authorized.
- Tracked working tree: branch started from updated `main`; status reports permission warnings for existing `.pytest_tmp*` directories.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read instructions, plan conventions, interpretation principles, and recent ZIP/address/metadata docs.
2. Inspect current backend lookup, frontend ZIP panel, home/sample behavior, API helper, tests, render harness, and fixtures.
3. Add shared lookup-state classifier and tests.
4. Add additive backend ZIP lookup metadata and focused backend test coverage.
5. Update `ZipLookupPanel` to render state copy and gate auto-select/race/compare behavior.
6. Add a gated rendered fixture and Playwright state tests.
7. Document behavior, limitations, validation, and next milestone.
8. Stage only intended files, commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Existing ZIP lookup payloads did not expose `data_source`, so the frontend could not reliably detect fixture/sample fallback from `/lookup/zip/{zip_code}`.
- Backend fallback lookup used one first matching ZIP row, while local fixture files collectively contain ZIP `27601` mapped to `NC-02` and `NC-04`.
- The DB schema still cannot represent multiple rows for one ZIP because `zip_district_map.zip` is a primary key.
- The existing frontend auto-opened any returned `house_rep` and loaded ZIP race context on any successful ZIP lookup.
- Existing manual representative search lives lower on the home page, so the ZIP panel needed a visible link to it.

## Decisions And Rationale

- Keep backend changes additive and backward-compatible: existing `zip`, `state`, `district`, `house_rep`, and `senators` remain, while `data_source`, `lookup_metadata`, and `district_mappings` are added.
- Classify database ZIP rows without source date/version as `stale_or_unknown_source`, blocking auto-select until a future source metadata milestone supplies currentness evidence.
- Classify fixture ZIP rows as `fixture_sample_only` unless a more severe ambiguity is present; ambiguous fixture rows also carry the sample caveat.
- Do not implement address entry or mention it as available; copy points users to representative-name search and says address lookup is future-only.
- Add a gated render fixture rather than pulling a component testing library into the repo.

## Deviations Or Corrections

- Full backend suite was attempted because backend code changed, but local execution was limited by existing database/cache/temp state. Focused backend read-layer tests passed and the broad-suite limitation is recorded below.

## Validation Results

- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 8/8.
- `npx playwright test tests/zip-lookup-state.spec.mjs` from `frontend`: passed, 4/4. Existing `NO_COLOR`/`FORCE_COLOR` warning emitted by the web server.
- `node --test lib\*.test.mjs` from `frontend`: passed, 83/83. Existing Node module-type warnings remain.
- `npm run lint` from `frontend`: passed with 8 existing React hook dependency warnings and 0 errors.
- `npm run build` from `frontend`: passed with the same 8 hook dependency warnings.
- `python -m pytest backend\tests\test_db_read_layer.py -p no:cacheprovider`: passed, 7/7.
- `python -m pytest backend\tests -p no:cacheprovider`: 341 passed, 6 failed, 25 errors. Failures were local-environment limited: API tests read the configured local database instead of fixture fallback, and many setup errors could not read `C:\Users\Dylan\AppData\Local\Temp\pytest-of-Dylan`. No focused ZIP read-layer regression was found.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the helper, ZIP panel changes, additive backend metadata, focused tests, gated rendered fixture, and docs from this branch.

## Blockers

- None for this milestone.

## Final Reconciliation

- Definition of done satisfied:
- Remaining limitations: production multi-district ZIP detection still needs a future schema/data source milestone; database source date/version metadata is not available yet, so database ZIP results are conservatively stale/unknown for auto-select purposes.
- Recommended next step: ZIP Source Metadata And Ambiguity Payload V1.
