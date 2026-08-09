# Milestone Plan: M11B National Security Source Readiness V1

## Intent

- Evaluate interpretation-source readiness for exactly the 82 actions authorized
  by the detached M11A universe receipt.
- Produce content-addressed, neutral evidence packets for a future separately
  authorized action-interpretation milestone without interpreting any action.

## Scope And Boundaries

- In scope: a domain-neutral readiness evaluator and closed schema, bounded
  official-source acquisition, raw/projection separation, independent
  validation, adversarial tests, current-state reconciliation, commit, push,
  and one draft PR.
- Out of scope: universe changes, action meaning, support/opposition, episodes,
  propositions, Semantic IR, synthesis, public wording, runtime behavior,
  persistence, publication, deployment, and production access.
- The accepted Justice source-readiness and publication chain remains immutable.

## Implementation Sequence

1. Bind the exact M11A receipt, proposal, source inventory, cutoff, and 82-action
   set without changing any M11A artifact.
2. Acquire only official House Clerk and Congress.gov evidence required for the
   approved actions, keeping raw bytes content-addressed and projections closed.
3. Derive one of the six closed readiness states per action from role-specific
   identity, stage, member-action, and operative-content evidence.
4. Independently validate schemas, source bytes, digests, action equality,
   stage compatibility, neutrality, blocker precedence, and aggregate counts.
5. Run the requested regression/governance/tooling matrix, inspect the final
   diff, and publish one draft PR for human review.

## Definition Of Done

- [x] Exactly 82 approved action IDs appear once; no outside action appears.
- [x] Each action has exact member-action, identity/stage, and operative-content
  role accounting and one closed readiness state.
- [x] Whole measures, amendments, resolutions, and Senate-origin measures pass
  only with their required exact stage-compatible official evidence.
- [x] Raw official sources and neutral projections are separately digest-bound;
  party, sponsor, cosponsor, vote-direction interpretation, issue meaning,
  episode, synthesis, and public-language fields are absent from projections.
- [x] The evaluator is domain-neutral and tests cover at least the ten mandated
  adversarial cases.
- [x] M11A and Justice regressions pass; current state records source readiness
  only and preserves all later authorization gates as closed.
- [x] No frontend/backend runtime change, production/database/publication write,
  or protected-ZIP change occurs.
- [ ] One scoped commit is pushed and one draft PR is open; work stops before
  action interpretation.

## Baseline

- M11A merge commit and exact post-merge main: `434c972132e99628bddec4cc6392adc741e03205`.
- Branch: `codex/m11b-national-security-source-readiness`.
- Authorized universe head contained by the merge: `9ce8858d04581cad282c5ddf75583106013d976a`.
- M11A receipt: `universe-authority:f000477:national_security_foreign:119:v1`
  with file digest `89b7a27236ab0256b867c2525627408d84c6493c982c474ec4de3c2c36e79c87`.
- Protected Justice ZIP is unrelated untracked work and must remain untouched.

## Validation Plan

- M11A validator and deterministic regeneration.
- M11B schema, artifact, source, digest, and adversarial tests.
- Justice source-readiness, Semantic IR, full-record, publication/current-state,
  schema/digest, Ruff/format/compilation, JSON parsing, and `git diff --check`.
- Exact ancestry, M11A membership/digest preservation, Justice immutability,
  runtime-diff absence, and protected-ZIP preservation checks.

## Progress

- [x] M11A exact-head preflight and merge
- [x] Exact post-merge branch creation
- [x] Existing contract and 82-action source inventory
- [x] Generic contract and acquisition implementation
- [x] Artifact generation and independent validation
- [x] Full validation and reconciliation
- [ ] Commit, push, draft PR, and CI review

## Production Writes

- Authorized: no
- Performed: no
