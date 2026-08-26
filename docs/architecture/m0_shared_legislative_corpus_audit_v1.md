# M0 Shared Legislative Corpus Feasibility Audit V1

This is a deterministic, offline, non-authorizing architecture audit. It does not change canonical semantics, production, publication, or presentation.

## Verdict

`TARGET_PATH_PROVEN_REFACTOR_REQUIRED`

Repository head: `d9e4d27b66253b20e1871d2e038f999fd212f565`. Expected baseline `74b054bfb8f138b8b6a31289f48995ceefcb0240` is an ancestor; the intervening Publication Activation Governance V2 change was inspected as a presentation-boundary fact and not reopened.

## Current architecture finding

The canonical Editorial Semantic IR compiler already separates `shared_semantics` from member action arrays, but four upstream artifact families remain mixed: member-scoped universe discovery/domain eligibility, source readiness, action interpretation, and policy episodes. Synthesis, wording, and presentation are appropriately downstream and member-specific.

| Stage | Current designation | Target disposition |
|---|---|---|
| chamber action inventory | shared | adapt |
| member issue-universe discovery | mixed | split into shared action eligibility and member projection |
| exact-action domain eligibility | mixed | split |
| operative source packet | shared | adapt |
| member action evidence | member_specific | retain as member-specific projection |
| source readiness | mixed | split |
| exact-action meaning | mixed | split |
| member exact-choice effect | member_specific | replace with projection |
| policy episode identity and grouping | mixed | split |
| member episode direction | member_specific | replace with projection |
| policy families, mechanisms, and traits | shared | retain shared owner |
| member coverage | member_specific | retain member-specific owner |
| behavioral propositions | member_specific | retain member-specific owner |
| synthesis/conclusion planning | member_specific | retain member-specific owner |
| public wording | member_specific | retain member-specific owner |
| public presentation and rendering | member_specific | retain separately reviewed owner |

## Duplication and scale evidence

The pilot contains 37 unique exact actions. The cached Clerk records contain 16001 resolved member-action projections across 449 members, a measured semantic-reuse multiplier of 432.459459. A shared corpus would avoid 15964 duplicate action-meaning authoring instances relative to naive per-member interpretation. No time or cost estimate is inferred.

## Two-member proof

Member A is `F000477` (D); member B is `G000576` (R). The deterministic selector found 37/37 overlap. All 37 shared action digests were reused and member B regenerated zero meanings. Directional agreement/disagreement is 5/32.

The canonical pipeline compiled both members in one run with one unchanged shared-semantics object. Proposition counts were `{"F000477": 24, "G000576": 24}` and synthesis counts were `{"F000477": 1, "G000576": 0}`. Hard assertion failures: 0.

## Evidence-supported refactor boundary

- Split member-scoped universe discovery so exact-action eligibility is shared and member coverage is projected.
- Split operative-source readiness from member-action evidence readiness.
- Split accepted exact-action meaning from official member status and deterministic choice effect.
- Split shared episode identity/grouping from member episode direction.
- Retain the canonical compiler and downstream review/presentation separation.

## Data gaps

None blocking. All 37 governed Clerk rolls and the accepted frozen compiler input were available locally.

## Current-to-target decision table

| Current owner | Decision | Evidence basis |
|---|---|---|
| House Clerk action inventory / roll_calls | retain as shared canonical owner | session-aware exact action and full roll roster |
| Universe discovery | split into shared and member artifacts | member-scoped inventory currently owns exact-action domain membership |
| Source readiness | split into shared and member artifacts | operative source and member vote are combined |
| Action interpretation | split into shared and member artifacts | meaning and member effect share a record |
| Policy episode pipeline | split into shared and member artifacts | grouping and member direction share a record |
| Editorial Semantic IR compiler | retain; replace upstream mixed objects with projections/adapters | already accepts shared semantics plus member arrays |
| Synthesis/conclusion planning | retain as member-specific owner | consumes compiled member propositions |
| Public wording | retain as member-specific reviewed owner | downstream wording cannot create meaning |
| Public presentation/rendering | retain as separately reviewed owner | independent compiler, selector, and publication gates |
| Legacy member-scoped reusable-meaning identities | retire after migration | member namespace changes reusable object identities |

Smallest coherent next sequence: (1) shared-corpus boundary/refactor; (2) interpretability completeness and review; (3) two-member end-to-end staging qualification; (4) later cross-member rollout. M0 does not authorize or implement any of those milestones.

Proof subject SHA-256: `a7c10d8922b59b9f65c40ddc90668b00bccdadbe4c398018cd5a446b5cdd56e7`.
