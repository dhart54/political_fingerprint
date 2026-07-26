# Editorial Public Issue Presentation V1

## Status and authority

`editorial_public_issue_presentation_v1` is the deterministic contract between
compiled Editorial Semantic IR V1, separately reviewed editorial wording, the
public API serializer, and display-only React.

It is downstream of `backend.app.semantic_ir.pipeline.run_editorial_pipeline`.
It consumes compiled IR as its only source of analytical meaning. It does not
invoke, restore, replay, or adapt any deleted pre-IR generator, selector,
registry, view model, fixture route, or rich editorial component.

The machine-readable shape is
`docs/editorial_public_issue_presentation_v1.schema.json`.

## Separated layers

Each immutable artifact keeps these layers distinct:

1. `compiled_semantic_meaning` copies the conclusion-plan propositions,
   stable identities, relationships, exact action IDs, episode IDs, typed
   source constraints, compiler-owned presentation boundaries, and review
   route.
2. `editorial_wording` contains analytical text mapped to stable proposition
   IDs or compiler-owned typed boundaries. Each record has a unique mapping
   ID, declared target, exact action and episode identities, and source and
   receipt references. Neutral interface labels such as tier badges remain
   explicitly separate.
3. `frontend_display` contains only fields React may render. When any
   publication gate fails, it contains the non-analytical `receipts_only`
   fallback and no conclusion, repeated pattern, trajectory, or limitation
   copy.
4. `evidence_metadata` preserves compiled coverage, complete action accounting,
   canonical action IDs, and episode IDs.
5. `provenance` records semantic sources, focused validation cases, dossier,
   claim, source, and receipt references, compiled-IR and reviewed-wording
   digests, the review receipt, and a deterministic compiler receipt.
6. `controls` keeps semantic acceptance, editorial approval, benchmark status,
   production eligibility, publication activation, and human review separate.
   Derived tier and gate fields are explanatory only and must equal
   independently recomputed values.

Canonical artifact bytes are UTF-8 JSON with sorted keys and compact separators.
The deterministic content digest is SHA-256 over those exact bytes.

## Wording-to-meaning rules

- Every analytical string—including a headline, teaser, summary, repeated
  pattern, trajectory, limitation, analytical coverage line, or analytical
  scope line—maps to one or more proposition IDs or a typed boundary ID.
- Conclusion wording maps to the conclusion-only synthesis propositions.
- Repeated-pattern and trajectory wording maps to one stable proposition in
  its declared Semantic IR presentation target.
- Coverage and scope wording map to deterministic typed presentation
  boundaries derived from compiled coverage and immutable artifact scope.
- Each mapping carries exactly the action and episode identities established
  by its proposition or boundary, plus source and receipt references.
- The compiler rejects missing, duplicate, unknown, broadened, unmapped,
  wrong-section, or parent-measure mappings. It never silently omits an
  unmapped limitation.
- Primary and limiting relationships remain the compiled relationships.
- Source/render constraints remain typed compiler output; rendering does not
  parse constraint prose.
- Contradictory or mixed evidence remains present and may not be silently
  removed.

## Compiler-owned tiers

The backend derives exactly one tier from compiled conclusion plans, typed
coverage and source boundaries, validation, review state, and publication
controls:

- `reviewed_conclusion`: the compiled primary plan contains both an
  independent-episode repeated pattern and a conclusion synthesis.
- `developing_read`: a non-blocked compiled primary plan exists but does not
  meet the reviewed-conclusion semantic shape.
- `non_directional_or_limited_evidence`: no primary analytical plan exists and
  compiled coverage is Present, Not Voting, otherwise non-directional, or
  explicitly limited.
- `receipts_only`: no safe analytical tier exists or any required gate fails.

No vote-count threshold, raw Yea/Nay total, keyword, party, member identity, or
receipt order determines a tier.

Public analytical display requires:

- accepted semantic-reference status;
- passed compiled validation;
- `human_approved` editorial status;
- an approved, content-bound human review receipt;
- explicit receipt approvals for the bounded conclusion, both repeated-pattern
  statements, the fentanyl limitation, claim/source mappings, benchmark
  promotion, and production eligibility;
- `gold_benchmark` status;
- production eligibility; and
- active publication.

`gold_benchmark` is the existing persistence contract's only promoted benchmark
value. `not_promoted` cannot pass the gate, and `promoted` is not a valid status
in this presentation path. Failure of any gate produces `receipts_only`. Merge,
tests, compilation, or semantic acceptance do not satisfy a publication gate.

The human approval receipt identifies the artifact key and version, compiled-IR
digest, reviewed-wording digest, complete mapping ID set, reviewed scope,
reviewer identity and authority, approval state, and individual approval
decisions. Changing wording, mappings, scope, identity, version, or reviewed
content invalidates approval.

## Public selector and scope

The API reads only through
`EditorialArtifactRepository.publication_selector()`. Validation recomputes the
semantic tier and publication result from atomic controls. Persisted
`publication_gates_passed`, `effective_public_tier`, and equivalent cached
results never authorize analytical copy.

Selection requires exact agreement among:

- registry member and issue;
- requested member and scope;
- payload identity and Congress;
- immutable natural key and artifact version;
- schema version;
- recomputed artifact content digest;
- recomputed reviewed-wording digest;
- review receipt binding; and
- provenance/compiler receipt binding.

Any invalid or mismatched row fails closed to the supplied `receipts_only`
result rather than causing a public-route failure.

- `scope=119` may show an eligible 119th-Congress artifact.
- `scope=all` may show that artifact only with an explicit reviewed-119th-
  Congress boundary.
- `scope=118` never shows the 119th-Congress artifact.
- No eligible artifact produces a backend-supplied `receipts_only` object.
- Pending, blocked, ineligible, inactive, malformed, or mismatched analytical
  copy is never serialized.

The selector does not alter card ordering. Canonical action IDs power
“See supporting votes” controls that target the existing receipt cards. Each
control has a finding-specific accessible name, moves keyboard focus to its
receipt, preserves visible focus/highlight styling, and uses non-smooth
scrolling when the user requests reduced motion. React also requires the API
payload's legislator and bioguide identities to match the displayed
representative before rendering presentation content.

## Current Foushee state

The authoring fixture at
`docs/editorial/presentations/f000477_justice_public_safety_119_review_fixture.json`
is bounded to F000477, `JUSTICE_PUBLIC_SAFETY`, and the 119th Congress. Its
semantic source is `semir-dev-05-justice-mechanism-divide`, with
`semir-dev-04-justice-mixed-fentanyl-trajectory` and
`semir-dev-06-justice-one-sided-argument` as focused validation companions.

The pending receipt identifies the immutable content requiring review but does
not approve it: reviewer identity and authority remain `not_supplied`, approval
state remains `human_approval_pending`, and every approval decision remains
false. The fixture remains `not_promoted`, production-ineligible, and
publication-inactive. It is a review fixture, not an active public artifact.
Until an authorized receipt supplies every required approval, its public result
is `receipts_only`.
