# Milestone Plan: Generic editorial issue frontend

## Intent

- Immediate task: promote the staged Valerie Foushee Economy & Taxes renderer into a generic editorial issue experience selected by the real representative issue flow.
- Larger-goal alignment: establish a reusable, evidence-preserving frontend contract before validating it with a second researched issue domain.

## Outcome

- User-visible or operational result: a representative issue may use the rich editorial experience when a matching slice is eligible for its environment; otherwise the existing basic evidence experience remains in place. Pending content stays confined to explicit review mode.

## Scope And Boundaries

- In scope: generic view-model adaptation, selection/publication gating, component rename and refactor, real-route integration, shared review harness, synthetic test-only coverage, responsive tests, workflow documentation, draft PR and preview evidence.
- Out of scope: source or claim edits, status promotion, persistence/API migrations, a second researched issue packet, fallback redesign, merge, or manual production deployment.
- Files/systems likely touched: `frontend/components`, `frontend/lib`, the golden-render review route/tests, focused editorial workflow docs, and this plan/review packet.

## Decision Envelope

- Codex may decide and execute: generic frontend contract shape, pure eligibility helpers, test-only fixture structure, accessible component boundaries, focused tests, screenshots, commit/push, and draft PR creation.
- Explicit approval required for: changing civic meaning/counting/source mappings, publishing pending content, schema or API migration, merge, or production deployment.

## Definition Of Done

- [x] Real representative issue flow selects an eligible generic editorial slice and otherwise preserves the basic fallback.
- [x] Pending slices render only in explicit review/preview mode and remain visibly labeled there.
- [x] Generic adapter/component support optional sections, variable record/episode counts, grouped deduplicated sources, Not Voting, and context-only records.
- [x] Foushee review harness and a substantively different synthetic fixture share the production-capable adapter and renderer.
- [x] Runtime selection/rendering contains no Foushee-, Economy-, roll-, or fixed-count conditions.
- [x] Tests/build/rendered validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/generalize-editorial-issue-frontend` from `086d86cfe76d7862eea1a843c83d770bb0482038` (`main`).
- Production/deployment state, if relevant: pre-launch production exists; this milestone permits only automatic draft-PR preview deployment.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`; preserve and exclude.

## Implementation Sequence

1. Map the real route, evidence loader, review harness, source bundle, and current hard-coded assumptions.
2. Define a generic view model and pure selection/eligibility contract, then adapt the existing pending slice without altering its source claims.
3. Rename/refactor the renderer, integrate it through `EvidencePanel`, and keep the basic fallback intact.
4. Add a synthetic review-only fixture plus unit, routing, interaction, responsive, regression, and genericity coverage.
5. Run content/frontend checks, build, rendered review, documentation reconciliation, commit, push, draft PR, and preview verification.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The real representative route is `frontend/app/page.js`, which supplies the selected member to `PositionByIssue`; that component loads `/legislators/{id}/positions/{domain}/evidence` and renders the selected issue in `EvidencePanel`.
- The review route passes production-shaped fixture data through the same `PositionByIssue`, but the existing selector and renderer directly import the Foushee bundle and Foushee-specific issue synthesis.
- The current fixture route is unlinked and enabled only by an explicit environment flag or Vercel preview; production representative pages have no explicit publication-eligibility contract yet.
- Static bundle selection exists only as a single hard-coded member/domain/Congress/roll matcher, not as a reusable registry or view-model selector.

## Decisions And Rationale

- Interpretation boundary: React will render only supplied synthesis/pattern language and will not infer philosophy, support, opposition, or episode counts from raw votes.
- Production eligibility will require all separate governance signals: human editorial approval, gold-benchmark promotion, and an explicit production-eligible flag. Review mode may show pending content but must label it as review content.
- Source bundle matching remains evidence-aware, but the renderer receives only a normalized reader-facing view model and never reads the Foushee review packet or identity constants.

## Deviations Or Corrections

- The first responsive run exposed source-encoding and same-URL navigation state in newly added test code; both were corrected before final validation.
- A sandboxed pytest run completed assertions but failed a tmp-path case and cleanup because Windows denied its temp directory. The identical 52-test suite passed outside the sandbox.

## Validation Results

- 52 focused backend/content regressions passed.
- 91 frontend Node tests passed.
- 8 Playwright tests passed across wide, laptop, tablet, and mobile layouts, including production-mode fallback integration.
- Deterministic staged-content check, ESLint (zero errors; eight pre-existing warnings), production build/type validation, and rendered browser review passed.
- Ten local captures cover fallback, pending review, summary, collapsed/expanded/deep source states, mobile, synthetic genericity, and optional omission.

## Production Writes

- Performed: no
- Scope: none authorized.
- Expected effects: branch preview only.
- Actual effects: local tests, builds, and explicit review-route renders only before draft-PR publication; no production write.

## Rollback Paths

- Revert the focused frontend commit; no database, API, or production-data rollback is required.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes; intended files are staged after all gates passed, with draft PR publication remaining as the final authorized handoff action.
- Remaining limitations: second real issue-domain validation is explicitly deferred to the next milestone.
- Recommended next step: validate the refined generic contract with a second researched issue domain after this PR.

## Pre-Merge Correction Pass

- Intent: harden PR #94's publication boundary and correct narrowly scoped genericity/optional-content defects without changing the approved renderer hierarchy or Foushee editorial content.
- Scope: split production/review registries; reconcile registry and source approval status; remove fixed record-count copy; omit empty additional lists; condition argument boundaries; strengthen source deduplication; require explicit episode identity.
- Boundaries: no redesign, source edits, status promotion, count changes, merge, or manual deployment.
- Progress: implementation and local validation complete; final reconciliation, commit, and normal push remain pending.
- Interpretation decision: no new synthesis is generated; the correction only prevents unsupported publication or presentation implications.
- Reconciliation: the production registry is empty and has no dependency on pending content; the review fixture explicitly supplies the pending registry through the shared selector/adapter/renderer. Production eligibility now reconciles registry, source, and included-record approval status. Fixed-count copy is removed, empty additional evidence is omitted, argument boundaries are conditional, official sources require valid HTTP(S) URLs and deduplicate by stable ID or canonical URL, and episode identity is explicit-only.
- Validation: 93 frontend Node tests, 52 focused backend/content/interpretation tests, 9 responsive Playwright tests, deterministic staged-content generation check, ESLint, production build/type validation, and `git diff --check` passed. ESLint/build retain eight pre-existing hook warnings and no errors.
- Source/content preservation: Foushee top-level and record statuses remain `human_approval_pending`; no Foushee source claims, mappings, copy, vote counts, episode counts, or inclusion semantics changed.
