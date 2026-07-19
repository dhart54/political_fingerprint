# Editorial Issue Frontend Workflow

Use this workflow when adding or reviewing a reader-facing editorial slice for one representative and one issue.

## Presentation contract

The generic frontend contract is adapted in `frontend/lib/editorialIssueExperience.mjs` and rendered by `frontend/components/EditorialIssueExperience.js`. React receives a reader-facing view model; it does not read an editorial review packet directly and does not calculate support, opposition, episodes, patterns, or philosophy from raw rolls.

The view model supports:

- member, issue, Congress/review-period, editorial status, and publication identity;
- supplied synthesis, indicators, patterns, voting context, reading guidance, and evidence-strength wording;
- variable vote/context record counts with optional stage, date, lifecycle, practical-choice, change, impact, argument, context, and source fields;
- explicit `substantive`, `not_voting`, and `context_only` inclusion classes;
- grouped official sources with valid HTTP(S) URLs, independently deduplicated by stable ID and canonical URL, without internal claim or source IDs.

Optional fields are omitted rather than replaced with invented content. Missing panels, facts, arguments, context, or source groups must not leave empty cards or headings.

## Real representative selection

`frontend/app/page.js` supplies the selected member to `PositionByIssue`. `PositionByIssue` loads the existing issue evidence response and asks the pure selector for a matching editorial experience at the `EvidencePanel` boundary.

- Eligible matching slice: render `EditorialIssueExperience`.
- No slice, incomplete evidence match, or ineligible slice: render the existing basic issue summary and vote evidence.

The fallback is intentionally temporary while editorial coverage is sparse. Do not duplicate new product features across both paths unless they are truly shared low-level primitives.

## Review versus production eligibility

Publication gates are deliberately separate:

- Explicit review mode may render pending content on the server-gated golden-render route and labels it as unpublished review content.
- Production mode reads only `frontend/lib/editorialIssueProductionSlices.mjs`; pending bundles live in the separate review registry and are passed explicitly by the review fixture.
- Production mode requires registry `human_approved`, `gold_benchmark`, and a separate explicit `productionEligible: true` flag, plus source-level `human_approved` and `human_approved` on every included record where that field exists.
- `human_approved` alone is not public-production authorization.
- Pending content may exist on `main` while remaining ineligible for production representative pages.

The golden-render route is unlinked and enabled only by `ENABLE_GOLDEN_RENDER_FIXTURE=1` or Vercel preview. It passes review mode through the same `PositionByIssue` selector, adapter, and renderer used by the real representative flow; it must not fork the renderer.

## Adding a future slice

1. Complete the source-grounded editorial workflow without changing frontend semantics.
2. Add the static source bundle and identity/synthesis/publication metadata to the review registry.
3. Keep it pending and production-ineligible while review is incomplete; promotion to the production registry is a separate publication action.
4. Validate matching, optional fields, non-counting classes, source deduplication, fallback, accessibility, and responsive behavior.
5. Promote human approval, benchmark status, and public-production eligibility only through their separate authorized governance decisions.

The second real-domain validation (Foushee Justice & Public Safety) confirmed that explicit episodes, optional one-sided arguments, variable counts, empty additional lists, and production fallback work without domain-specific runtime branching. The next contract-validation milestone should reuse a measure dossier across another representative. Synthetic fixtures are only genericity tests and are never editorial evidence.
