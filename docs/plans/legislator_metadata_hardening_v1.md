# Milestone Plan: Legislator Metadata Hardening V1

## Intent

- Immediate task: implement read-only local metadata checks and generated reports for legislator/member identity, chamber, currentness, term-boundary, state/district, ZIP mapping, duplicate/conflict, lookup-safety, and Senate-readiness risks.
- Larger-goal alignment: prevent stale, ambiguous, incomplete, or chamber-confused legislator metadata from driving misleading public profiles during future House, Senate, member, or ZIP expansion.

## Outcome

- User-visible or operational result: a repository/local-accessible metadata report command plus Markdown and JSON review packets that identify expansion gates without claiming production coverage truth.

## Scope And Boundaries

- In scope: local fixtures, Congress.gov member caches, Senate XML member metadata, ZIP/district fixtures, backend lookup/search routes, frontend profile/lookup assumptions, ETL/refresh source paths, warnings, focused tests, and generated reports.
- Out of scope: new data ingestion, local or production database mutation, public product behavior changes, vote interpretation semantic changes, ZIP lookup behavior changes, and production coverage assertions.
- Files/systems likely touched: `backend/scripts/generate_legislator_metadata_report.py`, `backend/tests/test_legislator_metadata_report.py`, generated Markdown/JSON reports, and this plan.

## Decision Envelope

- Codex may decide and execute: deterministic local metadata check structure, warning wording, report tables, focused synthetic test cases, and local report generation.
- Explicit approval required for: production credentials, production writes, schema changes, data ingestion, fixture/production-like data repairs, lookup behavior changes, and any methodology or vote-meaning semantic change.

## Definition Of Done

- [ ] Branch created from clean `main` after PR #72.
- [ ] Applicable repo instructions and requested recent docs read.
- [x] Local legislator, member, Senate XML, ZIP, lookup/search, frontend assumption, and ETL paths inspected.
- [x] Read-only metadata report generator implemented.
- [x] Focused backend metadata tests added.
- [x] Markdown and JSON report generated.
- [x] Requested validation commands run and recorded.
- [ ] Diff limited to requested milestone files plus known unrelated untracked artifacts preserved.
- [x] Focused draft PR opened.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/legislator-metadata-hardening-v1` from `main` after PR #72 merge commit `fbc63c6bd0b20ef77094d622a1ba99ef3d1a2d21`.
- Production/deployment state, if relevant: no production write or production credential use authorized.
- Tracked working tree: branch started from updated `main`; status reports permission warnings for existing `.pytest_tmp*` directories.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read instructions, prior audit/manifest docs, plan conventions, and interpretation guardrails.
2. Inspect local metadata sources and lookup assumptions.
3. Implement a stdlib-only local report generator.
4. Add focused pure/local test-case tests for metadata checks.
5. Generate Markdown and JSON review packet outputs.
6. Run requested validations.
7. Stage only milestone files, commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The prior data inventory manifest reports only repository/local-accessible metadata and explicitly does not certify production coverage.
- Local fixture legislators include one House member and two senators, all current, with Bioguide IDs but no persisted slugs and no Senate LIS IDs.
- Congress.gov local member cache currently includes `backend/data_sources/congress/members/118_members.json`.
- Stored app legislator schema has no LIS, persisted slug, or term-boundary fields.
- Senate XML member files include LIS and Bioguide identity locally, but `senate_xml_adapter.py` removes `lis_member_id` before the app-normalized legislator bundle is persisted.
- Backend ZIP lookup assumes one ZIP record and selects one House row by state/district with `ORDER BY id LIMIT 1`; legislator search returns all loaded legislators for an empty query.
- Frontend runs default ZIP `27701`, labels the default profile as sample, and can display supported ZIP coverage from `fixtures`.
- Generated report inspected 2,729 legislator/member rows across local fixtures, source caches, and member XML files.
- Generated report detects local split-ZIP ambiguity for ZIP `27601` across fixture mappings.
- Generated report treats Senate XML `stateRank` as partial seat/rank metadata, not a full Senate class model.

## Decisions And Rationale

- Use a separate legislator metadata report generator rather than expanding the source manifest, because this milestone needs record-level quality/conflict checks and lookup-risk summaries rather than broad inventory counts.
- Keep wording bounded by `docs/interpretation_principles.md`: metadata safety, coverage, and readiness only; no motive, ranking, ideology, prediction, or voting advice.
- Keep the report stdlib-only and file-based so it has no production credential dependency.
- Keep test data synthetic and scoped to `backend/tests/_legislator_metadata_cases`, with automatic cleanup after each test.

## Deviations Or Corrections

- None yet.

## Validation Results

- `python backend\scripts\generate_legislator_metadata_report.py`: passed; wrote Markdown and JSON reports.
- `python -m pytest backend\tests\test_legislator_metadata_report.py -p no:cacheprovider`: passed, 5/5.
- `python -m json.tool docs\review_packets\legislator_metadata_hardening_v1.json`: passed.
- `node --test lib\*.test.mjs` from `frontend`: passed, 75/75. Existing Node warning remains about `frontend/package.json` not declaring `"type": "module"` while module syntax is used.
- `npm run lint` from `frontend`: passed with existing 8 React hook dependency warnings and 0 errors.
- `git diff --check --cached`: passed.
- Staged diff validation includes only:
  - `backend/scripts/generate_legislator_metadata_report.py`
  - `backend/tests/test_legislator_metadata_report.py`
  - `docs/plans/legislator_metadata_hardening_v1.md`
  - `docs/review_packets/legislator_metadata_hardening_v1.json`
  - `docs/review_packets/legislator_metadata_hardening_v1.md`

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the metadata report script, focused tests, generated report outputs, and plan from this branch.

## Blockers

- None currently. Production-backed metadata truth would require future explicit read-only credential authorization and is out of scope.

## Final Reconciliation

- Definition of done satisfied: yes.
- Production writes performed: none.
- Production credentials used: none.
- Commit before final plan reconciliation: `41fbffc`.
- Draft PR: #73.
- Remaining limitations: this is repository/local-accessible metadata only, not production coverage truth. Production-backed metadata truth would require a future explicitly authorized read-only production report.
- Recommended next step: ZIP and district ambiguity hardening, followed by a production read-only metadata companion report before broad House, Senate, member, or national ZIP rollout.
