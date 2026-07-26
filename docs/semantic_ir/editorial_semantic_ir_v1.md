# Editorial Semantic IR V1

Status: accepted semantic-reference contract with an isolated deterministic
compiler.

## Canonical boundary

Semantic IR V1 is the review contract between authoritative evidence and later
presentation. Its canonical result is a typed proposition graph, evidence-state
boundaries, and conclusion plan—not a paragraph. Example prose is an optional,
non-authoritative review aid.

The stage order is:

1. authoritative action;
2. exact-action eligibility;
3. action meaning;
4. episode;
5. policy family;
6. structural metadata and policy traits;
7. member action and coverage;
8. behavioral proposition;
9. synthesis proposition;
10. coverage, method, and source/render boundaries;
11. conclusion plan and presentation ownership;
12. render plan.

Every later stage consumes stable identities and decisions from earlier stages.
It may select, relate, omit, or render them, but may not reinterpret them.

## Explicit semantic roles

Behavioral propositions describe what a member did on eligible substantive
actions. Their types are `trajectory`, `repeated_pattern`, and
`notable_choice`. Each behavioral proposition has exactly one public analytical
presentation target:

- `repeated_patterns`;
- `policy_trajectories`;
- `other_notable_choices`.

Synthesis propositions derive a conclusion from behavioral propositions.
`mechanism_divide`, `uniform_direction`, `no_common_throughline`, and
`interpretive_boundary` are synthesis types. They may target
`meaningful_limitations`, `conclusion_only`, or `omitted`; the reviewed
mechanism-divide and no-common-throughline cases use `conclusion_only`. They do
not displace their supporting behavioral propositions.

Coverage boundaries represent known evidence states such as Present, Not
Voting, missing evidence, outside service, or a partial episode. They are not
behavioral propositions and target `coverage_note`.

Method boundaries contain counting, episode-grouping, exact-action, and
context/control-exclusion rules. They target `method_note` and cannot appear as
findings.

Source/render constraints are shared member-neutral restrictions on what
available sources and later rendering can support. They target `source_note`.
Rendering cannot manufacture an opposing argument, fill a source gap, or add
analytical meaning.

The complete presentation-target vocabulary is:
`repeated_patterns`, `policy_trajectories`, `other_notable_choices`,
`meaningful_limitations`, `conclusion_only`, `coverage_note`, `method_note`,
`source_note`, and `omitted`. V1 behavioral propositions use only the three
analytical targets; the remaining values keep non-behavioral semantic objects
explicit without forcing them into a public section.

## Shared, member, and composition layers

Shared legislative semantics contain canonical actions, exact-action domain
eligibility, claim/source references, action meaning, legislative stage,
structural metadata, episodes, policy families, policy traits, trait
relationships, shared review dependencies, and source/render constraints.
These fields are member-neutral.

Action-meaning and policy-trait IDs may resolve to referenced reviewed dossier
contracts rather than being copied into each case. Typed `policy_traits`,
`trait_relationships`, `shared_review_dependencies`, and
`source_render_constraints` records are available when a case must introduce
or expose one.

Member semantics contain exact action status, service status, evidence status,
the derived coverage contract, and a derived review route. Member and party
fields provide identity/context only and cannot change the shared semantic
result.

Composition semantics contain the conclusion plan, typed presentation
ownership, coverage boundaries, method boundaries, intentionally omitted
sections, notes, prohibited claims, and a render plan that cannot add analysis.

## Compiler architecture and data boundary

`backend/app/semantic_ir/compiler.py` is the canonical V1 semantic compiler. It
is pure, dependency-light, and file-agnostic. A test harness or authoring tool
loads a case, calls `project_compiler_input`, and then passes the resulting
object to `compile_semantic_ir`.

The projection contains only:

- case scope and structured focused-fixture scope, when applicable;
- reviewed shared actions, eligibility, meaning references, stages, structural
  metadata, episodes, families, policy traits and trait relationships;
- shared review dependencies and source/render constraints;
- exact member action, service, and evidence states.

Reviewed `policy_traits.action_ids` state which actions instantiate a
member-neutral trait. This is authoritative shared meaning, not a member
proposition. A focused fixture may identify included and limiting trait
references through `compiler_scope`; every other accepted action is still
accounted for as outside that focused assertion.

The projection rejects expected-output fields, including coverage, proposition
graphs, composition, action accounting, external review decisions, and review
routes. Normal compilation never reads an accepted-reference file. From the
input-only object, the engine derives coverage, trajectories, repeated patterns,
residual notable choices, accepted synthesis types, coverage and method
boundaries, complete action accounting, conclusion membership, presentation
ownership, and deterministic review routing.

