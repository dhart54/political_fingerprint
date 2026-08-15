# Milestone Plan: M12A Next Full-Record Issue Selection V1

## Intent

- Immediate task: select the next Valerie Foushee 119th-Congress issue under corrected generic criteria and construct its exact reviewable universe proposal.
- Larger-goal alignment: prove the Full-Record Issue Interpretation pipeline can expand across another public taxonomy domain without issue-specific or future-synthesis assumptions.

## Outcome

- A deterministic all-candidate comparison, one evidence-bound proposed universe (or a documented no-eligible result), and a draft PR for independent ChatGPT review.

## Scope And Boundaries

- In scope: current-state reconciliation; fresh official-cutoff proof; generic selector correction; Economy compatibility audit; all-domain accounting; selected-universe proposal; boundary and genericity review; regression validation; PR #147 description housekeeping; draft PR.
- Out of scope: action interpretation; accepted episodes; Semantic IR propositions; synthesis; wording; frontend changes; publication; production writes; deployment; universe acceptance or sealing.
- Files/systems likely touched: the cross-issue builder and schema, focused tests/validator, additive M12A artifacts and review packets, and current planning/state indexes.

## Decision Envelope

- Codex may decide and execute: deterministic selection and proposal generation under existing full-record boundary rules, plus documentation-only GitHub housekeeping.
- Explicit approval required for: accepting or sealing the proposed universe; M12B or downstream semantics; production/publication/deployment changes.

## Definition Of Done

- [x] Exact `44d966a7b3c36494b4965db6d4b00d6ba6d6a332` baseline and current production state reconciled.
- [x] Every remaining domain, including Economy, has complete deterministic accounting under generic criteria.
- [x] One eligible domain is selected without ideological, vote-direction, multi-action-episode, or future-synthesis preference, or the required no-eligible result is returned.
- [x] Selected proposal has closed high-recall accounting, exact source bindings, and human-readable boundary tables.
- [x] Economy compatibility and genericity audits are complete.
- [x] Justice and National Security active state is unchanged and validation is recorded.
- [x] Final diff is inspected, PR #147 is corrected, and a draft M12A PR is open.

## Baseline

- Branch/base commit: `codex/m12a-next-full-record-issue` from `44d966a7b3c36494b4965db6d4b00d6ba6d6a332`.
- Production/deployment state: Justice & Public Safety and National Security & Foreign Policy are publication-active; this milestone is read-only.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: the two user-protected ZIPs named in the milestone; untouched and outside scope.

## Implementation Sequence

1. Reconcile canonical current state and bind one fresh governed official action cutoff.
2. Generalize M11A selection, include Economy, and generate complete all-domain accounting.
3. Produce the selected proposal, boundary tables, Economy compatibility audit, and genericity audit.
4. Run deterministic, adversarial, semantic/full-record, production-regression, and repository-quality validation.
5. Inspect the diff, commit/push, correct PR #147's description, open a draft PR, and stop.

## Progress Checklist

- [x] Discovery started
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- M11A hard-excluded Economy and required a same-parent multi-action group for eligibility; ranking also rewarded multi-action groups.
- The official House Clerk index remains published through roll 283 on July 23, 2026; governed local inputs contain 638 Foushee actions through that roll.
- A fresh read-only production snapshot found 563 governed Foushee actions and two publication-registry rows; the transaction rolled back and the connection closed.
- Environment & Energy ranks first under the corrected generic criteria: 153 high-recall candidates, 62 directional plus one non-directional proposed substantive action, 64 procedural/context actions, one expressive action, zero exact-action-ineligible records, 25 unresolved cases, and 63 independent mechanical events.
- Economy & Taxes was evaluated rather than hard-excluded. Its 152 candidates resolve to 20 proposed substantive, 55 procedural/context, two expressive, 14 exact-action-ineligible, and 61 unresolved records, so it fails only the generic unresolved-to-substantive manageability gate.

## Decisions And Rationale

- Same-parent groupings remain descriptive mechanical evidence only and will not affect eligibility or ranking.
- Existing M11A historical artifacts remain immutable; M12A outputs will be additive.
- Cross-measure groupings are future review candidates only. They confer no semantic episode, interpretation, synthesis, acceptance, sealing, or publication authority.

## Deviations Or Corrections

- Current-state indexes now distinguish the historical M11A-M11M checkpoints from the live two-publication state established by M11N.
- PR #147's description was corrected to record its accepted/sealed authority, bounded production write, idempotent recheck, and live National Security result.

## Validation Results

- M12A artifact validator: passed; selected `ENVIRONMENT_ENERGY`, six candidates, 638 official actions, 153 selected candidates, 63 proposed actions, and 25 unresolved cases.
- Deterministic rebuild `--check`: passed against the exact governed inputs.
- Focused selector and M11A authority regressions: 25 passed.
- Historical M11A validators: passed, including the exact 82-action authority receipt.
- Semantic IR loop: 12 accepted plus four held-out cases validated; 26 unit tests passed.
- Full-record artifact validation: passed; 19 full-record tests passed.
- Justice/National Security publication regressions: 113 passed; API route regressions: 71 passed.
- Ruff, formatting, Python compilation, JSON parsing, documentation governance, full-record terminology governance, and diff whitespace checks: passed.
- Live rendered review: National Security showed the reviewed 82-action record and non-counting H.R. 8800 control; Justice showed its reviewed 37-action record. M12A introduced no frontend or runtime change.
- Draft PR #149 opened from the exact reviewed branch head. Vercel, Vercel Preview Comments, amendment-evidence-contracts, foushee-full-record-benchmark, publication-activation-postgres, and receipt-evidence-repair-postgres all passed on the initial M12A implementation head.

## Production Writes

- Performed: no
- Scope: read-only official/publication checks only.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Branch-local files and GitHub description metadata only; no runtime or database state is in scope.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes; implementation, local validation, draft-PR delivery, and hosted-check recording are complete.
- Remaining limitations: the selected universe is a review proposal only; its 25 unresolved cases remain excluded, including 14 child/amendment actions without exact child binding.
- Recommended next step: independent ChatGPT review of the exact draft-PR head; do not begin M12B.
