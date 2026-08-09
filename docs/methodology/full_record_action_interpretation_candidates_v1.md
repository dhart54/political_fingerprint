# Full-Record Action Interpretation Candidates V1

## Purpose and authority

This contract generalizes the accepted Justice source-first candidate pattern for
a complete externally authorized issue universe whose actions have separately
passed or failed interpretation-source readiness. It produces detached human
review candidates. It does not accept action meaning or authorize any later
semantic or operational stage.

The closed schema is
`full_record_action_interpretation_candidates_v1.schema.json`. The generic
implementation is
`backend/app/etl/full_record_action_interpretation.py`.

## Required order

1. Validate the independently accepted issue universe and readiness artifact.
2. Preserve the exact universe denominator.
3. Build meaning from the exact recorded action and its accepted operative
   source.
4. Only after meaning exists, derive the member-position effect from the
   authoritative action and exact House stage.
5. Bind every claim to content-addressed official evidence.
6. Route every candidate to human action-meaning review.

Party, sponsor, cosponsor, ideology, expected behavior, episode plans, desired
synthesis, and public wording are forbidden meaning inputs.

## Exact-action rules

- An amendment candidate may use only its exact amendment purpose or
  description for the meaning claim. Parent-measure content cannot substitute.
- A whole-measure or resolution candidate uses the stage-compatible operative
  text bound by readiness.
- Yea/Nay is an official member action. It becomes
  `supports_exact_choice`/`opposes_exact_choice` only after the exact choice is
  established.
- Present and Not Voting remain non-directional.
- An action that failed readiness remains in universe accounting, receives no
  candidate, and cannot be recovered with alternate evidence in this stage.

## Coverage states

`bounded_official_purpose_summary` states the exact official purpose without
claiming a broader issue position. If the title includes “and for other
purposes,” that non-exhaustiveness is explicit.

`package_level_bounded_summary` is the generic whole-package state for large
authorization, appropriations, omnibus, and other multi-part measures. It says
what whole package the chamber considered while expressly refusing to attribute
the member's action to any individual component. This state is cross-issue; it
contains no National-Security-specific semantic exception.

## Candidate/decision separation

The candidate artifact, evidence maps, review dossier, and parity manifest are
non-authorizing. The human-decision template binds every candidate digest but
leaves reviewer, decision, rationale, and timestamp empty. Filling or accepting
that template is a separate human-authority milestone.

## Downstream boundary

Action-meaning acceptance, policy episodes, Semantic IR, propositions,
synthesis, public wording, publication, production persistence, and deployment
remain false. Validation proves structural and source conformance; it does not
prove political truth or confer human approval.
