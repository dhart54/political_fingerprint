# Editorial standardization pipeline

## Purpose

This workflow turns a human-reviewed presentation standard into a scalable, fail-closed generation and quality-control process. Deterministic validation establishes contract conformance; it does not prove political truth, factual perfection, motive, or human verification.

The legislative action dossier is researched once and reused across representatives. The system must not independently rewrite the same bill facts, effects, arguments, or sources for every member. Member-specific data is limited to authoritative action status and the bounded synthesis derived from the shared episode contract.

## Generation order

1. Ingest and canonicalize the legislative action.
2. Build or reuse the member-neutral action dossier.
3. Resolve the exact stage and source mappings.
4. Group related actions into a Congress-bounded policy episode.
5. Optionally relate episodes through a cross-Congress policy family without merging them.
6. Overlay each member's authoritative action status.
7. Calculate coverage against the shared episode contract.
8. Derive candidate within-episode trajectories and cross-episode findings.
9. Map established, member-neutral policy traits into shared, compatible, contrasting, or unresolved policy clusters.
10. Build a structured conclusion proposition model before prose: archetype, thesis, clusters, contrast, trajectory, exception, boundary, evidence and omitted episodes, reader-label concept, and review route.
11. Render a bounded public conclusion from proposition roles rather than action or episode titles.
12. Select three to five featured episodes upstream.
13. Build the public view model; React renders that model and does not infer civic meaning.
14. Run deterministic structural, editorial-utility, and mutation-tested integrity gates.
15. Run responsive, accessibility, and bounded-disclosure tests.
16. Emit deterministic validation and conclusion-compression reports.
17. Route failures and genuinely novel evidence structures for human review.
18. Permit periodic stratified auditing of passing slices.

`scripts/build_editorial_standardization_validation.mjs --check` fails when the committed report drifts from the candidate and public-view contracts. The report uses `pass`, `pass_with_nonblocking_warnings`, or `blocked`; none of those states confers human editorial approval.

## Evidence and absence states

Required action fields must contain sourced content or an explicit supported absence state:

- `not_applicable`
- `not_material`
- `not_material_or_not_available`
- `adequate_official_argument_not_found`
- `source_unresolved`
- `pending_research`

`source_unresolved` and `pending_research` block publication eligibility. One-sided official argument evidence stays one-sided: render the supported side and the supported absence note, never invented symmetry.

Source handling preserves four distinct states: source attached, claim mapped to a locator, claim supported under the dossier contract, and human verified. An attached source or mapping is not by itself proof of support or human verification.

## Review escalation

Every generated slice receives one non-publication workflow route:

- `standard_generation_pass`: established sources, policy traits, relationships, and archetype; all blocking and editorial-utility rules pass.
- `sampled_audit_candidate`: the same passing state, selected by an established deterministic quality-sampling rule.
- `human_exception_required`: new or unresolved traits, relationships, evidence conflicts, compression ambiguity, broad-philosophy candidates, or structures outside the known archetypes.
- `blocked`: source, coverage, service-status, member-leak, unsupported-claim, structural, or publication-boundary failure.

These routes govern quality-control work only. None means human approved, gold benchmark, production eligible, published, merged, or deployed.

### Automatic block

- unresolved source or incomplete action result;
- representative leakage into shared evidence;
- action-direction or coverage contradiction;
- unsupported claim or invented argument;
- ambiguous service eligibility presented as known;
- missing required episode relationship or cross-Congress merge;
- public workflow/methodology leakage or invalid publication status;
- missing official vote or measure source;
- more than five featured episodes or selected-issue duplication.

### Human exception review

- a new policy trait, trait relationship, or ontology concept;
- new legislative action type or novel procedural mechanism;
- contested episode grouping or a package whose policy meaning cannot be bounded;
- cross-Congress relationship not represented by existing fixtures;
- new analytical category or broad-philosophy candidate;
- unresolved one-sided argument evidence;
- conflicting authoritative sources.

Shared review happens once where possible. Humans review new legislative dossiers, policy traits, episode relationships, and ontology changes at the shared evidence layer. Once established, those structures may be reused across member overlays. Ordinary overlays that remain inside the established contract may proceed through deterministic generation and stratified audit rather than exhaustive bill-by-bill rereview.

### Eligible for sampled audit

- standard final-passage or amendment action using an existing dossier contract;
- known episode relationship with a member-overlay-only change;
- known consistent, selective, or divided synthesis shape;
- every deterministic gate passes.

Eligibility for sampled audit does not authorize production publication, benchmark promotion, registry inclusion, merge, or deployment.

## Stratified quality sampling

Future audits should sample across chamber, issue, Congress, action type, Yea/Nay/Present/Not Voting, multi-action and single-action episodes, package and non-package measures, one-sided argument evidence, consistent/selective/divided conclusions, and incumbent/partial-service records.

Quality assurance therefore combines reference fixtures, automated gates, mutation testing, targeted exception review, and stratified sample audits. It does not depend on exhaustive human reading of every generated card.

## Service-status boundary

Yea, Nay, Present, Not Voting, not yet serving, no longer serving, and missing evidence remain distinct. Year-only service metadata cannot establish action-date eligibility. When exact dates are unavailable, an absent action remains missing evidence; presentation convenience must never relabel it as outside service.

## Publication boundary

The reference-fixture designations `human_reviewed_presentation_fixture`, `reference_render_fixture`, and `standardization_regression_fixture` are regression metadata only. Real content remains `human_approval_pending`, `not_promoted`, and `productionEligible: false` until a separately authorized publication decision.
