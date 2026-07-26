# Editorial Semantic IR V1 Candidate Review

Status: `candidate_pending_external_semantic_review`

External semantic review decisions have been applied to the candidate contract.
This packet records those decisions; it does not present them as unresolved
questions and does not change any acceptance, production, or publication gate.

## Applied role model

- Behavioral propositions describe member actions and render only in
  `repeated_patterns`, `policy_trajectories`, or `other_notable_choices`.
- Synthesis propositions derive conclusions; the reviewed candidates use
  `conclusion_only`, while the contract also permits an explicit limitation or
  omission target.
- Coverage boundaries are evidence-state records using `coverage_note`, not
  behavioral propositions.
- Counting and control-exclusion rules are method boundaries using
  `method_note`.
- Source completeness is a shared source/render constraint using `source_note`.
- Only section-rendered behavioral propositions participate in the
  one-primary-section invariant.

The machine packet records every proposition role, presentation target,
relationship, conclusion-plan reference, coverage/method boundary, shared
source constraint, and accepted-action accounting entry.

## Candidate decisions

| Case | Scope | Applied external decision | Accepted-action accounting |
| --- | --- | --- | --- |
| `semir-dev-01-economy-funding-stages` | full record | Keep one H.R. 5371 trajectory; move one-episode counting to method only. | 2/2 actions in the trajectory. |
| `semir-dev-02-economy-uniform-no-throughline` | full record | Retain funding and budget trajectories plus the military-construction and SBA choices; uniform direction and no common throughline are conclusion-only synthesis. | 6/6 actions in behavioral propositions. |
| `semir-dev-03-economy-noncounting-boundaries` | full record | Separate one eligible substantive Not Voting action from two context-only controls; coverage and method objects replace the former proposition. | 1/1 eligible action has an explicit non-directional reason; 2 controls excluded. |
| `semir-dev-04-justice-mixed-fentanyl-trajectory` | full record | Retain the three-stage mixed trajectory; treat the no-change claim as conclusion-only synthesis. | 3/3 actions in the trajectory. |
| `semir-dev-05-justice-mechanism-divide` | full record | Retain two patterns and the mixed fentanyl trajectory; mechanism divide is conclusion-only synthesis. | 7/7 actions in behavioral propositions. |
| `semir-dev-06-justice-one-sided-argument` | full record | Retain the reporting choice; move one-sided argument availability to a shared source/render constraint. | 1/1 action in a notable choice. |
| `semir-dev-07-environment-exact-action-gate` | full record | Retain roll 6 as eligible and roll 5 only as rejected eligibility context. | 1/1 eligible action in a notable choice; 1 rejected context action excluded. |
| `semir-dev-08-environment-separate-family-episodes` | full record | Retain both repeated patterns; mechanism divide is conclusion-only synthesis. | 4/4 actions in behavioral propositions. |
| `semir-dev-09-not-voting-heavy-record` | full record | Retain the two Yea choices as notable propositions and withhold a broad conclusion because five actions are Not Voting. | 2 actions behavioral; 5/5 remaining actions have explicit Not Voting reasons. |
| `semir-dev-10-present-known-coverage` | full record | Preserve six Yea and one Present; retain the appropriations trajectory, resource pattern, and two notable choices; uniform direction/no-throughline remain conclusion-only. | 6 actions behavioral; the Present action has an explicit non-directional reason. |
| `semir-dev-11-tied-pattern-ownership` | full record | Retain both tied patterns, the appropriations trajectory, and the federal-land choice; the latter two limit the conclusion without replacing the patterns. | 7/7 actions in behavioral propositions. |
| `semir-dev-12-identity-title-order-invariance` | focused invariant fixture | Limit the fixture to identity, party, title, order, stable-ID, and deduplication invariance. | 2 actions behavioral; 5 actions explicitly outside the focused assertion. |

## Revised coverage contract

Each member record separately reports eligible substantive actions,
context-only/control actions, in-service eligible actions, resolved eligible
actions, directional Yea/Nay positions, Present, Not Voting, missing evidence,
outside-service actions, and complete/partial episodes. Controls and rejected
context never inflate substantive denominators.

## Held-out inputs

The four held-out cases remain input-only. They contain authoritative
references, member action states, and a semantic question, but no expected
propositions, boundaries, action accounting, or conclusions.

## Gate

The role-model review has been incorporated, but every development case remains
`candidate_pending_external_semantic_review`. This revision does not authorize
runtime adoption, persistence, population generation, promotion, or
publication.
