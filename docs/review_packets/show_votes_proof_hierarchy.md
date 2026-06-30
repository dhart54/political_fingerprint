# Review Packet: Show Votes Proof Hierarchy

## Scope

This packet covers the focused frontend proof-view hierarchy update for `Show Votes`.

In scope:

- `frontend/components/PositionByIssue.js`
- focused source-level regression coverage in `frontend/lib/profileMvpProfile.test.mjs`
- active plan reconciliation in `docs/plans/show_votes_proof_hierarchy.md`

Out of scope:

- backend, schema, methodology, token/config, production writes, and Record Across Congresses methodology or API changes
- broad page redesign
- Show Votes work beyond the proof hierarchy and receipt access

## Interpretation Guardrails Consulted

`docs/interpretation_principles.md` was consulted before changing copy or hierarchy.

The implementation keeps the product posture as: finding first, receipts immediately available, and limits/caveats visible. It does not infer motive, ideology, character, corruption, ranking, cross-time movement, or voting recommendations. Procedural, limited/context, and not-voting rows remain separate from countable Yes/No findings.

## Problem

The previous expanded `Show Votes` state rendered the issue summary and then every grouped vote card immediately. That preserved receipts, but the first proof state could feel like a giant undifferentiated list.

## Chosen Hierarchy

The expanded proof view now opens in this order:

1. issue summary and grouped-evidence preview already present in the panel
2. `Representative votes`
3. `Full reviewed vote list`
4. civic/evidence tools

`Representative votes` shows a bounded first proof set of up to 8 countable Yes/No votes using the existing evidence ordering. If an issue has no countable Yes/No rows, it falls back to the sorted available rows and directs users to the full reviewed list.

`Full reviewed vote list` keeps every receipt available behind `Show all reviewed votes`, grouped by bill or measure. The expanded list still reuses the existing grouped bill cards and vote rows.

## Receipt And Caveat Access

Vote-level `Source, caveats, and full context` disclosures remain inside `VoteEvidenceRow` and are reused in both the representative section and full list.

The UI also summarizes context rows when present, using language that says limited, procedural, and not-voting rows are not treated as countable Yes/No findings.

## Fields Used

The hierarchy only uses existing client-side evidence fields and helpers:

- `interpretation_status`
- `position`
- procedural/context helpers
- limited/context helper
- roll call date/chamber/number/type metadata
- measure/title/source/detail fields already rendered by `VoteEvidenceRow`

No backend or methodology semantics changed.

## Validation

- `cd frontend; node --test lib\*.test.mjs`: passed, 57 tests.
- `cd frontend; npm run lint`: passed with 8 existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with the same 8 existing warnings.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.

Rendered production build validation:

- Desktop local production build: `Show Votes` opened `Representative votes` first, then `Full reviewed vote list`; `Show all reviewed votes` expanded the grouped full list; source/caveat disclosures remained available; no page-level horizontal overflow.
- Mobile 390x844 local production build: same hierarchy and full-list access verified; no page-level horizontal overflow.

## Limitations

- Valerie Foushee was not locally renderable because the fixture backend search returned no Valerie/Foushee results. Valerie-specific issue overview copy remains covered by existing source-level tests in `frontend/lib/issueOverview.test.mjs`.
- Record Across Congresses did not render locally in the fixture path because the internal-token-backed route did not return a ready response. This branch did not change Record Across source files, and existing Record Across tests passed as part of the full node suite.
- No production deployment or production write was performed.
