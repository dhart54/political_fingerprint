# Milestone Plan: House Comparable Policy-Question Audit

## Intent

- Immediate task: Determine whether existing interpreted 118th and 119th House evidence in four conditionally comparable domains can be grouped into trustworthy policy-question families.
- Larger-goal alignment: Replace broad-domain overlap with reviewed governing-question comparability before any continuity/change product language.

## Outcome

- User-visible or operational result: A read-only comparable-family audit layer, threshold simulation, representative profile examples, and recommendation on family-model and continuity/change readiness.

## Scope And Boundaries

- In scope: House interpreted evidence only; 118th and 119th Congresses; Economy/Taxes, Environment/Energy, National Security/Foreign, and Justice/Public Safety; read-only production queries; local scripts, tests, and artifacts.
- Out of scope: New ingestion, new interpretations, production writes, schema/migration changes, frontend/runtime changes, Senate work, continuity/change claims, or model-generated family assignment.
- Files/systems likely touched: `scripts/`, `backend/tests/`, `docs/analysis/`, `docs/review_packets/`, and this active plan.

## Decision Envelope

- Codex may decide and execute: deterministic audit heuristics, human-reviewed artifact structure, read-only production queries, local artifact generation, targeted tests, documentation, and commit/PR preparation once the definition of done is met.
- Explicit approval required for: production writes, schema changes, permanent production family model, frontend implementation, interpretation/classification semantic changes, or any ambiguous civic comparability decision that cannot be represented safely.

## Definition Of Done

- [x] Field-reliability inventory covers candidate grouping fields with completeness, consistency, ambiguity, and cross-Congress usefulness.
- [x] Candidate family contract distinguishes directly comparable, conditionally comparable, related but not comparable, and ungrouped.
- [x] Reviewed sample inspects highest-value candidate families across all four domains and records inclusion/exclusion examples.
- [x] Machine-readable candidate-family artifact is generated.
- [x] Human-readable review packet records family coverage, threshold simulations, profile examples, model recommendation, unresolved risks, and next milestone.
- [x] Prior readiness totals are reconciled.
- [x] Read-only production access and no production writes are confirmed.
- [x] Cross-Congress isolation, not-voting exclusion, and procedural/limited non-counting treatment are validated.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/comparable-house-policy-question-audit` from `main` at `bc664a9`.
- Production/deployment state, if relevant: To be confirmed by read-only production analysis; prior readiness assessment reconciled public coverage totals at 2,259 roll calls and 627 eligible roll calls.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`; permission-denied pytest temp directories visible in broad `git status`.

## Implementation Sequence

1. Reuse the prior readiness artifact/script shape and inspect available source-grounded evidence fields.
2. Build a reusable read-only comparable-family audit script with deterministic candidate grouping and explicit review-status outputs.
3. Run read-only production analysis and reconcile totals with the merged readiness assessment.
4. Write structured candidate-family artifacts, threshold tables, profile examples, and the review packet.
5. Run targeted tests for reusable analysis tooling and update this plan with validation and final reconciliation.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Prior readiness review recommended this exact next milestone because broad issue domains produced high false-change risk.
- Prior baseline found 367 current House officials with substantive interpreted evidence in both Congresses, but no trustworthy continuity/change eligibility without reviewed policy-question comparability.
- Local branch was created from `main`; unrelated untracked artifacts pre-existed and are being preserved.
- Production schema contains source-grounded fields needed for a read-only audit (`roll_calls`, `bills`, `vote_classifications`, `vote_interpretations`, `vote_contexts`, `votes_cast`, and `legislators`), but no durable House policy-question-family table.
- The target universe contains 306 interpreted House roll calls in the four audited domains; 225 remained ungrouped by the reviewed deterministic rules.
- The audit identified 15 candidate families, 13 with evidence in both Congresses, including 4 directly comparable common families and 7 conditionally comparable common families.
- Directly comparable common families are annual defense authorization, hunting/fishing access, federal officer service-weapon purchase, and law-enforcement safety reporting.
- Prior readiness totals reconciled: 2,259 total roll calls, 627 eligible roll calls, and 367 current House officials with substantive interpreted evidence in both Congresses.

## Decisions And Rationale

- Keep comparable families as local review artifacts for this milestone because no production model is authorized.
- Use deterministic text and metadata signals only for candidate generation; final status stays reviewed/caveated in artifacts and does not alter product semantics.
- Treat shared broad domain, sponsor, bill identity alone, or political theme alone as insufficient for family membership.
- Recommend `FAMILY MODEL READY WITH MANUAL REVIEW` because common comparable families exist, but assignment quality still depends on reviewed source-grounded records.
- Recommend continuity/change readiness as `READY FOR LIMITED PROFILES`; however, `Record Across Congresses` should remain the product framing until a reviewed derived artifact is promoted and UI language is separately approved.
- Recommend a versioned derived artifact outside the production schema rather than a permanent production model in this milestone.

## Deviations Or Corrections

- Tightened an initially over-broad law-enforcement support-resolution matcher so DHS appropriations rows were not incorrectly grouped as support resolutions.
- Corrected threshold domain counts to count unique eligible officials by domain rather than family memberships.

## Validation Results

- Read-only production analysis completed and wrote `docs/analysis/house_comparable_policy_question_families.json`, `docs/analysis/house_comparable_policy_question_thresholds.csv`, `docs/analysis/house_comparable_policy_question_profiles.csv`, and `docs/review_packets/house_comparable_policy_question_audit.md`.
- Read-only confirmation reported `transaction_read_only = on`; no production writes were performed and no derived production outputs changed.
- Targeted tests passed: `python -m pytest backend\tests\test_house_comparable_policy_question_audit.py` (`5 passed`).
- No frontend validation was required because no frontend runtime code changed.

## Production Writes

- Performed: no
- Scope: Not authorized for this milestone.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Local-only artifacts and scripts can be reverted from this branch. No production rollback is required because no production writes are authorized.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: many 118th amendment rows still depend on generic issue facets and source-grounded summaries; conditional families require caveats for fiscal year, vote type, theater, and policy scope; strict burden controls still yield zero eligible current officials.
- Recommended next step: review and version a derived comparable-family artifact for the common directly comparable families before any frontend continuity/change language.
