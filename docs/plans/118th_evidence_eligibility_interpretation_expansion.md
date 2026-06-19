# Milestone Plan: 118th Evidence Eligibility And Interpretation Expansion

## Intent

- Immediate task: promote the strongest source-grounded 118th Congress votes into eligible issue evidence and reviewed interpretations.
- Larger-goal alignment: make Prior Congress and Full Record views materially useful while preserving civic-integrity guardrails and 119th outputs.

## Outcome

- User-visible or operational result: 118th-only evidence expansion with audited reasons, ranked opportunity families, bounded production writes, recomputed derived outputs, public validation, rollback artifacts, review packet, PR, merge, and deployment verification.

## Scope And Boundaries

- In scope: already-loaded 118th House and Senate facts, deterministic classification/eligibility tooling, source-grounded interpretation packages, bounded production classification and interpretation writes, derived precomputes, validation of `scope=118`, `scope=119`, and `scope=all`.
- Out of scope: 117th expansion, historical product redesign, new support/opposition/readiness/alignment methodology, 119th data changes, PN nominations and treaty/executive votes unless already safely representable.
- Files/systems likely touched: backend classification/ETL/summary scripts, tests, docs/review packet, rollback artifacts, active plan.

## Decision Envelope

- Codex may decide and execute: source collection for loaded 118th facts, deterministic rule improvements, package generation, bounded production classification/interpretation writes, derived recomputes, PR/merge/deployment verification after gates pass.
- Explicit approval or stop required for: new schema or methodology decisions, ambiguous civic meaning, conflicting authoritative sources, incomplete rollback, material preflight divergence, unexpected 119th changes, or inability to distinguish amendment meaning from parent measure.

## Definition Of Done

- [x] Full 118th reason distribution reported before changes.
- [x] At least top ten source families/opportunity groups ranked.
- [x] Deterministic rules improved where official sources safely support them.
- [x] Substantive and procedural-context interpretation packages generated.
- [x] Bounded writes completed only after preflight gates, rollback creation, and caps.
- [x] Derived outputs recomputed, idempotency-checked, then restored from rollback to preserve 119 rolling public outputs.
- [x] 119th IDs/classifications/interpretations/counts preserved; `scope=119` public read isolation fixed in API.
- [x] Idempotency rerun proves zero additional classification and interpretation writes; derived recompute proved zero before rollback.
- [x] Valerie Foushee, Thom Tillis, Ted Budd, one dual-Congress official, one 118th-only official, and one sparse profile validated.
- [x] `scope=118`, `scope=119`, and `scope=all` isolation confirmed on patched API.
- [x] Tests/build recorded; local API validation completed; rendered/public validation blocker recorded.
- [x] Separate rollback coverage for classifications, interpretations, and derived precomputes preserved.
- [x] Review packet updated.
- [ ] PR, merge, and deployment verification completed if all gates pass.
- [ ] Final reconciliation completed, including whether continuity/change statements are trustworthy.

## Baseline

