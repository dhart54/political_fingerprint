# Full-Record Issue Interpretation Contract V1

## Status and authority

This contract defines how Political Fingerprint expands benchmark-proven
interpretation across a representative's defined issue record and decides
whether a final issue-level public claim is eligible.

The closed machine-readable contract is
`full_record_issue_interpretation_v1.schema.json`. Deterministic validation is
implemented by `scripts/validate_full_record_issue_interpretation.py`.
Editorial Semantic IR V1 remains the canonical meaning layer; this contract
defines the evidence universe, review completion, and claim authority supplied
to a full-record Semantic IR compilation. It does not replace or reinterpret
accepted Semantic IR outcomes.

## Four independent axes

These axes must remain independent. `reviewed_conclusion` describes semantic
quality inside supplied reviewed evidence; it never establishes the size or
completion of that evidence universe.

Workflow review routing is independent as well. A compiled
`human_exception_required` route records that exceptional review was necessary;
it is not equivalent to `blocked` and may be completed only by an exact,
content-bound review-resolution chain. A `blocked` route, missing evidence,
unresolved service, partial episodes, or a source block on any accepted
substantive action cannot be approved away. Context-only and rejected actions
remain visible controls but do not enter the substantive denominator.

### Semantic tier

- `reviewed_conclusion`: the reviewed evidence supports the established
  conclusion shape and quality.
- `developing_read`: a bounded analytical plan exists but does not meet the
  reviewed-conclusion shape.
- `non_directional_or_limited_evidence`: the supplied evidence is resolved
  non-directional or too limited for a safe analytical plan.
- `receipts_only`: no analytical claim is authorized.

This preserves the existing public-presentation vocabulary and meaning.

### Review scope

- `benchmark_sample`: an immutable accepted reference slice selected to prove
  specific invariants.
- `bounded_partial_record`: a declared portion of an issue record that is not a
  benchmark and is not the complete defined issue universe.
- `full_defined_issue_record`: the content-addressed complete issue universe for
  the declared member, issue, and Congress scope.

### Review completion state

- `not_started`
- `in_progress`
- `blocked`
- `complete`

Completion says whether every action in the *declared universe* has a governed
disposition. A seven-action benchmark can be complete within that sample while
remaining categorically incomplete as a full defined issue record. The separate
scope axis prevents that state from being mistaken for full-record completion.

### Public claim class

- `vote_record_only`
- `reviewed_sample_finding`
- `full_issue_synthesis`
- `full_review_no_common_throughline`
- `full_review_no_safe_synthesis`

A `reviewed_conclusion` in a `benchmark_sample` may support only a
`reviewed_sample_finding`, not a full-record claim.

## Review-friendly substantive action

An action is review-friendly only when every condition below is true:

1. it has a stable canonical action identity;
2. the member is confirmed in service for the action;
3. the official member action is resolved as `Yea`, `Nay`, `Present`, or
   `Not Voting`;
4. the exact action—not merely a parent measure—is eligible for the issue;
5. official evidence is sufficient to explain what the chamber was deciding;
6. authoritative vote provenance is present;
7. authoritative exact-action meaning provenance is present; and
8. no unresolved or conflicting source state blocks interpretation.

The validator derives `is_review_friendly` from these closed fields. Authoring
cannot assert it independently.

`Yea` and `Nay` may contribute directional evidence. `Present` and `Not Voting`
are resolved review-friendly actions but remain non-directional. Procedural and
context-only actions remain visible and non-counting. Expressive nonbinding
actions are a separate visible context class: they record what a chamber
expressed without creating, amending, funding, directing, or otherwise changing
operative law or administration. They are not procedural, remain non-counting,
and cannot enter synthesis or support/opposition accounting. Verified
`not_yet_serving` and `no_longer_serving` actions remain outside service.
Missing, unresolved, conflicting, and source-constraint-blocked actions retain
their exact states.

Party, raw vote direction, keywords, title, salience, vote volume, or fit with
an emerging conclusion cannot change review-friendliness, issue-universe
identity, review scope, or episode identity.

## Content-addressed issue universe

Every review declares an immutable issue-universe snapshot. Its action
membership is the only allowed accounting denominator. For benchmark and
partial reviews, the local V1 snapshot digest remains SHA-256 over UTF-8
compact, key-sorted JSON with this exact shape:

