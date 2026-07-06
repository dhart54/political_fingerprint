# Milestone Plan: ZIP and District Ambiguity Hardening V1

## Intent

- Immediate task: implement read-only local detection, documentation, and tests for the current one-ZIP-one-district assumption and split-ZIP ambiguity risk.
- Larger-goal alignment: prevent national ZIP rollout from incorrectly auto-selecting a House member when a ZIP can span multiple districts or states.

## Outcome

- User-visible or operational result: a repository/local-accessible ZIP ambiguity report command plus Markdown/JSON review packets that define expansion gates before national ZIP lookup rollout.

## Scope And Boundaries

- In scope: local ZIP/district fixtures, local House legislator metadata for match checks, backend lookup/search route assumptions, schema assumptions, frontend ZIP copy assumptions, ETL/import ZIP handling, warnings, tests, generated reports, and draft PR.
- Out of scope: new ZIP data ingestion, local or production database mutation, public lookup behavior changes, frontend behavior changes, fixture output changes outside synthetic tests, address-level resolution, and production-backed coverage assertions.
- Files/systems likely touched: `backend/scripts/generate_zip_district_ambiguity_report.py`, `backend/tests/test_zip_district_ambiguity_report.py`, generated Markdown/JSON reports, and this plan.

## Decision Envelope

- Codex may decide and execute: deterministic local report structure, warning wording, test fixture shape, local code-path inspection checks, and generated Markdown/JSON output.
- Explicit approval required for: production credentials, national ZIP data downloads, schema changes, DB writes, public lookup behavior changes, frontend behavior changes, address-level resolver implementation, or data ingestion.

## Definition Of Done

- [x] Branch created from clean `main` after PR #73.
- [x] Applicable repo instructions and requested recent docs read.
- [x] Backend lookup/search, schema, fixtures, frontend ZIP component/copy, and ETL/import surfaces inspected.
- [x] Read-only ZIP ambiguity report generator implemented.
- [x] Focused backend ambiguity tests added.
- [x] Markdown and JSON reports generated.
- [x] Requested validation commands run and recorded.
- [x] Diff limited to requested milestone files plus known unrelated untracked artifacts preserved.
- [x] Focused draft PR opened.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/zip-district-ambiguity-hardening-v1` from `main` after PR #73 merge commit `172d161a2c65048d56f273cb4f76a3ee514daad0`.
- Production/deployment state, if relevant: no production write or production credential use authorized.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read instructions, recent audit/report docs, plan conventions, and interpretation guardrails.
2. Inspect ZIP lookup, search, schema, fixture, frontend, and ETL assumptions.
3. Implement a stdlib-only local ZIP ambiguity report generator.
4. Add focused deterministic tests using workspace-scoped synthetic test-case directories.
5. Generate Markdown and JSON review packet outputs.
6. Run requested backend, JSON, and frontend validations.
7. Stage only milestone files, commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Prior data inventory and legislator metadata reports are local-only and do not certify production coverage.
- Local ZIP mappings are fixture-only: 9 rows across 4 files and 4 unique ZIPs.
- Local fixtures already expose a deterministic split-ZIP ambiguity: ZIP `27601` appears as both `NC-02` and `NC-04`.
- Database schema stores `zip_district_map.zip` as the primary key, enforcing one stored state/district row per ZIP.
- Backend lookup returns one ZIP record, one House representative selected by state/district, and senators selected by state.
- DB House selection uses `ORDER BY id LIMIT 1`; fallback fixture lookup uses the first matching ZIP and first matching House fixture.
- Frontend ZIP copy states that a ZIP maps to one state-district and auto-opens the returned House profile when present.
- ETL bundle merging deduplicates ZIP mappings by ZIP, preserving one mapping per ZIP when combining source bundles.

## Decisions And Rationale

- Use a separate ZIP ambiguity report generator rather than extending the legislator metadata report, because this milestone is a narrower rollout gate with deterministic ambiguity fixtures.
- Keep the script stdlib-only and file-based, avoiding app DB helpers, production credentials, and network calls.
- Treat local source-cache and fixture findings as expansion-gate evidence only, not production coverage truth.
- Report both row-level findings and code-path assumptions so future behavior changes can be scoped deliberately.

## Deviations Or Corrections

- None yet.

## Validation Results

- `python backend\scripts\generate_zip_district_ambiguity_report.py`: passed; wrote Markdown and JSON review-packet outputs.
- `python -m pytest backend\tests\test_zip_district_ambiguity_report.py -p no:cacheprovider`: passed, 5/5.
- `python -m json.tool docs\review_packets\zip_district_ambiguity_hardening_v1.json`: passed.
- `node --test lib\*.test.mjs` from `frontend`: passed, 75/75. Existing Node warning remains about `frontend/package.json` not declaring `"type": "module"` while module syntax is used.
- `npm run lint` from `frontend`: passed with existing 8 React hook dependency warnings and 0 errors.
- `git diff --check`: passed before staging; milestone files were still untracked at that point.
- `git diff --check --cached`: passed.
- Staged diff validation includes only:
  - `backend/scripts/generate_zip_district_ambiguity_report.py`
  - `backend/tests/test_zip_district_ambiguity_report.py`
  - `docs/plans/zip_district_ambiguity_hardening_v1.md`
  - `docs/review_packets/zip_district_ambiguity_hardening_v1.json`
  - `docs/review_packets/zip_district_ambiguity_hardening_v1.md`

## Production Writes

- Performed: no.
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the ZIP ambiguity report script, focused tests, generated report outputs, and this plan from the branch.

## Blockers

- None currently. Production-backed ZIP truth would require future explicit read-only credential authorization and is out of scope.

## Final Reconciliation

- Definition of done satisfied: yes.
- Production writes performed: none.
- Production credentials used: none.
- Commit before final plan reconciliation: `f536bfb`.
- Draft PR: #74.
- Remaining limitations: this is repository/local-accessible ZIP and district metadata only, not production coverage truth. Address-level resolution and production-backed ZIP coverage remain out of scope.
- Recommended next step: address-level lookup or ambiguity UI design spike, followed by a read-only production ZIP coverage companion report before national ZIP rollout.
