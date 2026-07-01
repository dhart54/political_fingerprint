# Review Packet: Show Votes Proof Hierarchy

## Scope

This packet covers the focused frontend proof-view hierarchy update for `Show Votes`.

In scope:

- `frontend/components/PositionByIssue.js`
- `frontend/lib/issueOverview.mjs`
- focused source-level regression coverage in `frontend/lib/profileMvpProfile.test.mjs`
- focused issue-summary copy coverage in `frontend/lib/issueOverview.test.mjs`
- active plan reconciliation in `docs/plans/show_votes_proof_hierarchy.md`

Out of scope:

- backend, schema, methodology, token/config, production writes, and Record Across Congresses methodology or API changes
- broad page redesign
- Show Votes work beyond the proof hierarchy and receipt access

## Interpretation Guardrails Consulted

`docs/interpretation_principles.md` was consulted before changing copy or hierarchy.

The implementation keeps the product posture as: finding first, receipts immediately available, and limits/caveats visible. It does not infer motive, ideology, character, corruption, ranking, cross-time movement, or voting recommendations. Procedural, limited/context, and not-voting rows remain separate from countable Yes/No findings.

## Problem

The first PR version improved the receipt path with `Representative votes`, but the expanded `Show Votes` state still started with a large grouping taxonomy before the receipts. The issue-summary copy also still leaned on party-label framing in `What that means` and treated strongly one-directional samples as generically mixed when both support and opposition counts were present.

## Chosen Hierarchy

The expanded proof view now opens in this order:

1. `Issue summary`
2. `Representative votes`
3. `Full reviewed vote list`
4. `Evidence group overview`
5. civic/evidence tools

`Representative votes` shows a bounded first proof set of up to 8 countable Yes/No votes using the existing evidence ordering. If an issue has no countable Yes/No rows, it falls back to the sorted available rows and directs users to the full reviewed list.

`Full reviewed vote list` keeps every receipt available behind `Show all reviewed votes`, grouped by bill or measure. The expanded list still reuses the existing grouped bill cards and vote rows.

The previous `Evidence groups` preview was renamed to `Evidence group overview` and moved below full-list access. It remains visible, but it is secondary to the representative receipts and full reviewed vote list.

## Issue Summary Copy

The main finding now starts with policy substance, direction, and counts:

- `In this reviewed sample, [Representative] mostly [supported/opposed] [policy-substance measures]: [opposed] opposed and [supported] supported across [total] interpreted Yes/No votes.`
- Reviewed measure categories follow when available from existing grouped/facet data.
- Party and outcome context remain supporting sentences after the policy read.
- The receipt prompt now points users to representative votes below.

One-directional handling uses existing interpreted Yes/No counts only. A support or opposition side at or above two-thirds of interpreted Yes/No votes is described as `mostly supported` or `mostly opposed`; closer records are described as `split`. Limited, procedural, and not-voting rows remain excluded from support/opposition.

## What That Means Copy

`What that means` now starts from policy substance:

- If the representative mostly opposed the reviewed policy measures, users who favored those measures see that the votes were mostly opposed; users who opposed those measures or objected to their terms see that the record was mostly aligned with that view.
- If the representative mostly supported the reviewed policy measures, the alignment language is inverted.
- Split records direct users to inspect the representative votes rather than forcing a mostly-supported or mostly-opposed read.

The previous `If you generally favored these House Republican measures/packages...` framing was removed from this helper. Party context remains available as supporting context in the main finding, after the policy-substance read.

## Receipt And Caveat Access

Vote-level `Source, caveats, and full context` disclosures remain inside `VoteEvidenceRow` and are reused in both the representative section and full list.

The UI also summarizes context rows when present, using language that says limited, procedural, and not-voting rows are not treated as countable Yes/No findings.

Broader scope limits now live in `How to read this`, using: `This read is based on the reviewed votes shown here. Vote records show actions, not motive...`

## Fields Used

The hierarchy only uses existing client-side evidence fields and helpers:

- `interpretation_status`
- `position`
- procedural/context helpers
- limited/context helper
- roll call date/chamber/number/type metadata
- measure/title/source/detail fields already rendered by `VoteEvidenceRow`
- existing issue facet labels and practical-policy phrases already used by `issueOverview.mjs`

No backend or methodology semantics changed.

## Validation

- `cd frontend; node --test lib\issueOverview.test.mjs`: passed, 13 tests.
- `cd frontend; node --test lib\profileMvpProfile.test.mjs`: passed, 9 tests.
- `cd frontend; node --test lib\*.test.mjs`: passed, 58 tests.
- `cd frontend; npm run lint`: passed with 8 existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with the same 8 existing warnings.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.

Rendered production build validation:

- Desktop local production build: passed with the local fixture profile. After `Show Votes`, `Representative votes` appeared immediately after the issue summary; the full reviewed vote list appeared next; `Evidence group overview` appeared below full-list access; full-list expansion and vote-level `Source, caveats, and full context` drawers remained available; no page-level horizontal overflow or token/header/internal-route text was visible.
- Mobile 390x844 local production build: passed with the same order, full-list expansion, source/caveat drawer availability, no page-level horizontal overflow, and no token/header/internal-route text.
- Clear mostly-supported/opposed issue-summary copy and policy-first `What that means` copy are covered by source-level Valerie and split-record tests because the local fixture profile only exposes a limited one-vote issue in the rendered path.

## Limitations

- Valerie Foushee was not locally renderable because the fixture backend search returned no Valerie/Foushee results. Valerie-specific issue overview copy remains covered by existing source-level tests in `frontend/lib/issueOverview.test.mjs`.
- Record Across Congresses source was not changed, and existing Record Across tests passed as part of the full node suite. Local rendered visibility remains limited by the internal-token-backed fixture/server setup.
- No production deployment or production write was performed.