```json
{
  "action_ids": ["sorted canonical action IDs"],
  "congress_scope": ["sorted Congress numbers"],
  "issue_id": "ISSUE_ID",
  "member_id": "BIOGUIDE_ID",
  "review_scope": "review scope"
}
```

Array order in an input manifest therefore cannot change the universe identity.
Adding or removing an action changes the digest. A new action invalidates a
previously complete snapshot until the snapshot digest, exact accounting, and
any affected episode membership are updated and re-reviewed.

The universe definition must say what inclusion rule and temporal boundary it
uses. A benchmark universe must explicitly say that it is not the complete
issue record.

`full_defined_issue_record` authority cannot be authored by the review manifest.
It requires a separate `full_issue_universe_manifest_v1` plus a detached
`full_issue_universe_authority_receipt_v1`. The manifest binds member, issue,
Congress/session/time, chamber and service boundaries, inclusion/exclusion
rules, acquisition/source-manifest identities and digests, exact action
membership and count, source commit, action-set digest, and a digest of the
complete universe subject. The detached receipt repeats that subject under
`full_issue_universe_review_authority_v1`, repeats the exact closed boundary
definition and digest, and explicitly approves it as the complete issue
universe.

The review stores only content-addressed references. Validation loads both
artifacts, compiles their closed Draft-07 schemas, recomputes every file,
boundary, action-set, and subject digest, verifies source manifests, and checks
the receipt authority and binding. Recomputing a local review digest or changing
`review_scope` cannot promote a benchmark. Test-only authority is accepted only
through an explicit in-process test flag; the repository validation CLI cannot
use it. This milestone creates no Foushee full-record universe.

## Complete action accounting

Every action ID in the snapshot appears exactly once in `action_accounting`,
and no outside action may appear. Each receives one closed disposition:

- `interpreted_substantive_directional`
- `interpreted_substantive_non_directional`
- `pending_interpretation`
- `procedural_context`
- `expressive_nonbinding_context`
- `exact_action_ineligible`
- `outside_service`
- `missing_evidence`
- `source_unresolved`
- `source_conflicting`
- `source_constraint_blocked`

For each interpreted substantive action, the manifest requires:

- a unique action-interpretation ID and action-meaning ID;
- exact-action meaning;
- official member action;
- resolved evidence and in-service status;
- authoritative vote sources;
- authoritative exact-action meaning sources;
- one stable episode identity;
- review state; and
- an interpretation receipt or equivalent governed provenance; and
- a digest over that complete action-interpretation subject.

The disposition must follow the evidence state. A review-friendly `Yea` or `Nay`
is directional. A review-friendly `Present` or `Not Voting` is
non-directional. Before declared-universe completion, a review-friendly action
may use `pending_interpretation`; that disposition is forbidden when completion
is `complete`. A source-conflicting action cannot be relabeled missing or
silently removed. No action may disappear because it weakens or contradicts an
emerging pattern.

When more than one non-interpreted state is true, V1 assigns the single
disposition in this deterministic precedence: verified outside service;
procedural context; expressive nonbinding context; exact-action ineligibility; source conflict; source
constraint; missing evidence; then unresolved source or identity. Orthogonal
detail remains present in `review_friendliness`; precedence prevents duplicate
accounting without erasing the underlying state.

`full_record_action_accounting=passed` is reserved for a complete
`full_defined_issue_record`. Exact accounting of a benchmark sample remains
valid but does not pass the full-record gate.

## Cross-domain exact actions

An exact action may belong to more than one issue only when its own operative
choice independently changes a substantive mechanism in each named domain.
Membership is invariant to the member's vote direction and party.

For Justice & Public Safety, an otherwise National Security FISA action may be
included when the exact House choice directly changes surveillance authority;
FISC or other court authority; warrant, query, collection, or review powers;
law-enforcement use or oversight of surveillance; or civil-liberty protections
attached to those powers. The record must retain explicit National Security
membership and explicit cross-domain metadata. Any later Justice interpretation
is limited to surveillance, court authority, and attached civil-liberty
protections; it cannot establish a general policing, criminal-law, or domestic
public-safety position.

## Episode completion

A policy episode is one legislative event and may contain one or multiple
related actions. Multiple stages of that event count as one episode for
breadth. Separate proposals remain separate episodes even when they share a
policy family.

