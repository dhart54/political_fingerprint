# Public Editorial Frontend Contract

## Current hard-cutover state

The old-format public editorial selector, production and review registries,
presentation adapters, rich React renderer, fixture data, and review route were
removed in Editorial Hard Cutover V1. They are not supported fallbacks.

The representative route at `/` intentionally renders the basic vote-evidence
experience from the existing positions and evidence APIs. The removed
`/golden-render-fixture` route returns 404.

## Basic evidence contract

`frontend/app/page.js` supplies the selected representative to
`frontend/components/ProfileQuickRead.js` and
`frontend/components/PositionByIssue.js`. The former renders neutral coverage
counts and issue links. The latter loads issue summaries and exact vote evidence
with `fetchPositions` and `fetchPositionEvidence`, then renders:

1. issue selection based on actual evidence availability;
2. a bounded basic-evidence notice;
3. representative Yes/No vote examples;
4. the complete grouped vote list;
5. source links and vote-level receipts;
6. procedural and limited-context disclosures.

The current React path may count and label already-supplied evidence states for
display. It must not infer support or opposition, service eligibility, episodes,
featured evidence, policy patterns, conclusions, motives, ideology, publication
status, or other analytical meaning from raw rolls.

These states remain distinct:

- substantive reviewed Yes/No evidence;
- procedural context;
- limited context;
- Present;
- Not Voting;

Present and Not Voting are resolved non-directional actions. Procedural and
limited-context rows do not become support or opposition. The current production
positions and evidence APIs return actual vote records; they do not emit
expected-but-missing actions or service-status rows. React therefore does not
synthesize or claim to display those states. A narrow amendment does not become
final-passage evidence for its parent measure.

## Deferred presentation

An IR-native public presentation is deferred. A future milestone must consume
compiled Semantic IR through a meaning-preserving view model and may not
reintroduce the deleted format or reconstruct analysis in React.

Semantic acceptance, human approval, benchmark status, production eligibility,
publication, merge, and deployment remain separate decisions.
