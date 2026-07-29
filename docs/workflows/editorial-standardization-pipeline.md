# Editorial standardization pipeline

## Purpose

This workflow turns source-grounded legislative evidence and accepted semantic
contracts into scalable, fail-closed member interpretation and presentation.

Deterministic validation establishes contract conformance. It does not by itself
prove political truth, factual perfection, motive, human approval, production
eligibility, or publication authority.

The legislative action dossier is researched once and reused across
representatives. The system must not independently rewrite the same bill facts,
effects, arguments, or sources for every member.

Member-specific data is limited to authoritative member action status, exact
coverage, and the bounded interpretation derived from shared legislative
semantics.

## Canonical semantic boundary

Editorial Semantic IR V1 is the contract between shared evidence and later
presentation:

- `docs/semantic_ir/editorial_semantic_ir_v1.md`
- `docs/semantic_ir/editorial_semantic_ir_v1.schema.json`

The canonical output is:

- shared action eligibility and meaning;
- episode and policy-family hierarchy;
- structural metadata and policy traits;
- exact member action and coverage states;
- behavioral propositions;
- synthesis propositions;
- coverage, method, and source/render boundaries;
- action accounting;
- conclusion plan;
- presentation targets.

Exact prose is not canonical.

Later stages may select, relate, omit, or render established semantic objects.
They may not reinterpret earlier-stage meaning or add analytical claims.

All newly commissioned work enters through
`backend.app.semantic_ir.pipeline.run_editorial_pipeline`. That orchestration
calls the independently usable pure compiler exactly once, validates compiled
IR, and only then prepares review, presentation, or optional inert persistence
proposal payloads. The obsolete generators were deleted in Editorial Hard
Cutover V1. Their frozen outputs remain historical evidence and are validated
directly rather than replayed.

Representative-level expansion from an accepted sample to a complete issue
record also follows
`docs/methodology/full_record_issue_interpretation_v1.md`. Semantic tier,
review scope, review completion, and public claim class remain separate.
Accepted benchmark cases calibrate the compiler but do not define or complete a
representative's full issue universe.

## Three review checkpoints

### Checkpoint 1: shared semantic corpus

Review only member-neutral meaning:

- exact-action eligibility;
- action meaning and sources;
- legislative stage;
- episode hierarchy;
- policy families;
- structural metadata;
- policy traits and relationships;
- shared source constraints;
- supported absences and conflicts.

No member conclusion or frontend review occurs until this checkpoint is stable.

A change here invalidates affected downstream proposition and presentation
reviews.

### Checkpoint 2: proposition-shape calibration

Run the necessary member and synthetic inputs, but review representative semantic
shapes rather than every member.

Review:

- exact member action status;
- coverage;
- behavioral propositions;
- synthesis relationships;
- action accounting;
- conclusion plan;
- presentation ownership;
- review route.

Humans should review:

- each novel proposition shape;
- each genuine exception;
- shared unresolved dependencies once;
- a stratified audit sample.

Humans should not rereview every member whose proposition graph matches an
already accepted shape.

### Checkpoint 3: presentation calibration

Only after semantic graphs are stable, review a bounded set of rendered cases
covering relevant structures such as:

- consistent or uniform direction;
- mechanism divide;
- mixed within-episode trajectory;
- limited coverage;
- Present and Not Voting;
- tied patterns;
- notable choices;
- meaningful limiting evidence.

Presentation review concerns clarity, grammar, density, caveat placement,
accessibility, and visual hierarchy. It must not silently reopen upstream
semantic meaning.

## Generation order

1. Ingest and canonicalize the legislative action.
2. Build or reuse the member-neutral action dossier.
3. Resolve the exact action, stage, source, and claim mappings.
4. Decide exact-action domain eligibility independently from parent context.
5. Group stages of one legislative event into an episode where supported.
6. Keep separate proposals as separate episodes.
7. Optionally relate episodes through a policy family without merging them.
8. Resolve structural metadata separately from policy traits.
9. Resolve shared review dependencies once at the shared layer.
10. Overlay each member's authoritative action status.
11. Calculate the Semantic IR coverage contract.
12. Build behavioral propositions:
    - trajectories;
    - repeated patterns;
    - notable choices.
