# Milestone Plan: Foushee Justice Full-Record Integration V1

## Intent

- Immediate task: integrate the user-ratified 37-action Justice/Public Safety record, preserve its governed history, and promote a layered benchmark for review.
- Larger-goal alignment: retain fast bounded regression coverage while adding a complete, content-bound reference for full-record editorial and presentation validation.

## Outcome

- User-visible or operational result: a draft integration PR with detached benchmark roles, remote validation, and non-authorizing production-readiness evidence; ordinary public selection remains unchanged.

## Scope And Boundaries

- In scope: current-main reconciliation, benchmark-role governance, offline validation, push, draft PR, CI and preview inspection, review/readiness packets, and an external verified archive.
- Out of scope: merge, production eligibility, production/database access, deployment, publication activation, compact-fixture replacement, and editorial or semantic revision.
- Files/systems likely touched: benchmark records and validation, focused backend tests/CI, plans and review packets, GitHub draft PR, and automatic preview checks.

## Decision Envelope

- Codex may decide and execute: detached benchmark-role representation, mechanical mainline reconciliation, CI portability corrections, review-only readiness evidence, push, and draft PR creation.
- Explicit approval required for: merge, production eligibility, deployment, publication activation, or any change to ratified semantics, wording, mappings, risks, calibration, screenshots, or authority records.

## Definition Of Done

- [x] Exact M7 starting identity, authority chain, ratification, and offline verifier chain proven.
- [x] Compact seven-action benchmark preserved and full record promoted as `full_record_reference`.
- [x] Local release validation recorded.
- [ ] Draft PR and remote checks/previews recorded.
- [ ] Production-readiness and integration-review packets completed without granting eligibility.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/foushee-justice-full-record-integration-v1` created at `55f9e201afea051556f436e83e7e9e16ad3cb99b`; latest `origin/main` is `24a2bcb37347f74c6c40261930024e85676cd8d0` and is already an ancestor.
- Production/deployment state, if relevant: not queried; no production service or database access is authorized.
- Tracked working tree: clean before M8 implementation.
- Known unrelated untracked artifacts: `docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1.zip`; preserve without reading, staging, deletion, or packaging.

## Implementation Sequence

1. Verify M1-M7 locally, create the integration branch, fetch main, and merge normally.
2. Add and validate the detached layered benchmark-role record while preserving governed bytes and selector isolation.
3. Run the broadest safe offline validation, inspect the diff, commit, push, and open a draft PR.
4. Inspect CI and automatic preview behavior; use no more than two bounded integration correction cycles.
5. After remote success, add non-authorizing readiness and review evidence, repush, revalidate, and package the final review archive.

## Progress Checklist

- [x] Discovery
- [x] Benchmark implementation
- [x] Full local validation
- [ ] Documentation and readiness evidence
- [ ] Commit/PR readiness

## Discoveries

- Freshly fetched `origin/main` did not advance from the cached base, so the required normal merge was a no-op with no conflicts.
- The persistence benchmark axis supports only `not_promoted` and `gold_benchmark`; a detached role record truthfully distinguishes the compact and full-record purposes without changing immutable candidate controls.
- The corrected M5-R1 graph lives under the V2 Semantic IR implementation root and has four repeated patterns; the V1 graph is historical pre-correction evidence.

## Decisions And Rationale

- Preserve the existing presentation fixture's `gold_benchmark` state and add a second detached `gold_benchmark` role named `full_record_reference` rather than changing the runtime candidate or registry.
- Compare the full graph by normalized semantic identity excluding authoring-era proposition IDs; relationships resolve to the normalized identity of their targets.
- Treat screenshot hashes as governed launch-review evidence only, never as a cross-product pixel doctrine.

## Deviations Or Corrections

- An attempted `--help` probe exposed that the M6 finalizer has no help-safe CLI and executed once, changing only its parity manifest. The change was caught immediately and restored byte-for-byte to the reviewed M7 blob before any branch or fetch operation.
- The first targeted pytest attempts hit Windows sandbox permissions in pytest's temp root (187 tests had passed before 26 setup errors). The identical suite passed 213/213 with an explicit elevated isolated temp base.
- The first benchmark validator draft pointed to historical M5 V1 graph bytes; the failed four-pattern invariant identified the error, and the binding was corrected to the accepted M5-R1 V2 graph without changing any governed artifact.
- The release pipeline's optional persistence stage used `unittest` for a pytest-style module and therefore either failed import or collected zero tests. Correction cycle 1 adds the backend child import path and invokes that stage through pytest; a focused command-construction regression test was added.

## Validation Results

- M1-M7 deterministic validators and check-mode builders: passed.
- Targeted M1-M7 backend suite: 213 passed after the documented temp-root workaround.
- Layered benchmark validator: passed; focused adversarial suite: 7 passed.
- Editorial release pipeline: 9/9 checks passed, including accepted and held-out Semantic IR references, persistence, governance, and the production frontend build.
- Frontend unit suite: 110 passed; lint: zero errors and eight pre-existing hook-dependency warnings.
- Broad offline backend suite: 1,245 passed and 33 skipped; 17 baseline/environment failures remain outside M8 (missing local House/Senate source caches, one pre-existing ZIP-manifest byte mismatch, two API selector test assumptions, and dependent Senate source tests). The initial collection also required `--import-mode=importlib` to avoid stale external-worktree module collisions.
- Directly affected combined suite: 323 passed with two pre-existing API selector failures; the M1-M7 suite independently passed 213/213 and the M8 benchmark suite passed 7/7.
- Remote CI, preview, and final packaging results: pending.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert only the M8 benchmark, validator/test/CI, plan, and review/readiness commits; governed M1-M7 commits and the compact fixture remain unchanged.

## Blockers

- None at the benchmark implementation stage.

## Final Reconciliation

- Definition of done satisfied: pending remote and readiness stages.
- Remaining limitations: production eligibility, merge, deployment, and publication decisions remain explicitly deferred.
- Recommended next step: complete local validation, open the draft PR, and inspect remote checks before preparing eligibility evidence.