Source/render constraints remain authoritative pass-through constraints. Exact
coverage and method prose, prohibited-claim wording, example prose,
intentionally omitted-section wording, and public section ordering remain
non-authoritative presentation inputs; reference comparison does not pretend
that the compiler inferred those words.

Compiler proposition IDs are stable hashes of semantic structure. Reference
comparison therefore uses semantic identity—role, type, direction, evidence,
traits, target, relevance, and relationships—rather than requiring an
authoring-era proposition label.

## Case scope and completeness

Every development case declares one scope:

- `full_record`: the graph represents all accepted in-scope actions;
- `focused_invariant_fixture`: the graph tests a declared invariant and must
  state which unrelated semantics are intentionally outside the fixture.

For every accepted action, `action_accounting` records either:

- at least one behavioral proposition containing the action; or
- an explicit non-proposition reason such as Present, Not Voting, missing
  evidence, outside service, or exclusion by a declared focused-fixture
  boundary.

Full-record cases must account for every accepted action exactly this way.
Rejected and context-only actions never satisfy or inflate that requirement.

## Coverage contract

Coverage is computed only over exact-action-eligible substantive actions and
records:

- `eligible_substantive_actions`;
- `context_only_control_actions`;
- `in_service_eligible_actions`;
- `resolved_eligible_actions`;
- `directional_yes_no_positions`;
- `present_actions`;
- `not_voting_actions`;
- `missing_evidence_actions`;
- `outside_service_actions`;
- `complete_episodes`;
- `partial_episodes`.

Context-only, procedural, mixed-measure, and rejected eligibility inputs remain
available for method review but do not enter the substantive denominator.
Present and Not Voting are resolved, known, and non-directional.

## Identity rules

- Action IDs use `house:{congress}:{session}:{roll}` for this corpus.
- Episode and policy-family IDs reuse existing corpus IDs where available.
- Case IDs do not encode member names.
- Proposition meaning is defined by role, type, evidence identities, direction,
  traits/mechanisms, presentation target, and relationships—not exact prose.
- Reordering actions, changing titles, or changing member/party identity cannot
  change shared semantics or proposition selection for identical evidence.

## Universal invariants

1. Member vote direction cannot alter eligibility, episode identity, or family.
2. Member and party identity cannot alter semantics for identical evidence.
3. Parent-measure context cannot establish exact-action eligibility.
4. Structural metadata is distinct from policy traits.
5. Multiple stages of one legislative event may form one episode.
6. Separate proposals remain separate episodes within one policy family.
7. A trajectory requires multiple actions within one episode.
8. A repeated pattern requires multiple independent episodes.
9. Present and Not Voting are neither support nor opposition.
10. Known coverage cannot use generic unknown-state language.
11. Only section-rendered behavioral propositions have the one-primary-section
    invariant.
12. Synthesis, coverage, method, and source/render objects do not require a
    public analytical section.
13. Tied material patterns cannot be silently omitted.
14. Every accepted full-record action has behavioral evidence or an explicit
    non-proposition reason.
15. Rendering cannot add analytical meaning.
16. Shared novelty is reviewed once at the shared layer.
17. Approval, production eligibility, benchmark status, and publication remain
    separate gates.

## Evidence and review states

`official_record_resolved` means the authoritative member action is known. It
does not confer semantic acceptance. `missing`, `source_unresolved`, and
`conflicting` remain distinct. Present and Not Voting are resolved
non-directional statuses.

The 12 Phase A development cases are externally accepted as
`accepted_semantic_reference` records in the
`accepted_semantic_reference_corpus` at
`accepted/development_cases.json`. This is semantic-reference acceptance only.
It does not confer public editorial approval, benchmark promotion outside this
contract, production eligibility, persistence authority, publication, registry
inclusion, runtime adoption, or deployment. The historical candidate review
packet preserves the pre-acceptance review evidence.

Held-out files still contain inputs and questions only; expected graphs and
conclusions remain excluded and unevaluated.

## Validation tiers

Only the semantic loop is implemented: schema-shape checks, accepted-reference
and held-out integrity, stable identities, evidence references, hierarchy, the
separated coverage contract, role/presentation rules, action accounting, all 12
compiler comparisons, and targeted invariance and anti-overfitting tests.

The domain loop remains proposed: full domain member/vector inputs and derived
fixtures. The release loop remains proposed: runtime, frontend, database,
broad regression, and production-oriented validation.

Run the implemented loop from the repository root:

```powershell
python scripts/validate_editorial_semantic_ir.py
python scripts/compare_accepted_semantic_references.py
python -m unittest backend.tests.test_editorial_semantic_ir
```
