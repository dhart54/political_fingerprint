# Public Copy Safety Contract Review Packet

## Production Failure

Production after PR #64 still allowed raw evidence/audit strings to reach top-level issue copy, including fragments such as:

- `this was a direct vote on Protecting America's Strategic Petroleum Reserve from China Act`
- `If you favored these reviewed measures ... including this was a direct vote on...`

The failure was not in vote-row receipts. It was a missing boundary between public interpretation themes and row-level evidence/audit text.

## Contract Implemented

Top-level public interpretation copy may use:

- curated facet-to-public-theme mappings;
- curated domain fallback themes;
- safe short facet labels;
- explicitly approved public theme strings;
- computed counts and directional labels;
- party/outcome context already computed by existing logic.

Top-level public interpretation copy must not use:

- `what_happened`;
- `why_it_mattered`;
- `plain_english_summary`;
- `description`;
- `question`;
- `uncertainty_note`;
- `interpretation_reason`;
- `classification_reason`;
- `source_basis`;
- long raw bill/amendment titles;
- raw official vote question text.

Those raw details remain available in representative vote rows, the full reviewed vote list, vote summary/details drawers, source/caveat areas, and audit/detail surfaces.

## Unsafe Phrase Filter

`frontend/lib/publicCopyThemes.mjs` now rejects public theme candidates containing audit/evidence markers such as:

- `this was a direct vote`;
- `this vote is useful`;
- `records a direct position`;
- `the House voted on whether`;
- `whether to agree to`;
- `Amendment No.`;
- `the amendment decreases`;
- `official roll call`;
- `classification`;
- `source basis`.

Uncurated theme candidates are also rejected when they are sentence-like, too long, or likely raw measure titles. Curated strings are still checked against the unsafe marker list.

## Fallback Behavior

Theme priority for top-level copy is:

1. curated facet theme;
2. curated domain/theme keyword mapping;
3. safe short facet label;
4. generic domain fallback.

Examples of generic fallbacks:

- `other reviewed national-security measures`;
- `other reviewed fiscal measures`;
- `other reviewed public-safety measures`.

Unknown facets no longer fall back to `what_happened`, `why_it_mattered`, `policy_effect`, `description`, or `question`.

## Valerie National Security Before And After

Before:

```text
The opposed measures centered on this was a direct vote on Protecting America's Strategic Petroleum Reserve from China Act...
```

After, in the production-like regression fixture:

```text
In this reviewed sample, Foushee mostly opposed these reviewed National Security & Foreign Policy measures: 128 opposed and 22 supported across 150 interpreted Yes/No votes. The opposed measures centered on defense authorization amendments, China-related security restrictions, foreign military sales, and veterans cemetery administration. The supported votes centered on war-powers votes and other reviewed national-security measures.
```

The exact production live mix may vary by local/live data availability, but raw row strings are not eligible top-level public themes.

## Tests Added Or Updated

- Added `frontend/lib/publicCopyThemes.test.mjs` for direct helper contract coverage.
- Updated `frontend/lib/issueOverview.test.mjs` so issue overview, `What was reviewed`, `What that means`, and issue-card helper source checks reject raw evidence/audit fields.
- Added a production-like National Security fixture with 128 opposed / 22 supported and unsafe raw strings in row fields.
- Updated overview expectations to use safe public themes rather than `whether to...` question chains.
- Added `frontend/lib/profileNarrative.test.mjs` coverage ensuring record narrative/theme snippets ignore raw row-like fields.

The tests also preserve:

- dominant 128 opposed / 22 supported remains mostly opposed;
- split records remain split;
- representative vote rows and full reviewed list source structure remain covered by existing source tests;
- source/audit/details remain inside collapsed/detail layers, not removed.

## Validation Results

- `node --test lib\*.test.mjs`: passed, 67/67.
- `npm run lint`: passed with 8 existing React hook dependency warnings and 0 errors.
- `npm run build`: passed with the same 8 warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.

## Rendered Validation

Local app shell rendered at `http://127.0.0.1:3000`.

- Desktop default viewport: no horizontal overflow; no visible internal token/header/internal-route text; no unsafe raw phrase text.
- Mobile `390x844`: no horizontal overflow; no visible internal token/header/internal-route text; no unsafe raw phrase text.

Limitation: Valerie Foushee live/local lookup data was not available in this workspace. ZIP `27701` returned `Lookup unavailable: That ZIP code is not in the loaded map yet`, and the default sample profile had issue readiness unavailable. Because of that, production-backed rendered validation of Valerie National Security representative vote rows, source/caveat drawers, full reviewed vote list, and Record Across could not be completed locally. Source-level tests continue to cover those availability boundaries.

## Production Writes

None.

## Remaining Limitations

- A production-backed rendered check should be repeated in an environment where Valerie Foushee issue evidence is locally available or connected to the live data path.
- Existing React hook dependency warnings remain outside this hotfix scope.
