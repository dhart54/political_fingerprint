# Full Issue Interpretation Source Readiness V1

## Purpose

This contract mechanically determines whether every action in an externally
authorized full issue universe has sufficient official source and identity
evidence to be supplied to a later interpreter. It does not interpret an
action, establish an episode, create semantic authority, or authorize
persistence or publication.

The closed machine-readable contract is
`full_issue_interpretation_source_readiness_v1.schema.json`. The F000477 Justice
V1 artifact is detached from both the approved universe and the public
seven-action benchmark.

## Inputs

The builder accepts only the approved V2 universe manifest, detached M1
authority receipt, V2 discovery/source/configuration/comparison records,
governed official-source files or projections, and neutral source-sufficiency
and action-identity methodology.

Party, accepted benchmark interpretations and conclusions, Semantic IR,
presentation wording, episodes, propositions, synthesis outcomes, other action
interpretations, and secondary or partisan descriptions are excluded. The
artifact records this allowlist and exclusion list explicitly.

## Mechanical readiness

An action is ready only when it is one of the exact approved actions; its stable
identity, member action, exact measure or amendment, and House stage are
resolved; vote evidence and exact-action evidence are present and digest-valid;
narrower actions do not rely on a parent measure alone; required governed files
or projections and explicit versions exist; at least one stage-compatible
mechanism-bearing official source is present; no conflict or source constraint
remains; all paths and source types are allowed; applicable cross-domain scope
is complete; and no semantic material enters the packet.

The verifier derives criteria, blockers, and the primary state. Authors cannot
assert readiness independently. Blocker precedence is:

1. semantic leakage;
2. exact-action identity;
3. parent-only evidence;
4. wrong text version;
5. source digest;
6. source conflict;
7. source constraint;
8. cross-domain scope; and
9. missing operative-content source; and
10. missing official source.

All applicable blocker codes remain visible even though one deterministic
primary state is selected.

## Evidence separation

Every action has three independently populated roles:

1. `member_action_evidence` resolves Foushee's recorded action;
2. `exact_action_identity_and_stage_evidence` resolves the exact House choice
   and legislative stage; and
3. `operative_content_interpretation_input` supplies stage-compatible official
   legislative text or exact amendment/rule material.

Identity-and-stage evidence never satisfies the operative-content role. A bill
title, policy area, generic bill page, or generic `/v3/bill` response is not
mechanism-bearing. Passage and suspension actions require the exact House
engrossed text or a verified stage-equivalent official version. Amendments
require exact amendment material rather than parent-bill context alone.

Raw official files are SHA-256 content-addressed. Canonical Clerk and
Congress.gov projections use the closed `neutral_m3_source_projection_v1`
contract and are independently rehashed by the verifier. Raw provenance and
neutral projections are bound separately. Generic Congress bill metadata may
remain as raw provenance but is never M3-input eligible; no sponsor, cosponsor,
party, benchmark, presentation, episode, or synthesis field is permitted in a
neutral projection.

Availability, conflict, constraint, path, digest, source-type, and role states
are derived from the actual manifest, governed files, neutral projections,
canonical action identity, and stage compatibility. They are not authorable
readiness assertions.

## Cross-domain constraints

Actions `house:119:2:155` and `house:119:2:221` must retain both
`JUSTICE_PUBLIC_SAFETY` and `NATIONAL_SECURITY` membership plus these exact
limitations:

- `surveillance_authority`
- `fisc_and_court_authority`
- `civil_liberty_protections`

These fields constrain a future interpreter. They do not state a Justice
interpretation.

## Authority boundary

`complete_ready` means every authorized action has one passing source-readiness
record. `complete_blocked` means accounting is complete but at least one source
requirement remains blocked. Neither state claims human review, accepted action
meaning, episode authority, Semantic IR, synthesis eligibility, persistence
eligibility, publication eligibility, or permission to begin M3.
