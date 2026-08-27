# Action Interpretability Contract V1

## Purpose and authority

Action Interpretability V1 qualifies whether a governed exact legislative action has enough concrete, member-neutral meaning for semantic review. It operates at Shared Action Core meaning qualification within the accepted five-layer editorial model.

The JSON Schema is `action_interpretability_v1.schema.json`. Candidate conformance is validated by `backend.app.semantic_ir.action_interpretability`. Passing this contract does not accept a meaning, modify Shared Action Core, authorize issue mapping or member projection, approve public wording, or permit persistence, publication, production, or deployment.

## Minimum semantic content

Each exact action supplies:

- `policy_choice`: the choice Congress was making;
- `mechanism`: the legal or administrative tool creating the change;
- `affected_entities`: the directly regulated, funded, eligible, required, or protected parties and entities;
- `direct_effect`: the first-order operative change if the exact proposal were adopted at that stage;
- `plain_language_meaning`: a short neutral synthesis usable as the semantic basis for later separately reviewed wording;
- `limitations`: exact-action, package, amendment, or evidence boundaries needed to prevent overclaiming;
- optional `downstream_effects`, which must be separately sourced and are otherwise omitted.

Every substantive field maps to a governed `source_id` and narrow locator. Each candidate also records the governed source-packet digest and the raw and neutral-projection digests of every governed source identity.

## Exact-action boundaries

Proposal effect, House outcome, and enactment remain separate. A House vote never establishes enactment. An amendment must bind its exact amendment evidence and cannot inherit parent-bill meaning. A whole-package action cannot be projected onto a component unless an already-governed relationship authorizes that component claim.

Shared meaning contains no representative, party, official member action, support/opposition, or issue-taxonomy semantics. Present and Not Voting belong to later member action projection, not intrinsic action meaning.

## Candidate states

- `candidate_complete_for_semantic_review`: all mechanical requirements pass and the evidence supports a concrete candidate; human semantic review remains required.
- `source_enrichment_required`: the current governed evidence must be enriched before concrete interpretation is possible.
- `insufficient_for_useful_interpretation`: the evidence cannot support useful action meaning under the current contract.

These states are intentionally small and non-authorizing. A grammatical or source-bounded sentence is not complete merely because it avoids prohibited language.

## Deterministic qualification

The validator checks exact identity and source binding, field-level source mappings, mechanism and affected-entity presence, concrete direct effect, member neutrality, proposal/outcome/enactment separation, amendment/package boundaries, supported-or-omitted downstream claims, duplicate identities, historical artifact parity, and non-authorizing state.

These checks catch mechanical failure classes. They do not establish natural-language quality or semantic truth; independent semantic/product review remains required.