13. Build conclusion-only synthesis where justified:
    - mechanism divides;
    - uniform-direction synthesis;
    - no-common-throughline synthesis;
    - interpretive boundaries.
14. Record coverage, method, and source/render boundaries outside the behavioral
    graph.
15. Account for every accepted action in full-record cases.
16. For a representative-level full issue review, validate the
    content-addressed issue-universe manifest, governed action dispositions, and
    complete or explicitly partial episode membership.
17. Supply every interpreted episode outcome, including contrary and mixed
    evidence, to the full-record Semantic IR compilation.
18. Derive full-record eligibility from scope, completion, source, semantic,
    and human-review gates; do not require a neat conclusion.
19. Build the conclusion plan and typed presentation targets.
20. Render bounded prose without adding meaning.
21. Select featured episodes upstream for presentation.
22. Compile `editorial_public_issue_presentation_v1` from compiled IR and
    separately reviewed wording without adding meaning. Fail closed to
    `receipts_only` unless all publication controls pass.
23. Run the validation tier appropriate to the change.
24. Route failures and genuine novelty.
25. Permit stratified auditing of passing slices.

## Semantic invariants

- Vote direction cannot alter action eligibility, episode identity, or
  policy-family identity.
- Member and party identity cannot alter semantics for identical evidence.
- Parent-measure context cannot establish exact-action eligibility.
- Structural metadata is distinct from policy traits.
- Multiple stages of one legislative event may form one episode.
- Separate proposals remain separate episodes within one policy family.
- A trajectory requires multiple actions within one episode.
- A repeated pattern requires multiple independent episodes.
- Present and Not Voting are neither support nor opposition.
- Known coverage cannot use generic unknown-state language.
- Only section-rendered behavioral propositions have one primary analytical
  section.
- Synthesis, coverage, method, and source constraints do not require an
  analytical section.
- Tied material patterns cannot be silently omitted.
- Every accepted full-record action contributes to behavioral evidence or has an
  explicit non-proposition reason.
- A benchmark sample cannot confer `full_defined_issue_record` scope,
  full-record completion, or a full-record public claim.
- Every action in a declared issue-universe snapshot has exactly one governed
  disposition; new action membership invalidates the prior snapshot digest.
- Every interpreted action belongs to exactly one complete or explicitly
  partial episode.
- Rendering cannot add analytical meaning.
- Shared novelty is reviewed once at the shared layer.
- Approval, gold status, benchmark status, production eligibility, promotion,
  publication, merge, and deployment remain separate gates.

## Evidence and absence states

Required action fields must contain sourced content or an explicit supported
absence state:

- `not_applicable`
- `not_material`
- `not_material_or_not_available`
- `adequate_official_argument_not_found`
- `source_unresolved`
- `pending_research`

`source_unresolved` and `pending_research` block publication eligibility.

One-sided official argument evidence stays one-sided. Render the supported side
and the supported absence note. Never invent symmetry.

Source handling preserves distinct states:

- source attached;
- claim mapped to a locator;
- claim supported under the dossier contract;
- human verified.

An attached source or mapping is not by itself proof of support or human
verification.

## Coverage and service boundary

Keep these distinct:

- eligible substantive actions;
- context-only or control actions;
- in-service eligible actions;
- resolved eligible actions;
- directional Yea/Nay positions;
- Present;
- Not Voting;
- missing evidence;
- unresolved service;
- outside-service actions;
- complete episodes;
- partial episodes.

Context-only, procedural, mixed-measure, and rejected actions remain available
for method review but do not inflate substantive denominators.

Year-only service metadata cannot establish action-date eligibility. When exact
dates are unavailable, an absent action remains missing evidence; presentation
convenience must not relabel it as outside service.

Service and evidence states are orthogonal. Only verified
`not_yet_serving` and `no_longer_serving` statuses count as outside service;
unresolved service remains separately counted and blocks the result. Typed
source/render effects—not parsed prose—determine whether a constraint blocks
behavioral propositions, limits argument rendering, or bounds cross-domain
attribution.

## Review routing

Every generated slice receives one quality-control route:

- `standard_generation_pass`
- `sampled_audit_candidate`
- `human_exception_required`
- `blocked`

