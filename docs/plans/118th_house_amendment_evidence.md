# Milestone Plan: 118th House Amendment Evidence

## Intent

- Immediate task: Promote safely grounded 118th House amendment roll calls from deferred status into substantive historical evidence through the canonical amendment evidence path.
- Larger-goal alignment: Improve Prior Congress and Full Record value while preserving trust boundaries needed for future continuity/change analysis.

## Outcome

- User-visible or operational result: Source-grounded 118th House amendment evidence, bounded production writes, recomputed affected outputs, and verified public `scope=118`, `scope=119`, and `scope=all` behavior.

## Scope And Boundaries

- In scope: 118th Congress House amendment rows already loaded in production; official Congress.gov amendment/source records; deterministic matching, classification, interpretation packages, rollback, bounded writes, recomputation, validation, review packet, PR, merge, and deployment verification.
- Out of scope: Senate rework, new Congress expansion, continuity/change product summaries, support/opposition/readiness/alignment methodology changes, inferred amendment meaning from parent bills alone, and changes to 119th or non-targeted 118th evidence.
- Files/systems touched: `docs/review_packets/`, `docs/interpretation_batches/`, `docs/plans/`, production classification/interpretation rows for the exact 228 target roll calls, and affected derived-output tables.

## Decision Envelope

- Codex may decide and execute: source caching, shared matching and eligibility use, structured family manifests, interpretation packages, bounded production writes, affected-output recomputation, reconciliation, rollback validation, idempotency checks, PR/merge/deployment verification when all gates pass.
- Explicit approval required for: schema or methodology changes, destructive or unbounded writes, ambiguous civic semantics, service/secrets/config changes, or permanent code that cannot be justified as reusable.

## Definition Of Done

- [x] Audit all 566 deferred House amendment rolls and record defer-reason distribution.
- [x] Group and rank at least the top ten opportunity families before any production write.
- [x] Retrieve direct amendment identity, sponsor, purpose, text/actions, and vote question from official sources for target rows.
- [x] Preserve amendment-to-amendment, en-bloc, parent-measure, chamber, Congress, and session relationships.
- [x] Generate substantial source-grounded classification and interpretation packages.
- [x] Preserve procedural, limited, and not-voting non-counting boundaries.
- [x] Complete pre-write review artifact with exact write set, effects, rollback preview, scope isolation, and production preflight.
- [x] Perform bounded production writes only after all gates pass.
- [x] Recompute only affected derived outputs and reconcile expected versus actual effects.
- [x] Prove idempotency and no 119th or non-targeted 118th changes.
- [x] Validate required representative officials and public `scope=118`, `scope=119`, and `scope=all`.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [ ] PR, merge, and deployment verification completed.
- [x] Final reconciliation completed, including whether evidence is sufficient for future continuity/change summaries.

## Baseline

- Branch/base commit: `codex/118th-house-amendment-evidence` from `5038049c760bd40bbe171143deaa6dd0ff73cc2c`.
- Production/deployment state: production had 566 deferred 118th House amendment rows before this milestone.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read existing canonical amendment code, prior 118th/Senate runbooks, production access patterns, and schema contracts.
2. Run read-only production audit for 566 deferred 118th House amendment rows and defer reasons.
3. Group/rank opportunity families and select sourceable high-value targets with exact inclusion/exclusion boundaries.
4. Fetch/cache official Congress.gov amendment records using existing source tooling.
5. Build pre-write review packet, target manifest, rollback previews, and preflight comparisons.
6. Execute bounded writes only after gates pass, then recompute affected outputs.
7. Validate effects, idempotency, isolation, public scopes, representative officials, tests, CI, PR, merge, and deployment.

## Progress Checklist

- [x] Baseline confirmed
- [x] Active branch created
- [x] Active plan created
- [x] Read-only production audit
- [x] Top-ten family ranking
- [x] Source collection
- [x] Implementation
- [x] Production writes
- [x] Public validation
- [x] Tests
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- `docs/amendment_evidence_pipeline.md` identifies `backend/app/etl/amendment_evidence.py` as the canonical reusable runtime and recommends no new House milestone-specific ETL module by default.
- Read-only production audit found exactly 566 118th House amendment roll calls: 558 `defer_amendment_needs_direct_purpose` rows and 8 `procedural_vote_non_counting` rows.
- The 566 rows span 71 parent-bill families. After official Congress.gov source collection, 380 rows had matched direct source material and 186 remained limited.
- Of the 380 matched rows, 239 initially mapped to existing safe policy domains. Supervised validation identified 11 procedural-signal rows, so those rows were excluded from the write set.
- Final bounded write set: 228 source-grounded substantive House amendment roll calls. The remaining 338 audited rows stay deferred/limited or procedural.
- Top opportunity families after source collection were `118:hr:4665` with 37 matched rows, `118:hr:4394` with 28, `118:hr:8771` with 26, `118:hr:8070` with 24, and `118:hr:4368` with 23.

