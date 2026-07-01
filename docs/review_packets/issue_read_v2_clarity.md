# Review Packet: Issue Read v2 Clarity

## Summary

- Dominant interpreted Yes/No issue records now use mostly-supported/opposed framing at the two-thirds threshold instead of falling into mixed language merely because both sides have votes.
- Issue overview finding copy now keeps the direct finding/count short, then uses concrete reviewed measure categories once in the theme sentence.
- Generic vote-card summaries strip audit-leading phrases before public display while preserving source/caveat drawers and the full reviewed vote list.

## User-Visible Copy Behavior

- Dominant issue cards can show `Mostly opposed in reviewed sample` or `Mostly supported in reviewed sample`.
- A 128 opposed / 22 supported National Security sample renders as mostly opposed, with the finding/count first, then side-specific themes: opposed measures centered on defense authorization legislation, foreign military sales, and veterans cemetery administration; supported votes centered on motions to commit.
- Close split samples still render as split or mixed.
- `What that means` continues to use concrete reviewed measures when available and falls back to broader issue-area wording only when concrete categories are absent.
- All-opposed or all-supported samples use one combined concrete theme sentence instead of inventing an empty opposite-side theme.

## Scope Boundaries

- Changed frontend issue-read copy, readiness grouping, profile narrative labels, generic vote summary cleanup, tests, plan, and this review packet.
- Did not change backend, schema, ingestion, methodology, token/config, production writes, Record Across methodology, support/opposition semantics, or evidence ordering.

## Validation

- `cd frontend; node --test lib\*.test.mjs`: passed, 61 tests.
- `cd frontend; npm run lint`: passed with 8 existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with the same 8 warnings.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.
- Rendered local production shell at `http://localhost:3007`: desktop and 390x844 mobile checks passed with no page-level horizontal overflow.

## Remaining Limitations

- Valerie Foushee National Security was not locally renderable from the production shell because live issue evidence was unavailable in this workspace. Source-level regression coverage protects the 128 opposed / 22 supported read, concrete measure categories, source/caveat drawers, and full reviewed vote list access.
