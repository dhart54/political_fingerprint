# M12D/E Environment & Energy Action Meaning and Episode Candidates V1

## Intent

Mechanically implement the independently accepted 63 M12C action meanings as
M12D canonical internal inputs, validate that gate, then generate detached M12E
policy-episode candidates on the same branch without collapsing authority states.

## Baseline and scope

- Accepted M12C PR/head: `#151` /
  `013fc57dbff538fd9d2b0b99b85c0a2285c2faba`.
- Exact PR #151 merge and combined-cycle base:
  `cdd1cf652b92b9577f698149534b7683d47c554e`.
- Accepted M12C artifact SHA-256:
  `84713da4156f8a3f0347384225905351017bf21615ebcdca76e147aa2294b242`.
- In scope: generic authority/episode contract corrections, exact 63-decision
  M12D implementation, independent M12D gate, conservative M12E episode
  candidates, empty decisions, review dossier, parity, validation, and one draft
  PR.
- Out of scope: M12F, Semantic IR, synthesis, public wording, frontend/site
  integration, publication, persistence, deployment, and production/database
  writes.

## Internal gates

1. Verify and guarded-merge exact PR #151.
2. Generalize M11-specific authority/cardinality/reviewer assumptions while
   preserving accepted M11D artifact identities.
3. Implement exactly 63 accepted decisions as written and independently validate
   M12D before episode work.
4. Derive M12E only from the accepted M12D implementation; fail closed to
   singleton episodes without affirmative legislative-event relationships.
5. Generate review artifacts, run adversarial and historical validation, publish
   one draft PR, and stop for independent M12E review.

## Completed M12D gate

- [x] 63/63 decisions are `accept_candidate_as_written`; zero blocked.
- [x] 47 opposition, 15 support, and one non-directional Not Voting effect.
- [x] 61 bounded official-purpose and two whole-package coverage states.
- [x] H.R. 6387 remains `non_directional_not_voting`.
- [x] H.R. 471 and H.R. 3898 limitations remain exact.
- [x] Generic schemas validate both M11D and M12D; accepted M11D hashes remain
  unchanged.
- [x] M12D deterministic and adversarial validation passes before M12E.

## M12E result and review boundary

- [x] All 63 accepted M12D records are assigned exactly once.
- [x] 63 singleton episodes; zero multi-action, cross-measure, blocked, or
  ambiguous/unassigned actions.
- [x] Seven explicit contrast reviews reject topic-, mechanism-, agency-,
  statute-, direction-, and package-only grouping.
- [x] H.R. 6387 remains a non-directional singleton in episode accounting.
- [x] Both whole packages remain indivisible singleton actions.
- [x] Human episode decisions are entirely empty; M12F and every later authority
  remain false.
- [x] Broad regression validation and exact diff review pass, apart from the
  unchanged historical Windows checkout byte-hash baseline noted below.
- [x] Draft PR #152 and six hosted checks passed at exact head
  `ecf087f0a6c916ef457014a75381198a16f54857`.

Independent review accepted M12D mechanically and all 63 M12E singleton
candidates semantically as written. PR #152 merged as
`450a759c5a2d0eaf767e68bc999c7d3ec8e9ca1e`.

## Stop condition

Stop at the draft PR for independent M12E semantic review. Do not accept episode
candidates or begin M12F or any later semantic/publication stage.

## Validation results

Focused M12D and M12E validators, deterministic rebuilds, generic-schema
cross-domain checks, adversarial tests, historical M11 and justice routing
validators, documentation governance, terminology, Ruff, compile, JSON parsing,
and diff checks pass. The explicit 557-test regression run had 556 passing and
one unchanged historical Windows checkout-only byte-hash failure in
`test_imported_acceptance_exact_bytes`; the two governed files still matched each
other and had no Git diff. All six hosted signals passed.
