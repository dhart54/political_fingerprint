# Milestone Plan: House Comparable Family Derived Artifact

## Intent

- Immediate task: Promote the merged PR #44 House comparable policy-question audit into a versioned derived artifact outside the production schema.
- Larger-goal alignment: Preserve reviewed family comparability in a reusable artifact for future `Record Across Congresses` work without schema changes or unsupported continuity/change claims.

## Outcome

- User-visible or operational result: A stable, diffable JSON artifact plus reusable builder/validator, targeted tests, and a review packet documenting safe uses, limits, validation, and next milestone recommendation.

## Scope And Boundaries

- In scope: House evidence only; 118th and 119th Congresses only; reviewed families and totals from PR #44; local versioned artifacts and validation code; read-only production access only if needed for reconciliation.
- Out of scope: Production writes, schema/migration changes, new ingestion, new interpretations/classifications, frontend/runtime changes, public endpoints, Senate work, new policy-family review, or continuity/change labels.
- Files/systems likely touched: `docs/derived/`, `scripts/`, `backend/tests/`, `docs/review_packets/`, and this active plan.

## Decision Envelope

- Codex may decide and execute: artifact JSON structure, local builder/validator implementation, targeted tests, documentation, PR creation, and merge once gates pass.
- Explicit approval required for: production writes, schema changes, frontend/runtime implementation, public API endpoints, semantic changes to family status, or any continuity/change claim generation.

## Definition Of Done

- [x] Versioned derived JSON artifact exists outside the production schema.
- [x] Artifact includes required metadata, methodology, recommendations, family fields, examples, roll-call identifiers, eligibility flags, and explicit non-authorization of continuity/change claims.
- [x] Reusable builder/validator validates PR #44 totals and artifact invariants.
- [x] Targeted tests cover schema validity, version metadata, family ID stability, comparability rules, cross-Congress membership, related/ungrouped exclusion, no movement labels, and PR #44 reconciliation.
- [x] Review packet documents purpose, safe use, non-use, regeneration, product framing, validation, and next milestone recommendation.
- [x] No production writes, schema changes, frontend changes, or runtime services are introduced.
- [x] Tests/build/validation recorded.
- [ ] PR/deployment runbook followed.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/house-family-derived-artifact` from `main` at `0f0eac9811351d371ee0da50f9333b22cf8be53f`.
- Production/deployment state, if relevant: No production access required unless local artifact reconciliation fails; PR #44 artifacts are the source basis.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`; permission-denied pytest temp directories visible in broad status.

## Implementation Sequence

1. Inspect PR #44 source artifacts and current tests.
2. Build a small reusable artifact builder/validator that reads the PR #44 audit JSON and emits a versioned derived artifact.
3. Generate the derived artifact and review packet.
4. Add targeted tests for schema, totals, eligibility, and no continuity/change claim fields.
5. Run targeted tests and update this plan with validation and final reconciliation.
6. Prepare commit, PR, checks, merge, and post-merge verification if gates pass.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Baseline commit matches the requested merge commit.
- PR #44 audit is the source of truth; this milestone should not redo family review unless validation finds a concrete inconsistency.
- PR #44 source JSON contains complete family roll-call IDs but only sample ungrouped examples, so the derived artifact builder uses the reviewed PR #44 deterministic rules plus read-only current evidence identity validation to reconstruct the full ungrouped set.
- The versioned artifact is `docs/derived/house_comparable_policy_question_families_v1.json`.
- Artifact totals reconcile to PR #44: 306 target roll calls, 15 candidate families, 13 common families, 4 directly comparable common families, 7 conditionally comparable common families, 4 related clusters, 225 ungrouped roll calls, 33,825 covered substantive vote rows, and 26.59% coverage.

## Decisions And Rationale

- Use a local derived artifact directory rather than a production schema object to preserve reviewability and avoid premature runtime coupling.
- Keep `Record Across Congresses` as the product framing in the artifact metadata.
- Treat `directly_comparable` and `conditionally_comparable` common families as future limited-comparison eligible, while `related_but_not_comparable` and `ungrouped` are explicitly ineligible.
- Recommend next milestone option 1: build a read-only backend/internal accessor for the derived artifact.

## Deviations Or Corrections

- Initial builder validation was too literal and flagged the required non-authorization language as a forbidden movement signal; corrected validation to forbid generated movement labels while preserving explicit guardrail text.

## Validation Results

- Generated artifact with `python scripts\house_comparable_family_artifact.py`; read-only validation reported `transaction_read_only = on`.
- Targeted tests passed: `python -m pytest backend\tests\test_house_comparable_family_artifact.py backend\tests\test_house_comparable_policy_question_audit.py` (`11 passed`).
- No frontend validation required because no frontend runtime changed.
- No full backend suite required because no shared runtime code changed.

## Production Writes

- Performed: no
- Scope: Not authorized for this milestone.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert this branch's local artifact, builder/validator, tests, and docs. No production rollback is required.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes, pending PR/check/merge completion.
- Remaining limitations: artifact remains local and derived; it is not a public API or frontend contract, and it does not authorize continuity/change claims.
- Recommended next step: build a read-only backend/internal accessor for the derived artifact.