Action accounting is the sole authority for action meaning. Episodes carry only
the action ID, action-interpretation ID, and interpretation digest. They cannot
author a second meaning. The validator resolves each reference to exactly one
interpreted action and verifies identity and digest equality.

Every in-scope substantive action also declares
`episode_membership_state=established` with exactly one episode, or
`episode_membership_state=unresolved` with a governed reason and no episode.
Unresolved membership blocks review completion and synthesis. An established
action remains in its episode even when evidence is missing, unresolved,
conflicting, constraint-blocked, non-directional, or pending.

Every episode requires:

- stable episode identity;
- all related in-scope actions known in the declared universe;
- an action list and a complete chronological action order;
- a concrete policy question;
- exact content-addressed action-interpretation references;
- the member record across every episode action;
- a `directional_support`, `directional_opposition`, `mixed`,
  `non_directional`, or `unresolved` outcome;
- contrary or limiting evidence;
- official source references and source-completeness state; and
- an explicit `complete` or `partial` completion state.

An open episode action must appear in `unresolved_action_ids`; the validator
derives the episode as `partial`. A source gap also makes source completeness
partial, while an action awaiting interpretation may leave sources complete.
Every established substantive action belongs to exactly one episode whether or
not it is currently interpretable.

Public episode ordering is deterministic: episodes are ordered by latest action
date, newest first. Actions within an episode are chronological, oldest first.
Policy-mechanism ordering is not a V1 default and may only be introduced later
as explicit reviewed presentation metadata. React may not infer it.

## Full-record synthesis eligibility

The validator derives `full_issue_synthesis_eligible`; stored booleans and
benchmark labels are non-authorizing. A full synthesis is eligible only when:

- the issue universe is nonempty, defined, and content-addressed;
- `review_scope=full_defined_issue_record`;
- declared-universe review completion is `complete`;
- full-record action accounting passes;
- every review-friendly action is interpreted;
- every interpreted action belongs to exactly one complete episode;
- no partial episode or unresolved, conflicting, or constraint-blocked source
  state remains in an eligible synthesis;
- all interpreted episode outcomes are supplied to full-record Semantic IR;
- contradictory and mixed evidence is retained;
- source boundaries are resolved;
- a detached full-record semantic-validation receipt passes; and
- a detached content-bound full-record human approval receipt passes.

The explanatory `semantic_validation` and `human_editorial_review` fields never
authorize these gates. A full public claim must reference:

- a `full_record_semantic_artifact_v1` bound to the external universe, exact
  action-accounting digest, episode-set digest, propositions, conclusion plan,
  semantic tier, synthesis outcome, its own semantic-subject digest, and an
  exact digest-addressed canonical compiled Editorial Semantic IR artifact;
- a `full_record_semantic_validation_receipt_v1` binding that artifact and its
  accounting/episode digests to the canonical validator with passed status and
  zero blockers; and
- a `full_record_synthesis_approval_receipt_v1` binding the universe, semantic
  artifact, validation receipt, outcome, public claim class, wording, mappings,
  limitations, provenance, reviewer authority, and decision.

Validation loads every artifact, recomputes its digest, revalidates the canonical
compiled IR, and requires its exact member, action universe, proposition
identities, conclusion plan, and synthesis outcome to match. A changed universe,
action, episode, semantic result, outcome, claim class, wording, mapping,
limitation, or provenance invalidates the chain.

Production eligibility, publication activation, registry selection, deployment,
and merge remain separate later gates.

Semantic tier, human approval, benchmark status, production eligibility, and
publication activation are independent atomic states. No state implies or
silently promotes another.

The reviewed outcome may be:

- `repeated_pattern`;
- `mechanism_divide`;
- `uniform_direction`;
- `mixed_or_qualified`;
- `no_common_throughline`; or
- `no_safe_synthesis`.

`no_common_throughline` is a valid eligible full-record synthesis; a complete
review does not have to produce a neat pattern. `no_safe_synthesis` is a valid
reviewed completion outcome but sets `full_issue_synthesis_eligible=false` and
uses the distinct `full_review_no_safe_synthesis` claim class.

Raw Yea/Nay totals, party, bill-title keywords, salience, and vote volume cannot
directly produce or select the final synthesis.

## Semantic-tier and public-claim compatibility

