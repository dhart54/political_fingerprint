# Milestone Plan: Valerie Foushee Economy & Taxes staged website V2

## Intent

- Immediate task: render the approved `db7eb324` candidate interpretations in a staged public interface with three progressive-disclosure layers.
- Larger-goal alignment: make source-grounded legislative behavior understandable within seconds while keeping receipts and boundaries available.

## Outcome

- User-visible or operational result: Foushee Economy & Taxes vote cards show approved reader-first copy, stage-specific arguments, caveats, and official sources in a draft preview without changing production or approval status.

## Scope And Boundaries

- In scope: a deterministic public-content bundle derived from the approved packet; narrowly keyed frontend rendering for F000477 / Economy & Taxes / the nine reviewed 119th-Congress rolls; fixtures, tests, build, desktop/mobile rendered review, draft PR.
- Out of scope: production deployment, merge, schema or persistence changes, changes to other members/issues, automated approval, issue-counting changes, or editorial rewrites.
- Files/systems likely touched: frontend interpretation components and fixtures, deterministic content generation/checks, focused tests, this plan, and a rendered-review packet.

## Decision Envelope

- Codex may decide and execute: component composition, responsive layout, accessible disclosure controls, deterministic public-source labels, focused fixtures/tests, feature branch/commit/push, and a draft PR.
- Explicit approval required for: merge, production deployment, status promotion, broader content rollout, wording changes to approved fields, or product-semantics changes.

## Definition Of Done

- [x] Seven approved interpretations render the exact proposed copy in three disclosure levels.
- [x] Rolls 263 and 180 remain contextual, non-counting controls; roll 310 remains Not Voting.
- [x] No claim IDs, audit terms, or review statuses appear in the normal public UI.
- [x] Official sources are human-readable and stage-correct.
- [x] Desktop and mobile rendered behavior is captured and reviewed.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/valerie-foushee-economy-staged-website-v2` from `db7eb324136866c360a68a2f996e91907eb3d76d`.
- Production/deployment state, if relevant: canonical frontend is live from its production branch; this milestone may create only a draft branch preview.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`; preserve and exclude.

## Implementation Sequence

1. Build and verify a deterministic public-safe content projection from the approved packet, claim map, and manifest.
2. Add narrowly gated progressive-disclosure cards and non-counting control treatment to the existing evidence flow.
3. Add fixtures and regression coverage for exact copy, source boundaries, counting boundaries, accessibility, and responsive hierarchy.
4. Run frontend/backend/interpretation validation and production build.
5. Render desktop/mobile, record review results, commit, push, and open a draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The current public interface renders generic vote summaries from API fields; the approved editorial packet is documentation-only and has no runtime connection.
- A frontend-side, exact-member/issue/roll projection permits preview validation against production-shaped API data without a backend or production-data write.

## Decisions And Rationale

- Keep the approved content `human_approval_pending` in data and hide status/audit fields from normal users.
- Match on bioguide ID, issue domain, Congress, and roll number so same-number rolls in other Congresses cannot inherit the content.
- Treat the seven interpretations and two controls as different presentation contracts because controls deliberately lack a substantive policy translation.

## Deviations Or Corrections

- No approved interpretation field was changed. House Clerk source locators are presented as "member vote and roll-call totals" instead of exposing an internal bioguide-oriented locator.

## Validation Results

- Backend staged-content, editorial-gold, manual-interpretation, and benchmark regressions: 52 passed.
- Frontend Node tests: 86 passed.
- Playwright rendered regressions at desktop and 390 x 844: 4 passed.
- Deterministic generator `--check`: passed.
- ESLint: passed with eight pre-existing hook warnings and no errors.
- Production frontend build and type validation: passed.
- Manual rendered review: passed at 1280 x 900 and 390 x 844; no horizontal overflow or disclosure-boundary defect found.

## Production Writes

- Performed: no
- Scope: none authorized.
- Expected effects: draft preview only.
- Actual effects: local render and draft branch preview only; no production write.

## Rollback Paths

- Revert the feature commit or remove the exact staged-content projection and its gated component; no database or production rollback is required.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes, for draft rendered review.
- Remaining limitations: rendered comprehension review and status promotion remain human decisions.
- Recommended next step: review the draft preview at desktop and mobile widths before any merge decision.
