# Fallback Static Loading Copy Cleanup Review Packet

## Interpretation Principles Consulted

- Read `docs/interpretation_principles.md` before implementation.
- Applied the milestone direction: clear interpretation first, receipts available, and no unsupported cross-time movement copy in first-visible fallback surfaces.

## Audit Terms

- Audited frontend for: `Best read`, `Change`, `Steady mix`, `Drift`, `8 roll calls`, `-- source links`, `source links`, `548 legislators`, `560 legislators`, `sample`, `default`, `loading`, and `fallback`.

## Copy Changed

- Replaced hard-coded hero stat fallbacks in `frontend/app/page.js`.
  - Removed stale/misleading initial values: `548` legislators, `8` roll calls, and `--` source links.
  - The first render now shows neutral coverage-loading copy until live coverage metadata is available.
  - Hydrated stats use loaded metadata and label roll-call coverage as reviewed votes.
- Added default-profile context in `frontend/app/page.js`.
  - Aaron Bean is labeled as `Sample profile` until the user selects an official through ZIP lookup, comparison, or search.
- Changed comparison tool static copy in `frontend/components/ComparisonPanel.js`.
  - `Change Comparison Pair` is now `Switch Comparison Pair`.

## Copy Left Unchanged

- `Strongest evidence`, `Coverage`, and `Record read` in the top summary are current intended labels.
- `source links` remains as a loaded metadata stat label, not as a placeholder paired with `--`.
- Existing issue-overview `sample` language remains bounded evidence copy.
- Drift-related component/API strings were left unchanged because they are not rendered in the current first-visible page flow and broad component removal is out of scope.
- Ready-state `Open Best Read` remains unchanged because this milestone targets loading/static/fallback cleanup, not a broader ready-state label pass.

## Targeted Tests

- Updated `frontend/lib/profileMvpProfile.test.mjs` to assert:
  - the first-render profile shell uses neutral coverage-loading copy;
  - sample profile labeling is present;
  - old hard-coded hero fallback values are absent;
  - stale top-summary fallback labels do not return;
  - `Switch Comparison Pair` replaces the old static command label.

## Rendered And Static Validation

- Production build served locally with `npx next start -p 3000`.
- Backend fixture mode served locally with `DATABASE_URL=postgresql://invalid` and `uvicorn app.main:app --port 8000`.
- Desktop 1280x720:
  - no visible top-summary `Change` metric;
  - no `Steady mix`;
  - no stale `Best read / Coverage / Change` loading row;
  - no `8 roll calls`, `-- source links`, or `548 legislators`;
  - sample profile is labeled before ZIP-selected fixture representative loads;
  - hydrated fixture ready state renders record summary and issue evidence;
  - page-level horizontal overflow is false;
  - token/header/internal-route text is not visible.
- Mobile 390x844:
  - hydrated fixture ready state renders record summary and issue evidence;
  - no stale top-summary/fallback strings;
  - no misleading stat placeholders;
  - page-level horizontal overflow is false.
- Static HTML inspection:
  - `.next/server/app/index.html` has no matches for `Best read`, `Change`, `Steady mix`, `8 roll calls`, `-- source links`, or `548 legislators`.

## Validation Commands

- `node --test lib\*.test.mjs`: passed, 56 tests.
- `npm run lint`: passed with 8 existing React hook dependency warnings.
- `npm run build`: passed with the same 8 warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.

## Remaining Limitations

- Local Record Across Congresses rendering was not available in the production server session because the Next proxy requires `INTERNAL_API_TOKEN`, and token/config changes are out of scope. Existing Record Across tests still passed in the required `node --test lib\*.test.mjs` run, and the static bundle scan found no internal token/header/route leakage.
- Lint/build continue to report pre-existing React hook dependency warnings unrelated to this milestone.

## Production Writes

- None.