| Public claim class | Scope and completion | Compatible semantic tier | Analytical teaser |
| --- | --- | --- | --- |
| `vote_record_only` | any | any internal tier | forbidden |
| `reviewed_sample_finding` | benchmark or bounded partial | `reviewed_conclusion` or `developing_read` | scope-bounded only |
| `full_issue_synthesis` | externally authorized full scope, complete | `reviewed_conclusion` | allowed after external gates |
| `full_review_no_common_throughline` | externally authorized full scope, complete | `reviewed_conclusion` | only the externally validated outcome |
| `full_review_no_safe_synthesis` | externally authorized full scope, complete | `receipts_only` or `non_directional_or_limited_evidence` | forbidden |

The no-common-throughline path is supported by the isolated synthetic authority
proof and is not inferred from the current Foushee benchmark. A
`receipts_only` tier can never authorize an analytical synthesis or
no-common-throughline claim.

## Benchmark role

Accepted gold slices:

- prove specific semantic, evidence, hierarchy, editorial, and presentation
  invariants;
- provide reviewed reusable examples for expansion;
- remain immutable benchmark evidence;
- may expose valid findings within their bounded scope;
- do not satisfy full-record scope or completion;
- do not determine which other actions must agree with them; and
- cannot be used as templates to force new evidence into an accepted finding.

Expansion reruns the general methodology over the newly defined complete issue
universe. New evidence may strengthen, narrow, contradict, replace, or eliminate
the benchmark-sample conclusion. Benchmark status has no effect on
review-friendliness or full-record eligibility.

## Current Foushee Justice state

The machine-readable record is
`../editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json`.
It separates three truths:

1. **Historical publication truth.** The human-approved seven-action,
   five-episode artifact was successfully activated on 2026-07-29 and remains
   publication-active. The activation receipt and production facts are
   unchanged.
2. **Semantic validity within the reviewed sample.** Its semantic tier is
   `reviewed_conclusion`, its review scope is `benchmark_sample`, the declared
   seven-action sample is completely accounted for, and its public claim class
   is `reviewed_sample_finding`.
3. **Future full-record product eligibility.** The exact 37-action V2
   `full_defined_issue_record` for F000477, `JUSTICE_PUBLIC_SAFETY`, Congress
   119 is established through the declared July 23, 2026 cutoff by a detached,
   content-bound human authority receipt. That decision establishes universe
   membership only. Action interpretation and episode construction have not
   started; full-record Semantic IR validation and synthesis remain absent;
   production persistence is not authorized; and
   `full_issue_synthesis_eligible=false`.

This classification does not rewrite, invalidate, deactivate, or mutate the
active artifact, its approved wording, its approval receipt, its publication
receipt, or its incident history.

## Frontend-facing state for the next milestone

Frontend Pass A may eventually consume only backend-supplied values for:

- `review_scope`
- `review_completion_state`
- `public_claim_class`
- `total_recorded_actions`
- `review_friendly_actions`
- `interpreted_actions`
- `unresolved_actions`
- `procedural_context_actions`
- `present_actions`
- `not_voting_actions`
- `complete_episode_count`
- `partial_episode_count`
- `full_issue_synthesis_eligible`
- `benchmark_sample_available`
- `conclusion_teaser`, only when valid for its explicit scope

All counts are relative to the declared content-addressed universe. React must
not infer these values from raw rolls or party metadata.

The closed public labels are:

- **Reviewed benchmark sample**
- **Full review complete**
- **Full issue interpretation available**
- **No common throughline found**
- **No safe synthesis available**
- **Vote receipts available**

`Full review complete` is valid only for a complete
`full_defined_issue_record`. `Full issue interpretation available` requires an
eligible full synthesis. The no-common-throughline and no-safe-synthesis labels
use their distinct public claim classes.

## Validation and governance

Validation checks Draft-07 schema conformance plus cross-field invariants that
JSON Schema alone cannot prove:

- exact one-time action accounting;
- derived review-friendliness and disposition;
- source and interpretation provenance;
- episode membership, completeness, ordering, and member-record integrity;
- content-addressed universe identity;
- derived synthesis blockers and public eligibility;
- frontend count and label truth;
- benchmark non-authority; and
- protected benchmark, approval, publication, and incident file digests.

`scripts/check_full_record_terminology.py` validates current structured labels
against scope, completion, and authority, and rejects governed sentence patterns
that equate a benchmark, gold slice, reviewed sample, or seven-action sample with
a complete or representative-wide record. Clearly dated historical and archived
evidence is exempt only through an explicit path allowlist.
