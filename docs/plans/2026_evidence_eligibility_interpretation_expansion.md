# Milestone Plan: 2026 Evidence Eligibility And Interpretation Expansion

## Intent

- Immediate task: promote the strongest source-grounded 119th Congress session 2 / 2026 House and Senate rows from conservative placeholders into useful issue evidence and interpretations.
- Larger-goal alignment: keep current profiles useful without weakening civic evidence standards or collapsing procedural/amendment/final-passage distinctions.

## Outcome

- The 282 ineligible 2026 rows are audited and grouped by source family.
- Safe deterministic classification improvements are implemented.
- Bounded classification and interpretation writes are applied only after preflight, rollback, and validation gates pass.
- Derived outputs are recomputed so public profiles show the new eligible 2026 evidence.

## Scope And Boundaries

- In scope: 119th Congress, session 2 / 2026, already-loaded House and Senate facts.
- Out of scope: prior-Congress expansion, broad new fact ingestion, unsupported PN/treaty/executive semantics, support/opposition/readiness/alignment methodology changes.
- PN nominations and treaty/executive votes remain deferred unless existing semantics already support them.

## Decision Envelope

- Codex may improve deterministic classifiers, create source packets, generate bounded batches, write classifications/interpretations, refresh derived outputs, and validate/deploy when established gates pass.
- Target a meaningful package without weakening evidence standards.
- Continue independently safe vote families if another family fails.
- Stop for ambiguous civic meaning, conflicting authoritative sources, new schema/product semantics, incomplete rollback, or material preflight divergence.

## Definition Of Done

- [ ] Audit all 282 session-2 classifications and record the exact ineligibility reason distribution.
- [ ] Rank at least the top 10 source families/opportunity groups.
- [ ] Improve deterministic eligibility/classification rules where existing source data safely supports it.
- [ ] Preserve amendment, final-passage, procedural, nomination, treaty, limited-context, and not-voting distinctions.
- [ ] Generate meaningful substantive/procedural-context interpretation packages.
- [ ] Create rollback artifacts before each production write.
- [ ] Apply bounded writes when gates pass.
- [ ] Recompute derived outputs and prove idempotency.
- [ ] Reconcile expected vs actual support/opposition, readiness, alignment, and not-voting effects.
- [ ] Verify public API/UI for representative House and Senate profiles.
- [ ] Tests, review packet, PR, merge, and deployment verification complete.

## Baseline

- Base branch: `main`.
- Base commit: `116d984f9d9f8c23ff8fa2840db682e288cfa237`.
- Branch: `codex/2026-evidence-eligibility-expansion`.
- Known unrelated untracked artifacts preserved: chamber filtering audit, frontend grounding bundle, pytest temp directories.

## Implementation Sequence

1. Production read-only audit of the 282 session-2 rows.
2. Source-family grouping and opportunity ranking.
3. Inspect classifier/interpreter behavior against current source fields.
4. Implement safe deterministic classification improvements.
5. Generate candidate interpretation packages.
6. Dry-run, rollback, bounded production writes.
7. Recompute derived outputs and validate idempotency.
8. Public API/UI verification.
9. Review packet, tests, PR, merge, deployment verification.

## Progress Checklist

- [x] Base confirmed and branch created.
- [x] Production audit.
- [x] Opportunity ranking.
- [x] Implementation.
- [x] Preflight and rollback.
- [x] Production writes and post-validation.
- [x] Derived output refresh.
- [ ] Tests and deployment validation.

## Discoveries

- Production has 282 119th Congress session-2 rows currently ineligible for issue evidence.
- Exact reason distribution: `house:low_classification_confidence` 138, `house:procedural_vote` 78, `senate:procedural_vote` 42, `senate:low_classification_confidence` 24.
- Candidate dry-run after conservative filtering selects 64 rows: 32 substantive interpretations and 32 non-counting procedural-context rows.
- Deferred rows: 143 broad/low-value procedural, 33 amendments needing purpose, 39 no-domain-signal rows, and 3 context-mismatch rows.
- One House appropriations row carried Senate cloture/proceeding title context through the loaded bill join; this and two similar mismatches are deferred rather than interpreted.

## Decisions And Rationale

- Use direct official roll-call question and loaded measure text only; do not use parent-measure context to infer amendment purpose.
- Keep amendments deferred when purpose/context is unavailable in the loaded facts.
- Promote direct final-passage/appropriations/resolution votes only when a single issue-domain signal is dominant.
- Promote focused procedural rows only as non-counting context with null support/opposition positions.
- Defer broad multi-bill rules and cross-chamber context mismatches.

## Deviations Or Corrections

- Added an explicit context-mismatch guard after candidate review found House rows with Senate cloture/proceeding bill titles.

## Validation Results

- `backend/tests/test_session2_evidence_expansion.py`: 7 passed.
- Compact dry-run: 64 target rows, 32 substantive, 32 procedural-context, 0 planned classification support/opposition inference.
- Production target validation: 64 eligible classifications, 32 interpreted rows, 32 procedural/non-counting rows.
- Interpretation impact: vote_interpretations support/oppose non-null rows increased from 97 to 129 (+32); target substantive vote rows include 7,769 support votes, 5,734 oppose votes, and 745 not-voting rows excluded.
- Derived refresh: 4,280 fingerprints, 42 chamber medians, 535 drift scores, and 535 summaries updated or inserted for the 2026-06-17 window.
- Idempotency: classification rerun updated 0 rows; interpretation rerun updated 0 rows; precompute rerun updated/inserted 0 rows.
- Local production-backed API returns the refreshed 2026-06-17 window for Valerie Foushee, Thom Tillis, Ted Budd, Adam Schiff, and sparse profile `leg_grijalva`.
- Public Render API currently returns the older 2026-03-12 window and needs deployment verification after PR merge.

## Production Writes

- Classification update: 64 existing `vote_classifications` rows updated.
- Interpretation update: 64 existing `vote_interpretations` rows updated.
- Derived output refresh: `fingerprints`, `chamber_medians`, `drift_scores`, and `summaries` updated for the 2026-06-17 v1 window.

## Rollback Paths

- `docs/review_packets/session2_evidence_expansion_rollback.sql`
- `docs/review_packets/session2_evidence_expansion_precompute_rollback.sql`

## Blockers

- None currently.

## Final Reconciliation

- Pending.
