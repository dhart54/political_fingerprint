# Milestone Plan: House Continuity Readiness Assessment

## Intent

- Immediate task: Assess whether existing 118th and 119th House evidence can support trustworthy continuity/change summaries.
- Larger-goal alignment: Advance balanced multi-Congress accountability profiles by separating meaningful cross-Congress records from agenda-driven or sparse-evidence comparisons.

## Outcome

- User-visible or operational result: A read-only, source-grounded readiness packet with machine-readable coverage/comparability artifacts, threshold simulations, profile validations, an eligibility contract, and a product recommendation.

## Scope And Boundaries

- In scope: House officials only; existing production evidence for the 118th and 119th Congresses; existing classification, interpretation, readiness, support/opposition, alignment, and API contracts; read-only production queries; local analysis artifacts and tests.
- Out of scope: New ingestion, Senate analysis, production writes, schema or migration changes, frontend implementation, continuity/change product language, model-generated political claims, parent-bill-only inference, or broad refactors.
- Files/systems likely touched: `docs/plans/`, `docs/review_packets/`, `docs/analysis/` or `scripts/` for reusable read-only analysis, and targeted tests if reusable tooling is added.

## Decision Envelope

- Codex may decide and execute: read-only production queries, local analysis scripts, threshold simulations, review packet writing, targeted tests, and commit/PR preparation once artifacts satisfy the milestone.
- Explicit approval required for: any production write, schema change, frontend/runtime feature implementation, or PR before the readiness definition of done is met.

## Definition Of Done

- [x] Coverage inventory distinguishes universe roll calls, official participation, cast votes, and substantive evidence.
- [x] Comparability assessment classifies issue domains without treating shared domain alone as sufficient.
- [x] Agenda-difference risks are grounded in concrete evidence examples.
- [x] Threshold simulations report qualifying profile counts, percentages, represented domains, exclusions, and false-change risk.
- [x] Required validation profiles are documented, including Valerie Foushee and Aaron Bean.
- [x] Product framing options are compared and one of `READY`, `READY FOR LIMITED PROFILES`, or `NOT READY` is recommended.
- [x] Machine-readable analysis artifacts and human-readable readiness packet are written.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/house-continuity-readiness-assessment` from `main` at `61f009f` (`PR #42` merge commit; `PR #41` merge commit `0edb9df`).
- Production/deployment state, if relevant: To be confirmed by read-only `/metadata/coverage` and production database queries.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Discover current API/query semantics, production schema, coverage metadata, and available evidence fields.
2. Build or adapt a read-only analysis tool that produces coverage, comparability, threshold, and profile-validation artifacts.
3. Reconcile tool output against public metadata/API semantics and investigate any mismatches.
4. Write the readiness packet, proposed eligibility contract, risks, and recommendation.
5. Run targeted tests for reusable tooling and record validation, including the previously blocked tmp-path import-persistence check if possible.
6. Prepare intended files for commit/PR if the milestone artifacts satisfy the definition of done.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Local `main` was behind `origin/main`; after fetch and fast-forward it is at `61f009f`.
- GitHub confirmed `PR #41` merged at `0edb9df` and `PR #42` merged at `61f009f`.
- Public `/metadata/coverage` and `/coverage/metadata` reconcile to production totals: `roll_call_count = 2259`, `eligible_roll_call_count = 627`.
- Current House officials with substantive interpreted evidence in both Congresses: 367 of 441.
- Shared broad issue domain is not enough for material comparability; structured topic overlap is too coarse for continuity/change claims.
- No domain is strongly comparable; four are conditionally comparable and four are not currently comparable.

## Decisions And Rationale

- Use a scoped milestone branch to preserve the clean `main` baseline and unrelated untracked artifacts.
- Keep any analysis code outside runtime API/frontend paths unless a small reusable read-only helper materially improves repeatability.
- Recommendation is `NOT READY`; safest product framing is `Record Across Congresses`.
- Keep the read-only analysis script as reusable tooling because future evidence expansion should rerun the same threshold and comparability checks.

## Deviations Or Corrections

- Initial analysis treated broad `issue_facet` overlap as potential topic overlap; corrected so broad-domain labels do not count as material policy-question matches.
- Public coverage endpoint checks required escalated network access because sandbox curl was routed to `127.0.0.1:9`.

## Validation Results

- Read-only analysis script completed and wrote `docs/analysis/house_continuity_readiness_analysis.json`, `docs/analysis/house_continuity_thresholds.csv`, and `docs/analysis/house_continuity_profile_examples.csv`.
- Public API validation: `/metadata/coverage` and `/coverage/metadata` returned database source with matching totals; Valerie Foushee `scope=118`, `scope=119`, and `scope=all` returned isolated congress metadata.
- Targeted analysis tests: `python -m pytest tests\test_house_continuity_readiness_analysis.py` passed (`3 passed`).
- Previously blocked tmp-path persistence test: sandbox rerun reproduced `PermissionError: [WinError 5]`; escalated rerun passed (`1 passed`), confirming an environment-specific local filesystem issue.

## Production Writes

- Performed: no
- Scope: Not authorized for this milestone.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Documentation and local artifacts can be reverted by removing this branch's added files. No production rollback is required because no writes are authorized.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: Structured topic fields cannot prove material policy-question family overlap; no CI run was triggered from this local branch.
- Recommended next step: comparable-question audit artifact for existing House interpreted evidence before any continuity/change feature work.
