# Public Editorial Frontend Contract

## Current hard-cutover state

The old-format public editorial selector, production and review registries,
presentation adapters, rich React renderer, fixture data, and review route were
removed in Editorial Hard Cutover V1. They are not supported fallbacks.

The representative route at `/` retains the basic vote-evidence experience and
may layer fields from the IR-native
`editorial_public_issue_presentation_v1` API. When no eligible active artifact
exists, that API supplies `receipts_only`. The removed
`/golden-render-fixture` route remains absent and returns 404.

## Basic evidence contract

`frontend/app/page.js` supplies the selected representative to
`frontend/components/ProfileQuickRead.js` and
`frontend/components/PositionByIssue.js`. The former renders neutral coverage
counts and issue links ordered by evidence usefulness. That order compares total
available actions, reviewed substantive Yes/No counts, non-directional or
limited/context availability, and finally the stable domain order. It never uses
Yea versus Nay direction, party, ideology, or a generated conclusion. The latter
loads issue summaries and exact vote evidence with `fetchPositions` and
`fetchPositionEvidence`, then renders:

1. issue selection based on actual evidence availability;
2. a bounded basic-evidence notice;
3. representative Yes/No vote examples;
4. the complete grouped vote list;
5. source links and vote-level receipts;
6. procedural and limited-context disclosures.

The current React path may count and label already-supplied basic evidence
states for display. It must not infer support or opposition, service
eligibility, episodes, featured evidence, policy patterns, conclusions, tiers,
motives, ideology, publication status, or other analytical meaning from raw
rolls. Analytical fields, tier badges, teasers, scope boundaries, and canonical
supporting action IDs come only from the public presentation API.

Issue cards use a single shared, member-neutral description for each supported
domain. Their coverage labels describe evidence availability only. The compact
bar is labeled `Recorded action composition` and displays the positions API's
Yea, Nay, and combined `Non-directional / context` counts. Its denominator is
the sum of those three supplied overview counts, not an expected-action total.
The visible legend names every segment and does not rely on color alone. Exact
Present, Not Voting, procedural, and limited-context distinctions remain visible
in the opened vote receipts. No expected-action denominator is invented. Party
benchmarking is deferred because raw party-level Yea/Nay aggregates would not
establish reviewed action-level meaning.

The evidence-ranked card grid is the primary issue selector. The compact
`Jump to issue` control remains inside the evidence section for local
navigation. A third repeated issue list is intentionally omitted.

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

## IR-native presentation

`docs/editorial_public_issue_presentation_v1.md` defines the downstream
compiler, validator, controls, and API serializer. It consumes compiled Semantic
IR as the only source of analytical meaning, matches wording to stable
proposition identities, and may not reintroduce the deleted format.

Issue-card order remains evidence-first and is unchanged by presentation tier or
availability. Cards show only the API-supplied tier badge and teaser. The opened
issue may show supplied coverage, conclusion or narrower tier message, repeated
patterns, a limiting trajectory, limitations, and canonical supporting-action
controls before the unchanged receipts. `scope=all` preserves an explicit
reviewed-119th boundary; `scope=118` cannot display the 119th artifact.

React renders a presentation only when the API payload's legislator and
bioguide identities match the currently displayed representative and the
presentation issue matches the selected issue. Supporting-vote controls use
finding-specific accessible names, move focus to the canonical receipt, retain
visible focus/highlight styling, and respect `prefers-reduced-motion`.

Semantic acceptance, human approval, benchmark status, production eligibility,
publication, merge, and deployment remain separate decisions. The current
F000477 Justice fixture remains pending and therefore public `receipts_only`.
