# Milestone Plan: Selected Issue Experience V1

## Intent

- Immediate task: Recompose the selected-issue experience into a scan-first governed-record explanation followed by a compact, complete, progressively disclosed action ledger.
- Larger-goal alignment: Make the voter route easier to understand while preserving exact action accounting, semantic boundaries, and official-source access.

## Outcome

- User-visible result: Distinct evidence and interpretation scopes, a compact reviewed-record summary and pattern index, collapsed limitations, a compact/grouped ledger, and voter-facing expanded receipts.

## Scope And Boundaries

- In scope: reusable selected-issue React composition, frontend selectors, focused fixtures/tests, accessibility and responsive behavior, deterministic review captures, one branch, and one draft PR.
- Out of scope: backend/editorial wording changes, artifact 221, publication registry, action/proposition/episode identity or membership changes, production writes, merge, deployment, and representative imagery.
- Likely touch set: 12-22 frontend source/test files, this plan, and an isolated non-governed review packet.

## Decision Envelope

- Codex may decide component boundaries, presentation-only extraction, grouping UI, focus behavior, responsive styling, tests, and review-packet mechanics.
- Stop for governed-content conflict, an unresolvable API-contract blocker, production/publication mutation, merge, or deployment.

## Definition Of Done

- [x] Evidence scope and governed interpretation scope remain visibly and programmatically distinct.
- [x] Governed takeaway, patterns, counts, mixed trajectory, and limitations render without React inventing analysis.
- [x] Every action remains independently identifiable, filterable, focusable, expandable, and source-linked; optional grouping never aggregates positions.
- [x] Public receipt metadata is simplified while internal governance records remain unchanged.
- [x] Responsive, keyboard, focus, disclosure, reduced-motion, zoom, leakage, build, and contract validation pass.
- [x] Deterministic after-state packet and manifest are produced outside governed product content.
- [x] Final diff is bounded, committed, pushed, and opened as one draft PR.
- [x] PR #131 correction removes ordinary row-status theater, receipt duplication, meta takeaway copy, proportional pattern bars, generic title fallbacks, and overbroad governed-caveat filtering.
- [x] The correction implementation is locally validated and prepared as one bounded commit; post-commit push, CI, and exact-commit live-preview capture are reported outside this commit-boundary plan.

## Baseline

- Branch/base: `codex/selected-issue-experience-v1` from exact `ce2d1b4e09c329cbe4490aa25f85b9970bd3428a`.
- Before-state authority: production selected-issue route plus the approved baseline review named by the user.
- Accepted continuation state: public-receipt simplification already implemented and validated in this worktree.
- Unrelated untracked artifact: protected `f000477_justice_public_safety_119_v1.zip`; do not read, stage, modify, or package.

## Implementation Sequence

1. Audit public presentation/evidence shapes and codify presentation-only selectors.
2. Recompose issue identity, distinct scopes, reviewed summary, takeaway, pattern index, and limitations.
3. Compact the ledger, add truthful grouping, and complete pattern filtering/focus/return behavior.
4. Harden generic states, responsive behavior, and accessibility.
5. Run focused through release-level frontend and affected governed-contract validation.
6. Generate and inspect the after-state packet, reconcile the diff, commit, push, and open a draft PR.

## Progress Checklist

- [x] Discovery started; governing product/workflow documents and full prompt read.
- [x] Implementation
- [x] Validation
- [x] Review packet
- [x] Commit/PR readiness

## Discoveries

- The exact required base is the current `main` HEAD; accepted receipt work was preserved before branch creation.
- The full-record review fixture exposes 37 actions, 32 episodes, governed pattern/action mappings, and special action boundaries without requiring semantic regeneration.
- Visual QA caught and corrected a compact-row fallback that could repeat full governed questions when no short label was supplied.

## Decisions And Rationale

- Use small presentation selectors and composition components; no Foushee-, issue-, roll-, or count-specific production branches.
- Preserve “reviewed” where it bounds analytical meaning, but remove review-process status theater and internal metadata from voter receipts.

## Deviations Or Corrections

- The earlier receipt-only prompt is treated as an accepted internal phase, not a separate milestone.
- Product review of PR #131 accepted the architecture and required a bounded voter-facing correction at reviewed head `448ef3a9e02497748974b1cc9692c1400891fb62`; governed backend content and identities remain out of scope.

## Validation Results

- Pre-continuation receipt phase: 114 unit tests, 20 targeted browser tests, lint without errors, production build, and leakage audit passed.
- Final frontend unit suite: 123 passed.
- Final Playwright suite: 44 passed, 3 opt-in capture tests skipped; the production-shaped selected-issue suite passed 8 of 8.
- Production frontend build passed; lint passed with no errors and 8 unrelated baseline hook warnings.
- Semantic IR validator passed; 26 governed contract tests passed.
- Diff check and rendered public-leakage audit passed.
- Production-build review packet: 16 captures and manifest generated outside the repository and visually inspected.
- PR #131 correction: 127 frontend unit tests passed; the complete Playwright suite passed 45 tests with 3 opt-in captures skipped; the focused production-shaped suite passed 9 of 9.
- PR #131 correction: production build, Semantic IR validation, 26 governed contracts, diff check, and leakage coverage passed; lint remained at 0 errors with 8 unrelated baseline hook warnings.

## Production Writes

- Performed: no
- Scope/expected/actual effects: none.

## Rollback Paths

- Revert the cohesive branch commit; no database, publication, artifact, registry, or deployment rollback is required.

## Blockers

- None at discovery.

## Final Reconciliation

- Initial milestone implementation was delivered in draft PR #131. At this correction commit boundary, implementation and local validation are complete; push, CI verification, and the production-data Vercel preview packet remain external post-commit steps and will be reported without another repository mutation.
