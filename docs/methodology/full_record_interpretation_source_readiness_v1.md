# Full-Record Interpretation Source Readiness V1

## Purpose and authority

This contract determines whether official evidence for each action in an
already-authorized full issue universe is mechanically ready to enter a later,
separately authorized action-interpretation stage.

Source readiness establishes no action meaning, support/opposition direction,
episode, proposition, Semantic IR conclusion, synthesis, public wording,
publication eligibility, or persistence authority. Every downstream authority
flag is closed in the artifact.

The evaluator in `backend/app/etl/full_record_source_readiness.py` is
domain-neutral. Member, issue, Congress, cutoff, universe, and source identities
are supplied by a milestone-specific builder. The closed Draft-07 artifact
contract is `full_record_interpretation_source_readiness_v1.schema.json`.

## Exact universe binding

A readiness artifact must bind an approved detached universe-authority receipt,
the approved universe proposal, its selection, and its source inventory. The
action IDs and action-set digest must match the authority receipt exactly. An
outside, duplicate, missing, or reordered action fails independent validation.

Readiness never changes universe membership. An unresolved action outside the
approved universe remains outside this artifact.

## Evidence roles

Every action has explicit source bindings for three independent roles:

1. `member_action_evidence` proves the official member action and roll identity.
2. `exact_action_identity_and_stage_evidence` proves the exact measure or
   amendment and the House decision stage.
3. `operative_content_interpretation_input` supplies the exact operative object
   a later interpreter may inspect.

A source may satisfy more than one role only when its official content actually
does so. Parent-measure metadata cannot satisfy the operative-content role for
an amendment. Title, policy-area, sponsor, cosponsor, party, and generic bill
metadata cannot establish action meaning.

## Stage-compatible operative evidence

- Whole House measures require the House-passed text for the recorded passage
  stage. A failed passage action requires the exact text placed before the
  House, not a later version.
- Amendments require an exact amendment identity bound to the roll plus official
  amendment purpose, description, or text. Parent-measure content is
  insufficient.
- Resolutions require the exact operative resolution text. For a failed
  resolution, the introduced text may be stage-compatible when official action
  evidence shows that was the object before the House.
- Senate-origin measures require proof of the version before the House. A House
  amendment in the nature of a substitute requires an `eah` text; passage
  without House amendment requires the Senate-engrossed (`es`) text.

## Raw provenance and neutral projections

Official raw bytes are stored under the governed source-readiness evidence root
with SHA-256 identities. A separate neutral projection binds the action, source,
stage, version, date, member action, official description, and raw digest.

Neutral projections exclude sponsor, cosponsor, party, action-meaning,
support/opposition, episode, proposition, synthesis, public-language, and other
semantic fields. Raw official records may contain such source-native metadata;
that raw provenance is not itself an interpretation input projection.

## Closed readiness states

Each approved action receives exactly one state:

- `ready_for_action_interpretation`
- `blocked_missing_operative_content`
- `blocked_stage_mismatch`
- `blocked_exact_action_identity`
- `blocked_source_conflict`
- `blocked_insufficient_context`

The evaluator uses deterministic blocker precedence: source conflict, exact
identity, stage mismatch, missing operative content, then insufficient context.
No desired aggregate or later conclusion may influence readiness.

## Validation

The independent validator recomputes universe bindings, file and projection
digests, official source roles, Clerk member actions, exact roll/date matches,
amendment identities and purpose/description, XML operative bodies, text-version
compatibility, aggregate counts, packet digests, and the non-authorizing current
state. Adversarial tests require fail-closed behavior for identity, stage,
content, conflict, digest, universe-membership, duplication, and semantic or
political leakage failures.