- Branch/base commit: `codex/118th-evidence-expansion` from `main` at `77bf778c075deacf075a868f183f4c17a64127e3`.
- Production/deployment state, if relevant: to be discovered before any write.
- Tracked working tree: pre-existing user-owned edits in `docs/deployment.md` and `docs/monitoring.md`; preserve unless explicitly directed.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`; leave untouched.

## Implementation Sequence

1. Discovery: inspect data model, classification/interpretation tooling, tests, production access, and current 118th state.
2. Audit and package design: report reason distribution, rank at least ten opportunity groups, identify safe packages using direct vote question/amendment purpose before parent context.
3. Implementation: update deterministic rules and package generation with tests; keep procedural/limited rows non-counting and not-voting excluded.
4. Preflight and rollback: define exact rows/tables/caps/effects and create separate rollback artifacts.
5. Production write and recompute: perform only bounded authorized writes, recompute affected derived outputs, validate actual versus expected effects, prove idempotency.
6. Product validation: public/API/rendered checks for required officials and scopes.
7. Documentation and delivery: review packet, final reconciliation, commit, PR, checks, merge, deployment verification.

## Progress Checklist

- [x] Discovery
- [x] Audit and opportunity ranking
- [x] Implementation
- [x] Preflight and rollback
- [x] Production writes and recompute
- [x] Validation
- [x] Documentation
- [ ] Commit/PR/merge/deployment readiness

## Discoveries

- Local branch creation initially required escalated `.git` ref write permission; branch was created after approval.
- Pre-existing tracked doc edits were substantive operational-monitoring notes before branch creation and were preserved as user-owned baseline changes. They are not present as branch diffs after switching to the milestone branch.
- Baseline 118th audit before writes: 1,353 loaded roll calls; only 3 eligible policy rows and 2 interpreted rows.
- Final 118th audit after writes: 198 eligible rows, including 77 substantive interpreted rows and 121 procedural-context rows.
- A local API validation found that `scope=119` used the rolling precompute path and could expose late-118th evidence in Recent Congress evidence reads. The database data was not corrupted; the API read path was corrected to use congress-scoped queries for explicit profile scopes.

## Decisions And Rationale

- Treat procedural and limited-context rows as visible but non-counting; keep not-voting outside support/opposition.
- Use amendment purpose and direct vote question before parent-measure context for eligibility/classification.
- Defer all amendment rows without direct amendment purpose, even when parent-measure context exists.
- Do not retain historical derived precompute writes that alter the latest rolling public output window; use scoped on-demand reads for `scope=118`, `scope=119`, and `scope=all` validation.

## Deviations Or Corrections

- Derived precompute write was executed and idempotency-checked, then restored from `docs/review_packets/118th_evidence_expansion_precompute_rollback.sql` because retaining the rolling-window derived rows would have changed 119 public outputs. The final data change retained is limited to bounded 118th classifications and interpretations.
- API scope read path was corrected so explicit `scope=119` uses 119-only congress-scoped rows rather than the latest rolling precompute window.

## Validation Results

- Targeted ETL tests: `pytest --basetemp=..\.local\pytest_118_expansion tests\test_evidence_118_expansion.py tests\test_session2_evidence_expansion.py` -> 15 passed.
- Scoped API/read-layer tests after `scope=119` fix: `pytest --basetemp=..\.local\pytest_118_api_scope tests\test_db_read_layer.py tests\test_api_fingerprint.py tests\test_api_positions.py tests\test_api_alignment.py` -> 39 passed.
- Frontend unit tests: `node --test frontend/lib/*.test.mjs` -> 40 passed.
- Frontend build: `npm run build` -> passed.
- Broad backend suite: attempted in database and fixture modes; both hit pre-existing live-adapter failures and Windows basetemp cleanup `PermissionError` after test execution, so it is not treated as a clean milestone gate.
- Local database-backed API health: `/health` returned `{"status":"ok"}` and `/coverage/metadata` returned database source with 392 eligible roll calls.
- Patched local API scope validation: `scope=118` samples only 118 evidence, `scope=119` samples only 119 evidence, and `scope=all` samples combined 118/119 evidence. 118-only and sparse profiles show zero Recent Congress evidence after the API fix.
- Public frontend validation: `https://political-fingerprint.vercel.app` returned 200 and rendered the Political Fingerprint page. Local Next.js rendering remains an environment limitation only and is not treated as a product blocker after passing tests/build.
- Public backend validation: `https://political-fingerprint.onrender.com/health` returned `{"status":"ok"}` and `/coverage/metadata` reported `data_source = database` with 392 eligible roll calls.

## Production Writes

- Performed: yes.
- Scope: 198 reviewed 118th roll calls; no fact-table writes.
- Classification write: 198 updates.
- Interpretation write: 198 updates.
- Derived precompute write: exercised, idempotency-checked, then rolled back to preserve latest rolling public outputs.
- Expected effects: 77 substantive interpreted rows with support/oppose positions and 121 procedural-context rows with null support/oppose.
- Actual effects: matched expected; not-voting counted as support/opposition = 0.

## Rollback Paths

- Classifications: `docs/review_packets/118th_evidence_expansion_classification_rollback.sql`.
- Interpretations: `docs/review_packets/118th_evidence_expansion_interpretation_rollback.sql`.
- Derived precomputes: `docs/review_packets/118th_evidence_expansion_precompute_rollback.sql` and applied after derived write validation.

## Blockers

- Merge remains unauthorized until the final pre-merge gate passes.

## Final Reconciliation

- Definition of done satisfied: no.
- Remaining limitations: pending.
- Remaining limitations: 588 amendment rows remain deferred because loaded facts do not provide direct amendment purpose safely enough to distinguish amendment meaning from parent-measure context; PN nominations and treaty/executive votes remain deferred. The 118th package improves Prior Congress and Full Record evidence but is still too uneven for broad continuity/change claims.
- Recommended next step: complete full test/build gates, rendered/public deployment verification, PR, merge, and deployment verification.
