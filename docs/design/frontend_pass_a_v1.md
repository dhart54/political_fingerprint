# Frontend Pass A V1 Design Record

## Outcome

Frontend Pass A replaces the stacked representative dashboard with one
route-ready journey:

`finder → representative overview → issue discovery → reviewed analysis when
authorized → policy episodes when supplied → chronological exact receipts`.

The public route remains `/`. Representative, issue, and Congress scope are
encoded in URL query parameters so refresh, Back, Forward, and shared links
preserve the user's location. No representative or sample is selected
automatically.

## Visual direction

The route uses the approved light editorial direction: warm ivory page
background, white evidence surfaces, restrained teal accents, serif display
headings, sans-serif interface text, generous spacing, and light borders.
Party never controls color or hierarchy. There is no profile image, dashboard
rail, score, or dense top-level data panel. Pills are reserved for closed
review/public-claim states and exact vote positions.

The responsive issue grid is four columns at wide desktop, two at medium
widths, and one on mobile. The selected issue then appears once as a deeper
section; it is not repeated as a second competing card. At 320 pixels, long
titles, source links, controls, and receipt metadata wrap without horizontal
scroll.

## Route-ready component boundary

- `RepresentativeFinder` owns explicit ZIP/name lookup and its loading, empty,
  and failure states.
- `RepresentativeHeader` owns the compact selected state and switch action.
- `ScopeControl` owns truthful `all`, `119`, and `118` vote-record scope.
- `IssueOverviewGrid` and `IssueDiscoveryControls` own evidence summaries,
  neutral composition, sorting, and reviewed-analysis filtering.
- `IssueDetail` composes conditional section navigation, reviewed findings,
  optional policy episodes, and the ledger.
- `ReviewedAnalysisSection` renders backend-supplied semantic roles and
  directions; it does not classify wording.
- `PolicyEpisodeSection` accepts the future reviewed episode contract and stays
  absent when the backend supplies no episodes.
- `ChronologicalActionLedger` and `ActionReceipt` own deterministic ordering,
  filters, progressive disclosure, highlighting, evidence boundaries, sources,
  episode relationships, and provenance references.

`frontend/lib/frontendPassA.mjs` owns non-semantic route state, sorting, filter,
and receipt-identity helpers. It may count supplied positions for display. It
may not infer support, opposition, analytical direction, review completion,
claim authority, or a conclusion.

## Public review-state adapter

`scripts/build_public_review_state_catalog.py` validates every full-record review
manifest through the merged validator and emits the closed, deterministic
runtime catalog at
`backend/app/editorial_presentations/public_review_state_catalog_v1.json`.
The catalog exposes only public fields required by Pass A.

Catalog state is descriptive, not authorizing. The public selector still
requires a separately eligible, publication-active presentation and exact
member, issue, artifact, semantic-tier, teaser, and scope agreement. Any
missing or mismatched input fails closed to `receipts_only`.

The current F000477 Justice presentation therefore remains:

- semantic tier: `reviewed_conclusion`;
- review scope: `benchmark_sample`;
- public claim: `reviewed_sample_finding`;
- public label: `Reviewed benchmark sample`;
- full issue synthesis eligible: `false`.

`scope=119` and `scope=all` may render that bounded sample; `scope=all` retains
the reviewed-119th boundary. `scope=118` remains receipts-only.

## Issue discovery and receipt behavior

Recommended ordering uses only backend-supplied public review state, evidence
usefulness, and stable domain order. It excludes party, ideology, Yea/Nay
direction, support/opposition, and generated conclusions. Alternate controls
provide most-evidence, reviewed-analysis-only, and alphabetical views with an
explicit active explanation.

The ledger is newest-first, initially shows 12 rows, and keeps the complete
record one click away. Only one receipt or episode is expanded at a time.
Filters preserve Present, Not Voting, substantive, procedural, and
limited-context distinctions. A finding control highlights and focuses an
exact canonical receipt with a bounded explanation; it never hides the rest of
the record.

## Policy-episode boundary

Pass A implements the presentation component but the live selector supplies an
empty `policy_episodes` array. When a later reviewed backend artifact supplies
episodes, the component can display:

- title and practical policy question;
- member record, outcome, and current status;
- what would change and affected people or institutions;
- supporter and opponent argument summaries;
- one-sided-source limitation and contextual caveats;
- official sources; and
- exact actions ordered oldest-first within each episode.

Supplying, reviewing, or publishing episode prose remains a separate
methodology/editorial milestone.

## Accessibility and deferred tools

The route uses semantic regions/headings, explicit control names, status and
alert announcements, `aria-pressed`/`aria-current`/`aria-expanded`, visible
focus, focus transfer after representative and issue selection, and
reduced-motion-aware receipt navigation. Base body text is 16 pixels and the
layout remains usable at 200% zoom.

Comparison, preference/alignment, race context, alerts, contact, methodology
explorers, and across-Congress analytical tools are deferred from the primary
journey. Their underlying components are preserved; Pass A does not delete or
reinterpret them.

## Pass A / Pass B boundary

Pass A establishes the journey, deterministic public review state, sample-safe
analysis rendering, future episode component boundary, and exact receipt
foundation. Pass B may refine secondary navigation and visual polish, connect
reviewed episode payloads, and revisit deferred tools only under their own
product and methodology authority. Pass A does not create full-record claims,
new interpretations, publication state, production writes, or a deployment.