These routes do not confer human approval, gold status, benchmark promotion,
production eligibility, publication, merge, or deployment.

### Standard generation pass

Use when:

- shared semantics are established;
- the proposition shape is established;
- coverage and action accounting are complete;
- all blocking and editorial-integrity checks pass.

### Sampled audit candidate

Use the same passing state, selected by a deterministic stratified quality rule.

### Human exception required

Use when:

- a new or unresolved policy trait or relationship is material;
- a new legislative action or evidence type is outside the established contract;
- authoritative meaning is genuinely contestable;
- a new proposition or synthesis shape is required;
- source support is one-sided or incomplete in a way requiring judgment;
- the contract can preserve the candidate safely but acceptance requires review.

Review shared novelty once at the shared layer rather than propagating duplicate
member exceptions.

### Blocked

Use for hard failures such as:

- unresolved or conflicting authoritative source evidence;
- representative leakage into shared evidence;
- action-direction or coverage contradiction;
- unsupported claim or invented argument;
- unrepresentable service status;
- invalid action accounting;
- hierarchy contradiction;
- publication-boundary failure;
- missing required official action source.

Do not weaken a rule or relabel a failure merely to keep the pipeline moving.

## Stratified quality sampling

Audit across:

- chamber;
- issue;
- Congress;
- action type;
- Yea, Nay, Present, and Not Voting;
- multi-action and single-action episodes;
- package and non-package actions;
- one-sided source evidence;
- consistent, divided, mixed, and limited-evidence conclusions;
- full-service and partial-service records;
- established and newly migrated proposition shapes.

Quality assurance combines accepted semantic fixtures, held-out evaluation,
property testing, mutation testing, targeted exception review, and stratified
sample audits. It does not depend on exhaustive human reading of every generated
card.

## Validation tiers

### Semantic loop

Use while authoring or correcting Semantic IR, candidate or accepted-reference
cases, compiler logic, action accounting, and coverage.

```powershell
python scripts/run_editorial_pipeline.py validate --tier semantic
```

The canonical command coordinates actual Draft-07 validation, corpus and receipt
integrity, all 16 accepted-reference comparisons, and the focused compiler,
property, input-only, and adapter-isolation tests.

This loop must not require frontend, browser, persistence, or production work.

### Domain loop

Use after changes affect a full issue domain.

Validate affected members, vectors, mutations, fixtures, and persistence
proposal for that domain.

For the current accepted-reference domains, run a bounded read-only replay
through the canonical pipeline:

```powershell
python scripts/run_editorial_pipeline.py validate --tier domain --domain <DOMAIN_ID>
```

The default does not prepare a persistence proposal or generate downstream
artifacts.

### Release loop

Use near merge when runtime, frontend, cross-domain, migration, persistence,
publication, or deployment behavior changes.

Do not run release validation after every small semantic correction.

```powershell
python scripts/run_editorial_pipeline.py validate --tier release
```

Use `--include-frontend` or `--include-persistence` only when those boundaries
actually changed. The command coordinates checks only and confers no production,
publication, merge, or deployment authority.

## Failure handling

Within an authorized milestone and established contract, continue autonomously
through safe correction and narrow regeneration.

When a gate fails:

1. preserve the failing input and exact rule result;
2. diagnose the owning layer:
   - shared evidence;
   - eligibility;
   - hierarchy;
   - member status or coverage;
   - proposition selection;
   - synthesis;
   - presentation;
   - validation;
3. correct the owning layer without weakening the rule, inventing evidence,
   hand-editing generated output, or changing publication state;
4. rerun the narrowest sufficient validation;
5. continue independent safe cases;
6. record the correction, remaining limitation, and review route.

A failed first output is not by itself a reason to stop. Stop when a true
repository stop condition remains after safe correction.

## Publication boundary

Reference, candidate, fixture, route, and validation labels are regression and
workflow metadata only.

Real content remains unapproved and non-public until separately authorized
decisions establish the required approval, production-eligibility, registry, and
publication state.

No semantic acceptance automatically authorizes:

- persistence to production;
- benchmark promotion;
- publication-registry inclusion;
- public selection;
- merge;
- deployment.
