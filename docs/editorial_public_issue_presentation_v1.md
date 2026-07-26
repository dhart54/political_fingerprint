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
   source constraints, and compiler-owned review route.
2. `editorial_wording` contains wording mapped to stable proposition IDs.
   The compiler copies it as data and never creates analytical language.
3. `frontend_display` contains only fields React may render. When any
   publication gate fails, it contains the non-analytical `receipts_only`
   fallback and no conclusion, repeated pattern, trajectory, or limitation
   copy.
4. `evidence_metadata` preserves compiled coverage, complete action accounting,
   canonical action IDs, and episode IDs.
5. `provenance` records the semantic source case, focused validation cases,
   dossier, claim, source, and receipt references, plus the compiled-IR digest
   and review receipt.
6. `controls` keeps semantic acceptance, editorial approval, benchmark
   promotion, production eligibility, publication activation, and the review
   receipt separate.

Canonical artifact bytes are UTF-8 JSON with sorted keys and compact separators.
The deterministic content digest is SHA-256 over those exact bytes.

## Wording-to-meaning rules

- Conclusion wording maps to every primary conclusion-plan proposition ID.
- Repeated-pattern, trajectory, and proposition-specific limitation wording
  maps to one stable proposition ID.
- Each mapped wording record carries exactly the compiled action IDs for that
  proposition.
- The compiler rejects missing, duplicate, unknown, broadened, or parent-measure
  action mappings.
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

All analytical tiers additionally require:

- accepted semantic-reference status;
- passed compiled validation;
- `human_approved` editorial status;
- an approved human review receipt;
- explicit receipt approvals for the bounded conclusion, both repeated-pattern
  statements, the fentanyl limitation, claim/source mappings, benchmark
  promotion, and production eligibility;
- promoted benchmark status;
- production eligibility;
- active publication.

Failure of any gate produces `receipts_only`. Merge, tests, compilation, or
semantic acceptance do not satisfy a publication gate.

## Public selector and scope

The API reads only through
`EditorialArtifactRepository.publication_selector()`. It defensively rechecks
artifact status, controls, schema validation, member identity, and scope before
serializing display fields.

- `scope=119` may show an eligible 119th-Congress artifact.
- `scope=all` may show that artifact only with an explicit reviewed-119th-
  Congress boundary.
- `scope=118` never shows the 119th-Congress artifact.
- No eligible artifact produces a backend-supplied `receipts_only` object.
- Pending, blocked, ineligible, inactive, malformed, or mismatched analytical
  copy is never serialized.

The selector does not alter card ordering. Canonical action IDs power “See
supporting votes” controls that target the existing receipt cards.

## Current Foushee state

The authoring fixture at
`docs/editorial/presentations/f000477_justice_public_safety_119_review_fixture.json`
is bounded to F000477, `JUSTICE_PUBLIC_SAFETY`, and the 119th Congress. Its
semantic source is `semir-dev-05-justice-mechanism-divide`, with
`semir-dev-04-justice-mixed-fentanyl-trajectory` and
`semir-dev-06-justice-one-sided-argument` as focused validation companions.

The fixture remains `human_approval_pending`, `not_promoted`,
production-ineligible, and publication-inactive. It is a review fixture, not an
active public artifact. Until an authorized receipt supplies every required
approval, its public result is `receipts_only`.
