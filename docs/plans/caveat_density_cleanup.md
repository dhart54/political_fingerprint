# Milestone Plan: Caveat Density Cleanup

## Intent

- Immediate task: Reduce repetitive caveat language in frontend interpretation surfaces while keeping evidence boundaries available.
- Larger-goal alignment: Make Political Fingerprint read like a plain-English voting-record interpreter with receipts, not a defensive evidence library.

## Outcome

- User-visible or operational result: Top summaries lead with bounded findings, issue sections keep one read-level boundary, vote rows retain detailed source/caveat drawers, and methodology/history artifacts remain intact.

## Scope And Boundaries

- In scope: Frontend user-facing copy audit, copy consolidation, targeted tests, rendered validation, review packet, commit/PR readiness.
- Out of scope: Backend, data/model/schema/methodology changes, new features, production writes, broad redesign.
- Files/systems likely touched: `frontend/lib/issueOverview.mjs`, `frontend/components/PositionByIssue.js`, frontend tests, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: Copy placement and wording within existing civic-integrity boundaries; tests and docs for the revised hierarchy.
- Explicit approval required for: Any product semantics change, data/model/schema change, production write, or overbroad claim that removes necessary boundaries.

## Definition Of Done

- [x] Required caveat terms audited and classified.
- [x] Repetitive top-level caveats consolidated without removing vote-level/source caveats.
- [x] Targeted tests updated or added.
- [x] Lint/build/test/static scan recorded.
- [x] Rendered validation recorded for Valerie Foushee; Aaron Bean Record Across validation completed; Aaron Bean issue-detail validation recorded as unavailable in the local payload.
- [x] Review packet updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/caveat-density-cleanup` from `main` at `0da4f07`.
- Production/deployment state, if relevant: No production writes authorized or planned.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Audit frontend caveat terms and classify occurrences.
2. Consolidate issue-level caveats into one concise read-level boundary and keep vote-row drawers intact.
3. Update tests for revised copy expectations.
4. Run lint, build, node tests, static token/internal-route scan, and rendered validation.
5. Create review packet, reconcile plan, commit, push, and open ready PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Repository-wide search is dominated by historical review packets, derived artifacts, backend data contracts, and methodology files. The implementation audit is narrowed to `frontend` user-facing copy and tests; historical/methodology artifacts are classified as retained.
- Frontend repetitions are concentrated in issue overview read copy and the issue boundary panel. Vote-level `Source, caveats, and full context` and Record Across Congresses caveats are evidence/readiness boundaries that should remain.
- Record Across rendered locally once the frontend and backend production servers were restarted with the same throwaway `INTERNAL_API_TOKEN`.

## Decisions And Rationale

- Preserve vote-level `what_not_to_infer` fields behind existing source/caveat details; this is the appropriate receipt layer.
- Replace issue-level "What not to infer" and repeated motive warnings with a single "How to read this" boundary that points users to vote-level source/caveat drawers.
- Lead issue evidence summaries with the finding/pattern and move reviewed-vote background into the receipt layer immediately below.

## Deviations Or Corrections

- Local rendered validation deviated from the full requested matrix: Valerie desktop/mobile completed; Aaron Bean Record Across completed; Aaron Bean issue-detail validation was not practical because the local issue-readiness payload rendered as unavailable.

## Validation Results

- `cd frontend; npm run lint`: passed with 8 existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with the same existing React hook dependency warnings.
- `cd frontend; node --test lib\*.test.mjs`: passed, 55 tests.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches; no-match exit treated as success.
- Rendered validation: Valerie Foushee desktop and 390x844 mobile passed for finding-first issue summary, reduced repeated caveat language, one issue-level boundary, vote-level source/caveat drawers, issue evidence rendering, no horizontal overflow, and no visible internal token/header/route text.
- Rendered validation: Aaron Bean Record Across Congresses rendered on the token-backed local frontend with 11 eligible families, no horizontal overflow, and no visible internal token/header/route text.
- Rendered limitation: Aaron Bean issue-detail validation was not completed because the local page reported that issue readiness was unavailable for that legislator.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the focused frontend copy/test/doc commit.

## Blockers

- None active. Aaron Bean issue-detail validation remains limited by the local payload.

## Final Reconciliation

- Definition of done satisfied: Yes for the focused caveat-density cleanup. Implementation, tests, build, static scan, Valerie rendered validation, Aaron Bean Record Across validation, and review packet are complete.
- Remaining limitations: Aaron Bean issue-detail rendered validation remains unavailable in the local payload; this does not block the focused caveat hierarchy change.
- Recommended next step: Commit the focused implementation and open PR.
