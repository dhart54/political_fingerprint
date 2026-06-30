# Record Across Congresses UX Polish Review Packet

## Milestone

Focused UX/readability polish for the `Record Across Congresses` panel and family roll-call drilldown.

Base: `main` at `1f92d97c4a5ab2311da8be9d4dfd7a7679f29fd2`.

Branch: `codex/record-across-congresses-ux-polish`.

## Read-Only UX Audit

Production baseline checked at `https://political-fingerprint.vercel.app` with desktop viewport `1366x900`.

- Placement: the panel appears after `ProfileQuickRead` and after `PositionByIssue` (`strongest issue evidence`), then before the secondary tools/preferences/comparison disclosure.
- Placement decision: keep this placement. It keeps the panel close to inspectable evidence without making it the primary profile answer.
- Discoverability: baseline collapsed panel was a short `54px` row containing only `RECORD ACROSS CONGRESSES`; it was easy to miss after the long strongest-issue section.
- Collapsed title: too subtle in the baseline because it lacked a plain-language cue or count preview.
- Count summary: expanded counts were present, but the main count label was long and did not explain the bucket distinction until later caveats.
- Family cards: the baseline cards were usable, but the roll-call action read like explanatory copy rather than a clear control.
- Drilldown density: the baseline repeated family metadata and then immediately showed two dense Congress columns; a small drilldown heading helps orientation.
- 118th/119th distinction: sections were separated, but headings were terse (`118th`, `119th`).
- Mobile readability: count buckets used breakpoint-specific grids that could become cramped; an auto-fit grid is safer.
- Horizontal overflow: none found on the production baseline desktop check.
- Sensitive text: production visible UI did not expose `INTERNAL_API_TOKEN`, `X-Internal-API-Token`, or `/internal/record-across-congresses`.

## Changes Made

- Strengthened the collapsed panel summary with:
  - `Record Across Congresses` framing;
  - plain-language cue: `Reviewed family evidence in both Congresses`;
  - count chips for eligible, closest, and caveated families;
  - visible open/close affordance.
- Clarified the expanded intro: counts stay separated by Congress and vote-status bucket.
- Replaced the long main count label with `Eligible families` plus helper text.
- Added helper text for closest and caveated family counts.
- Changed the family drilldown action to `View roll-call evidence` / `Hide roll-call evidence`.
- Added `aria-controls`, `aria-expanded`, `aria-live` for loading/error states, and targeted `data-testid` hooks.
- Added a drilldown heading: `Roll-call evidence used for this family`.
- Expanded Congress headings to `118th Congress` and `119th Congress`.
- Switched family count bucket layout to an auto-fit grid to improve mobile wrapping.

## Copy Guardrails

Panel-scoped visible copy was checked by targeted tests against the existing disallowed-term guardrail list.

The panel copy does not use or imply:

- continuity;
- change/changed;
- movement;
- trend;
- ideological movement;
- consistency;
- changed-position;
- more supportive / less supportive;
- motive;
- recommendation;
- endorsement.

## Existing Nearby-Language Findings

Existing profile summary UI outside this panel still contains cross-time or pattern language:

- `frontend/components/ProfileQuickRead.js`
  - metric label `Change`;
  - drift labels such as `Steady mix`, `Some shift`, `Shifted mix`;
  - scope/comparison text that can include `consistent`, `differs`, and `change`.
- `frontend/components/DriftIndicator.js`
  - standalone change/steady/shifted copy, including `Issue-Attention Change`.
- `frontend/lib/profileNarrative.mjs`
  - comparison statuses include `consistent`, `stronger`, `weaker`, `different`;
  - fallback copy says the profile does not describe a cross-Congress change.
- `frontend/lib/issueOverview.mjs`
  - legacy summary copy uses `consistently supported/opposed` for issue-level samples.

These are legacy/current profile summary surfaces outside the `Record Across Congresses` panel. They can create some conceptual adjacency with the new panel, especially because the production baseline shows `consistent`, `differs`, `Change`, and `Steady mix` above the panel. This milestone did not rewrite them because the request said not to automatically change nearby copy outside the feature. A separate future copy-boundary milestone is recommended.

## Rendered Validation

Completed:

- Production baseline desktop `1366x900` read-only audit:
  - panel present and collapsed by default;
  - appears after strongest issue evidence and before secondary tools;
  - no horizontal overflow;
  - scoped panel text had no disallowed continuity/change/movement terms;
  - visible UI did not expose token/header/internal-route text.
- Changed UI local rendered validation against a deterministic mock API with production-shaped family data:
  - desktop `1366x900` default collapsed state passed;
  - desktop expanded panel state passed;
  - direct family drawer opened with `aria-expanded=true`, matching `aria-controls`, separated `118th Congress` and `119th Congress` sections, and no horizontal overflow;
  - caveated family drawer opened with the same accessibility/section checks and a visible `Present` bucket row;
  - mobile `390x844` default collapsed state passed;
  - mobile expanded direct-family drawer passed;
  - mobile count grids had equal `scrollWidth` and `clientWidth`, confirming no internal count-grid overflow;
  - all checked changed-UI states had no scoped disallowed continuity/change/movement terms;
  - all checked changed-UI states had no visible token/header/internal-route text.
- Vercel preview deployment for PR #56 is ready, but the in-app browser was redirected to Vercel login when opening the preview URL, so direct hosted preview inspection is access-limited in this session.

Local limitation:

- Local fixture-mode frontend/backend could not render the panel because the internal family evidence route uses the DB-backed helper. With the documented invalid fixture DSN, the local backend returned a database connection error for `/internal/record-across-congresses/house/leg_aaron_bean`.
- Local validation used this only to confirm the limitation; no production write or config change was made.

Hosted preview limitation:

- PR #56 Vercel status is green and reports a ready preview URL.
- The browser session cannot complete hosted rendered validation because the preview redirects to Vercel login.
- This is recorded as a preview-access limitation, not a product failure.

Profiles to check on hosted preview:

- Production baseline was checked on Valerie Foushee.
- Changed UI local mock validation rendered the panel under the app's loaded House profile with deterministic family data.
- Aaron Bean and Aumua Amata Coleman Radewagen remain recommended hosted-preview checks once preview access is available.

## Validation Results

- `npm run lint`: passed with 8 existing React hook dependency warnings outside this scope.
- `npm run build`: passed with the same existing hook warnings.
- `node --test lib\recordAcrossCongresses.test.mjs`: passed, 15 tests.
- `node --test lib\*.test.mjs`: passed, 55 tests. Node emitted existing module-type warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches, treated as success.
- PR #56 Vercel status: ready/success, preview access protected in this browser session.

## Production Writes

None.

## Remaining Limitations

- Hosted preview could not be directly inspected from this browser session because Vercel required login.
- Existing non-panel profile copy uses change/steady/consistent/differs language and should be handled separately if the product wants a stricter page-wide boundary around cross-Congress wording.

## Recommended Next Milestone

Run a focused copy-boundary pass for legacy profile summary and drift language so users do not confuse general profile comparison/drift copy with the evidence-only `Record Across Congresses` panel.
