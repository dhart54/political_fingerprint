# Milestone Plan: Data Inventory / Source Manifest V1

## Intent

- Immediate task: implement a read-only local manifest that reports which repository-accessible data sources, fixtures, metadata, vote rows, source URLs, interpretation artifacts, and derived outputs exist.
- Larger-goal alignment: create the first expansion gate before broad House, Senate, member, or multi-Congress rollout work.

## Outcome

- User-visible or operational result: a generator command plus Markdown/JSON review packet that makes local coverage and gaps explicit without claiming production coverage.

## Scope And Boundaries

- In scope: local source-cache inventory, fixture inventory, legislator metadata inventory, ZIP/district inventory, vote row inventory, source URL coverage, interpretation coverage, derived artifact inventory, warnings, tests, generated review packet, and draft PR.
- Out of scope: data ingestion, production writes, local DB mutation, vote interpretation semantic changes, frontend product behavior changes, and production-backed coverage assertions.
- Files/systems likely touched: `backend/scripts/generate_data_inventory_manifest.py`, focused backend tests, generated `docs/review_packets/data_inventory_source_manifest_v1.md`, generated JSON, and this plan.

## Decision Envelope

- Codex may decide and execute: local file paths to inspect, report shape, warning wording, deterministic counting helpers, focused tests, and generated Markdown/JSON output.
- Explicit approval required for: production credentials, production writes, schema changes, ETL refactors, data ingestion, or interpretation/counting semantics changes.

## Definition Of Done

- [x] Branch created from clean `main` after PR #71.
- [x] Applicable repo instructions and requested recent docs read.
- [x] Backend/frontend/ETL/source-cache paths inspected for the requested inventory categories.
- [x] Read-only manifest generator implemented.
- [x] Focused tests added for parsing/warning behavior.
- [x] Markdown and JSON manifest generated.
- [x] Validation command and targeted tests run.
- [x] Diff limited to requested milestone files.
- [x] Focused draft PR opened.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/data-inventory-source-manifest-v1` from `main` after PR #71 merge commit `56c463b8b696589142eb2601e9f61e72a1d752a0`.
- Production/deployment state, if relevant: no production write or production credential use authorized.
- Tracked working tree at branch start: clean apart from known unrelated untracked artifacts.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read instructions, audit docs, plan conventions, and interpretation guardrails.
2. Inspect source cache, fixture, schema/read-layer, ETL, frontend fixture, interpretation batch, and derived artifact layouts.
3. Implement a stdlib-only local manifest generator under `backend/scripts`.
4. Add focused backend tests for missing directories, deterministic fixture counts, warning generation, and no production credential dependency.
5. Generate Markdown and JSON review packet outputs.
6. Run requested and relevant validations.
7. Stage only milestone files, commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Generation
- [x] Validation
- [x] Commit/PR readiness

## Discoveries

- `backend/scripts` did not exist before this milestone, so the manifest command creates that directory.
- Local House Clerk cache directories present: `2023`, `2024`, and `2026`; `2025` is absent.
- Local Senate XML session directories present: `118_1`, `118_2`, and `119_2`; `119_1` is absent.
- Fixture fallback data remains intentionally tiny and should not be confused with production coverage.
- Record Across and comparable-family artifacts remain House-only.
- Generated manifest reports 14 fixture roll-call rows, 21 fixture member vote rows, 1,291 inspected local source URL rows, and 922 interpretation-like rows.
- Generated manifest detects local split-ZIP ambiguity in fixture files for ZIP `27601`, which appears with both `NC-02` and `NC-04` across fixture sets.

## Decisions And Rationale

- Use a repository/local manifest only and state that it is not production truth, because no production credentials are authorized.
- Keep the generator stdlib-only and avoid importing app DB helpers, so it remains safe and credential-independent.
- Save JSON as well as Markdown because the manifest is an expansion gate and future milestones can diff or inspect machine-readable counts.
- Count local fixture/example URLs as non-official source URLs rather than suppressing them, because fixture fallback should remain visibly separate from production-quality receipt coverage.

## Deviations Or Corrections

- None yet.

## Validation Results

- `python backend\scripts\generate_data_inventory_manifest.py`: passed; wrote Markdown and JSON review-packet outputs.
- `python -m pytest backend\tests\test_data_inventory_manifest.py`: initial run failed before test execution because pytest could not access its default `AppData\Local\Temp\pytest-of-Dylan` base directory in the managed sandbox.
- `python -m pytest backend\tests\test_data_inventory_manifest.py --basetemp=.pytest_tmp_data_inventory`: also failed at pytest session cleanup due permissions on the pytest-created basetemp directory.
- Correction: tests were changed to avoid pytest temp fixtures and use scoped workspace test-case directories.
- `python -m pytest backend\tests\test_data_inventory_manifest.py -p no:cacheprovider`: passed, 4/4.
- `node --test lib\*.test.mjs` from `frontend`: passed, 75/75. Existing Node warning remains about `frontend/package.json` not declaring `"type": "module"` while `frontend/lib/issueDomains.js` uses module syntax.
- `npm run lint` from `frontend`: passed with the existing 8 React hook dependency warnings and 0 errors.
- `python -m json.tool docs\review_packets\data_inventory_source_manifest_v1.json`: passed.
- ASCII check for script, tests, plan, Markdown report, and JSON report: passed.
- `git diff --name-only`: empty before staging because all milestone files were new/untracked. `git status --short --branch` showed only intended milestone files plus known unrelated untracked artifacts.
- Staged diff validation included only:
  - `backend/scripts/generate_data_inventory_manifest.py`
  - `backend/tests/test_data_inventory_manifest.py`
  - `docs/plans/data_inventory_source_manifest_v1.md`
  - `docs/review_packets/data_inventory_source_manifest_v1.json`
  - `docs/review_packets/data_inventory_source_manifest_v1.md`

## Production Writes

- Performed: no.
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the manifest script, tests, generated review packet, generated JSON, and plan from this branch.

## Blockers

- None currently. Production-backed counts would require explicit read-only credentials and are out of scope for this milestone.

## Final Reconciliation

- Definition of done satisfied: yes.
- Production writes performed: none.
- Production credentials used: none.
- Commit: `7fb3e0f` before final plan reconciliation; branch head contains this final reconciliation amendment.
- Draft PR: #72.
- Remaining limitations: manifest is repository/local-accessible coverage only. It does not certify production row counts or production source coverage.
- Recommended next step: Legislator metadata hardening before House pilot expansion, Senate public reads, or national ZIP rollout.
