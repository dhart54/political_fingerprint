# Milestone Plan: Blind Editorial Pipeline Validation V1

## Intent

- Immediate task: Run the accepted editorial standardization pipeline blindly on one deterministically selected, genuinely new representative from the existing Justice cross-member cohort.
- Larger-goal alignment: Determine whether shared Justice dossiers, generic member overlays, inference, presentation, and the 37-rule validator generalize without manual editorial repair or member-specific behavior.

## Outcome

- User-visible or operational result: One guarded, review-only candidate slice either passes the frozen pipeline or records a stable rule-level block, with the first generation and validation result preserved.

## Scope And Boundaries

- In scope: Existing seven substantive Justice actions, five episodes, six procedural controls, shared Justice evidence, cross-member overlays, deterministic candidate selection, generic generation, standardization validation, one review anchor, tests, bounded rendered smoke review, review packet, and draft PR.
- Out of scope: New research, bills, actions, issue domains, Congresses, cohort expansion, changed sources or vote facts, production registry changes, approval/promotion, frontend redesign, ingestion, ZIP work, merge, or manual deployment.
- Files/systems likely touched: Generic backend inference/generation, Justice cohort artifacts, standardization fixtures/validator inputs, review registry/harness, tests, and milestone documentation.

## Decision Envelope

- Codex may decide and execute: Deterministic novelty scoring and tie-breaks; generic artifact wiring; tests; one generalized correction pass only when a candidate-independent defect is proven with positive and negative coverage; commit, push, and draft PR.
- Explicit approval required for: New civic semantics or schema outside the frozen architecture, production writes, human approval, benchmark promotion, production eligibility, merge, or manual deployment.
- Frozen: Episode-first hierarchy, action-card structure, four analytical section types, shared-evidence contract, service semantics, compact coverage, three-to-five featured episodes, complete-record/procedural disclosures, 37 rules, and three reference fixtures.

## Definition Of Done

- [x] Candidate is selected before generation using structured action evidence and a machine-readable record.
- [x] First generated conclusion and first 37-rule result are preserved before rendered inspection.
- [x] Candidate uses shared dossiers, generic overlay/inference/presentation contracts, and remains review-only.
- [x] Candidate tests, reference regressions, 20 mutations, identity/leak/source/drift scans, frontend tests, lint, build/type checks, and `git diff --check` pass or an allowed stable block is documented.
- [x] Bounded desktop/mobile smoke review and review packet are complete.
- [x] Intended files are committed, pushed, and presented in a tightly scoped draft PR.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/blind-editorial-pipeline-validation-v1` from `7bce7467cebfde4fd2f164bdcecb596ba0fd1e91`.
- Remote state: Fetched `origin`; local `main` and `origin/main` both matched the required commit; PR #98 was confirmed merged at that commit.
- Production/deployment state: No production write, merge, or manual deployment authorized. Candidate must remain pending, unpromoted, production-ineligible, and absent from the production registry.
- Tracked working tree: Clean isolated worktree created because the primary checkout contains unrelated tracked and untracked work.
- Known unrelated artifacts: All primary-checkout changes and existing sibling worktrees remain untouched.

## Implementation Sequence

1. Inspect the three reference fixtures, 37-rule validator, 20 mutations, standardization workflow, and Justice cross-member cohort.
2. Implement and run deterministic pre-generation selection; commit the selection record to the artifact flow.
3. Generate the candidate once, run validation, and preserve the first output/result before any rendered inspection.
4. If and only if a generalized defect is proven, make one correction with regression and malformed coverage; otherwise retain the clean pass or stable block.
5. Add the guarded review anchor and direct acceptance tests without candidate-specific runtime logic.
6. Run the full required regression suite, then the bounded rendered smoke review.
7. Reconcile the review packet, commit, push, and open a draft PR without merging.

## Progress Checklist

- [x] Startup gates and governing-document discovery
- [x] Architecture and fixture inspection
- [x] Candidate selection
- [x] Blind generation and first validation
- [x] Implementation/correction
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The primary checkout is intentionally dirty with unrelated milestone work, so this branch uses a separate clean worktree.
- Four non-reference, complete, non-identical cohort vectors were eligible. The lexicographic novelty score selected García's all-Nay vector.
- The first generated conclusion passed the accepted 37-rule validator but repeated a bounded-sample phrase; this exposed a generalized validator/catalog gap rather than a candidate data gap.
- All candidate actions, sources, service support, and episode relationships were complete; no new research or analytical category was required.

## Decisions And Rationale

- Interpretation boundary: All generated findings must remain bounded to the reviewed actions and concrete mechanisms; no motive, ideology, character, prediction, recommendation, or unsupported cross-time movement claim is permitted.
- Blind-order boundary: Candidate selection precedes conclusion generation; rendered inspection follows first validator output; the selected member will not be changed after generation.
- Deterministic validation establishes contract conformance only. It does not confer human editorial approval or publication authority.
- The one permitted generalized correction removes duplicate bounded-sample wording for any equivalent future vector and extends existing `DETAIL-001`; the three reference fixtures retain their meaning.

## Deviations Or Corrections

- One generalized correction pass: removed duplicate “in this sample” catalog wording, enforced duplicate bounded-sample detection through `DETAIL-001`, and added a negative test. The preserved first generation and validation remain unchanged.

## Validation Results

- Startup: `origin/main`, local `main`, and required starting commit matched; PR #98 merged.
- First candidate validation: 37/37 pass, zero findings.
- Final candidate validation: 37/37 pass, zero findings.
- Original mutations: 20/20 blocked by expected rule IDs; added duplicate-boundary negative case blocked by `DETAIL-001`.
- Backend editorial suite: 60 passed. Frontend Node suite: 132 passed.
- Lint: passed with eight pre-existing hook warnings. Build/type validation: passed.
- Rendered suite: 12 passed, 12 intentionally superseded/opt-in skipped. Desktop/mobile captures inspected with no bounded smoke-review defect.
- Generator/validator drift, reference fixtures, shared-evidence identity, member leakage, source integrity, registry isolation, and `git diff --check`: pass.
- Primary commit: `801eabaa857419d13fd797cb6577b1a457dbb6f2`.
- Draft PR: `#99`, targeting `main`; required backend and Vercel checks passed.
- Vercel preview: Ready at `https://political-fingerprint-git-codex-blind-6db175-dhart54s-projects.vercel.app`.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the milestone commit(s) or delete the isolated review artifacts/anchor; no production data, schema, approval state, or deployment rollback is expected.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes; implementation, local validation, scoped commit/push, draft PR, and hosted preview status are complete.
- Remaining limitations: deterministic validation does not confer human editorial approval; this is one additional member/vector.
- Recommended next step: proceed to broader generality validation after draft-PR preview checks.
