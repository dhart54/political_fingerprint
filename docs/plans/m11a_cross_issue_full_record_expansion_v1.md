# Milestone Plan: M11A Cross-Issue Full-Record Expansion V1

## Intent

- Immediate task: select the next Valerie Foushee issue from current authoritative House evidence and construct a reviewable full issue-universe proposal.
- Larger-goal alignment: prove the Justice full-record method can begin scaling across issues without carrying Justice-specific semantic assumptions into a new domain.

## Outcome

- A deterministic National Security & Foreign Policy selection, complete candidate accounting, source-bound universe proposal, and human review packet through the July 23, 2026 official cutoff.

## Scope And Boundaries

- In scope: canonical-state reconciliation; six-domain selection; official-source acquisition; full-universe discovery; candidate dispositions; non-authorizing episode candidates; genericity audit; validation; draft PR.
- Out of scope: Justice or Economy selection; action interpretation; accepted episode modeling; synthesis; Semantic IR conclusions; public wording; frontend work; publication; deployment; promotion; production writes.
- Files/systems likely touched: M11A builder, artifacts, validator/tests, methodology schema, review packet, plan index, and current-state index.

## Decision Envelope

- Codex may decide and execute: deterministic evidence-based selection and exact-action-supported universe proposals under existing contracts.
- Explicit approval required for: accepting the universe boundary; beginning interpretation; any semantic/model change affecting accepted Justice outputs; publication, deployment, or production mutation.

## Definition Of Done

- [x] Exact checkpoint and merged PR #132 state reconciled before work.
- [x] Every non-excluded domain receives complete, deterministic accounting.
- [x] Winner selected without political-interest criteria.
- [x] Selected issue receives a complete high-recall, exact-source-bound universe proposal.
- [x] Unresolved and non-counting actions remain outside the substantive proposal.
- [x] Genericity findings and human-readable/JSON review artifacts recorded.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/m11a-cross-issue-expansion` from `f16bc73fb4e60d34fe75b17e58cb4f224e5b7fcd`.
- Production/deployment state, if relevant: read-only evidence confirms F000477 Justice artifact 221 is the sole active publication; M11A authorizes no write.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: protected user-owned `docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1.zip`; excluded and untouched.

## Implementation Sequence

1. Reconcile authoritative current state and rerun domain selection on the governed House cutoff.
2. Acquire exact official Clerk, Congress.gov measure, and Congress.gov amendment-index evidence and construct the selected universe proposal.
3. Validate accounting, bindings, parent-child and cross-domain boundaries, genericity, deterministic digests, and Justice regressions; commit, push, and open a draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The official House Clerk index remains complete through roll 283 on July 23, 2026.
- National Security & Foreign Policy is the only eligible non-excluded domain after exact child-action binding is enforced.
- The corrected selected high-recall set has 149 candidates: 82 proposed substantive, 33 procedural/context, two expressive, 26 exact-action ineligible, and six unresolved.
- The 82 proposed actions form 50 mechanically same-parent, non-authorizing episode candidates, five with multiple actions.
- Forty-two whole-measure actions have direct target-policy-area authority, 23 amendments have exact action-specific authority, and 17 cross-domain actions are retained with deeper official evidence.
- H.R. 495 and H.R. 7567 moved out of the proposal because their official summaries do not materially establish National Security membership; six narrower child actions without exact bindings remain unresolved and excluded.

## Decisions And Rationale

- Selection ranks only official-source completeness, independent episode count, mechanism variation, legitimate multi-action episodes, smallest unresolved boundary, and canonical ID tie-breaking.
- Parent-measure policy area and title are recall aids only. They never establish narrower child-action membership.
- A title hit cannot override a non-target official policy area; cross-domain retention requires deeper action-specific official evidence.
- Counted episode grouping uses only same-parent legislative identity and remains non-authorizing. Possible cross-measure War Powers relationships are future review notes with no M11A authority effect.

## Deviations Or Corrections

- An initial Environment & Energy result incorrectly treated retained divisions of an appropriations measure as if the parent title established their issue meaning. The builder was corrected to require exact child-action binding; the affected rows became unresolved rather than substantive, leaving National Security & Foreign Policy as the only eligible domain.
- Human review of head `48dd78f` found recall keywords were still being used as ordinary whole-measure boundary authority and that cross-measure War Powers grouping affected counts. The bounded correction separates canonical policy-area/deeper-source authority from recall, removes semantic grouping from accounting, and makes every downstream authorization explicitly false.

## Validation Results

- M11A schema, accounting, exact-source, digest, unresolved-boundary, and source-inventory validator: passed.
- Focused policy-authority, parent/child, cross-domain, procedural, expressive, and episode-accounting tests: 10 passed.
- Deterministic generated-artifact check: passed.
- Justice Editorial Semantic IR validator and regression suite: passed; 26 tests.
- Full-Record Issue Interpretation validator and regression suite: passed; 19 tests.
- Ruff lint and format checks: passed.
- Python compilation, JSON parsing, and `git diff --check`: passed.
- Detached M11A universe-authority receipt validator and adversarial regression suite: passed; 11 tests.
- Existing generic universe-authority regression suite: passed; 12 tests.
- Documentation and full-record terminology governance: passed.

## Production Writes

- Performed: no
- Scope: read-only repeatable-read production discovery with explicit rollback and connection close.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- All changes are branch-local files. No publication, production, deployment, or accepted semantic state changed.

## Blockers

- None for the M11A review packet. Human approval is intentionally required before any interpretation milestone.

## Final Reconciliation

- Definition of done satisfied: yes; implementation and validation are complete, with a bounded correction commit to the existing draft PR as the delivery operation.
- Remaining limitations: six exact child-action boundaries remain unresolved and excluded; episode candidates are not accepted episodes.
- Human universe-boundary decision: approved by `dhart54` under `full_issue_universe_review_authority_v1` against PR #133 head `1860ef0fab3f65ffb303c5b74b380f41fe929421`.
- Approved boundary: 82 substantive actions; 33 procedural/context, two expressive/nonbinding, 26 exact-action-ineligible, and six unresolved actions remain outside the approved universe.
- Authority effect: universe membership only. Action interpretation has not started; episode acceptance, Semantic IR, synthesis, public wording, publication, and production persistence remain unauthorized.
- Detached authority receipt: `docs/editorial/full_record_reviews/f000477_national_security_foreign_119_full_issue_universe_authority_receipt_v1.json`.
- Recommended next step: final mechanical review of the authority receipt and closeout commit. Do not begin M11B in PR #133.
