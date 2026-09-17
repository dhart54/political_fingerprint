# Shared record-card policy — candidate v1

This is one presentation-calibration proposal under the existing editorial
workflow, not publication authority. The released PR191 card remains unchanged.

## Owning boundaries
Shared action meaning stays in Shared Legislative Corpus / Semantic IR. Member
findings and public wording stay in the existing reviewed issue presentations.
PR191's six choices, country-specific rewrite, waiver explanation and whole-card
hashes were bespoke presentation/selection inputs; they are not a new meaning
source. This path does not copy those rewrites or adopt a second member's prose.

## Fixed rules (before held-aside replay)
1. Consume only the existing eight-domain, member/scope-matched API envelope.
   Receipts-only domains contribute coverage absence, never invented findings.
   Reviewed scope and review-state Congress must agree. Individual findings need
   unique stable IDs, complete nonempty canonical actions, title and explanation.
2. Preserve explicit display restrictions. `show_direction=false` is displayed
   under neutral “Reviewed choices,” even if semantic direction exists. Missing
   direction is also neutral; malformed/conflicting supplied direction is an
   exception, never inferred from title, party, raw votes or another member.
3. Resolve existing typed `relationship_roles` against semantic-source IDs in the
   same issue. A parent and all its referenced support/contrast/context findings
   form one indivisible unit. Missing/ambiguous children or action-set disagreement
   is one precise relationship exception; children cannot escape separately.
   Individual mixed trajectories already form atomic complete-action units.
4. Prefer those explicit containers to their components. Then visit domains in
   the existing domain order, round-robin. Within a domain use the existing field
   order (synthesis, pattern, trajectory, notable choice), then stable finding ID.
   This is a reproducible display tie-break, not substantive importance.
5. Overlapping action sets never create independent duplicate entries. Later
   overlap is omitted with the exact earlier entry and shared actions recorded.
   No meaning is merged merely because two findings share evidence. Contextual
   components are recorded separately from actual overlap omissions.
6. A 500-word opening-card budget includes complete titles, explanations and
   qualifications; it is a ceiling, not a target. Oversized units remain accessible
   through issue findings and receive an explicit “needs compact form” exception.
   Fit remaining independent units in round-robin order; record limited-space
   omissions individually. No required count, direction balance or political score.
7. Two shared forms: short source explanation (at most 55 words), or a neutral
   reference form for longer explanations: “Read the complete explanation of these
   N House choices.” Both retain every source limitation and secondary clarification
   on the opening card. A long mixed/relationship form says “Compare the complete
   set of N House choices.” Short atomic mixed explanations remain complete.
   Component qualifications are separate paragraphs prefixed by their source title.
   Issue-level limits with explicit intersecting action IDs accompany the entry;
   unscoped issue limits remain labeled with their issue in coverage details and
   in the existing issue view, rather than being attributed to unrelated findings.
   No sentence is truncated, paraphrased or direction-swapped.
   Details immediately show the complete source explanation, clarification and
   limitations for the parent and every contextual component. Exact receipts stay
   accessible. Source titles are never rewritten by this policy.
8. Preserve per-issue reviewed scopes and the full source scope boundary. Prefer an
   explicit typed `evidence_coverage.cutoff` bound to that boundary; otherwise only
   the literal supported “through Month D, YYYY” scope-boundary form yields a date.
   Unknown date syntax is unspecified, not a guessed cutoff. Capture, generation,
   vote maximum and request dates are never coverage. No shared cutoff is invented.
9. Content bindings include the substantive reviewed inputs and policy version;
   request/capture/generation timestamps do not affect output. The transformation
   reruns on each fetched presentation revision. Old finding URLs fail the source
   check, while current independent issue summaries and receipts remain available.
   Raw ledger changes are not an input to the card.

## Exceptions and authority
Exceptions are deduplicated by rule and semantic source identity (or finding ID
when no shared identity is supplied), not multiplied by member. They neither create
review approval nor alter existing pipeline routing. Valid independent units keep
working. Zero reviewed domains is “no reviewed findings”; reviewed but unsupported
findings is a distinct representation exception; API failures stay unavailable.

Proposed review boundary: after this policy/form review and separate authorization
to adopt it, applying unchanged rules to already publication-gated findings would
be mechanical, without duplicate member/card approval. New meaning, relationships,
forms or policy changes still use the existing workflow. This proposal does not
grant that standing authorization.