## Decisions And Rationale

- Use the canonical amendment evidence path and structured artifacts; no permanent runtime code was needed.
- Treat direct amendment source coverage and supervised/manual validation as hard gates before production writes.
- Exclude the 11 procedural-signal rows rather than overriding the validator.
- Leave parent-context-only and no-safe-domain rows limited because parent-measure context cannot replace a narrower amendment meaning.
- Recompute affected historical outputs after writes, using a rollback file captured before recompute.

## Deviations Or Corrections

- The first bounded write precondition counted member-level vote-context rows rather than distinct target roll calls, so it failed before any write. The temporary runner was corrected to validate distinct roll-call IDs and rerun successfully.
- No milestone-specific temporary scripts were retained.

## Validation Results

- Source audit: `docs/review_packets/118th_house_amendment_evidence_prewrite_audit.json`.
- Initial blocked packet: `docs/review_packets/118th_house_amendment_evidence_blocked_prewrite_review.md`.
- Candidate batch: `docs/interpretation_batches/118th_house_amendment_substantive_candidates.json`.
- Pre-write review: `docs/review_packets/118th_house_amendment_evidence_prewrite_review.md` and `.json`.
- Supervised validation passed for the final 228-row batch: 228 substantive, 0 procedural, 0 insufficient, no errors or warnings.
- Manual interpretation validation passed: 228 valid records, no errors.
- Post-write validation passed: 228 target rows eligible, interpreted, reviewed, and policy-vote classified; 0 out-of-scope rows; 0 not-voting records counted as support/opposition.
- Idempotency check passed: classification diffs `[]`, interpretation diffs `[]`, `idempotent: true`.
- Public backend validation passed against `https://political-fingerprint.onrender.com`: health `ok`, metadata `eligible_roll_call_count: 627`, `window_end: 2026-06-19`, and scoped representative checks returned expected 118th/119th/all separation.
- Rendered frontend validation passed against `https://political-fingerprint.vercel.app/`: page loaded with `627 ROLL CALLS`; Full Record, Recent Congress, and Prior Congress controls changed active state and scope helper text.
- Targeted backend tests passed: `python -m pytest tests\test_amendment_evidence.py tests\test_source_packets.py tests\test_amendment_companion_enrichment.py tests\test_supervised_enrichment.py` plus five non-temp manual-interpretation tests; 29 passed.
- Test limitation: `tests\test_manual_interpretations.py::test_import_manual_interpretations_validates_before_persisting` could not complete in this Windows session because pytest raised `PermissionError: [WinError 5] Access is denied` while accessing its generated basetemp directory. The failure occurred at pytest temp-fixture/session cleanup, not in milestone production validation.

## Production Writes

- Performed: yes.
- Classification updates: 228 exact target roll calls.
- Interpretation updates: 228 exact target roll calls.
- Preflight before write: 228 target rows, 0 out-of-scope rows, 0 currently counting rows, 228 currently ineligible/insufficient rows.
- Expected member vote instances from prewrite review: 42,481 support, 53,861 opposition, and 3,510 not-voting excluded.
- Actual post-write vote positions: 42,481 `yea`, 53,861 `nay`, 21 `present`, and 3,510 `not_voting`; not-voting counted as support/opposition: 0.
- Affected output recompute updated or inserted 4,833 fingerprints, 42 chamber medians, 612 drift scores, and 540 summaries for the `2026-06-19` precompute window.

## Rollback Paths

- Classification rollback: `docs/review_packets/118th_house_amendment_classification_rollback.sql`.
- Interpretation rollback: `docs/review_packets/118th_house_amendment_interpretation_rollback.sql`.
- Precompute rollback: `docs/review_packets/118th_house_amendment_precompute_rollback.sql`.

## Blockers

- None currently. Remaining work is test execution, commit/PR, and final remote workflow if checks permit.

## Final Reconciliation

- Definition of done satisfied: not yet, pending tests and PR workflow.
- Evidence sufficiency: sufficient to improve Prior Congress and Full Record profile coverage for the 228 target amendment rows. Not sufficient by itself to launch trustworthy continuity/change summaries, because 338 audited 118th House amendment rows remain limited/procedural and continuity/change still needs a separate product and methodology decision.
- Remaining limitations: no schema or methodology changes were made; no new continuity/change summary semantics were introduced; limited rows remain non-counting.
