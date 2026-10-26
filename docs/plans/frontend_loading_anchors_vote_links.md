# Bounded frontend loading, anchors, and official vote links

## Intent and outcome

Make representative/issue anchor destinations visible below the sticky header,
offer verified readable official vote pages while preserving exact source URLs,
and measure loading/recovery without changing civic interpretation or disclosure.

## Baseline and scope

- Isolated managed worktree: `C:/Users/Dylan/.codex/worktrees/4b3c/political_fingerprint`.
- Branch: `codex/frontend-loading-anchors-vote-links`; base and verified remote main:
  `c52d121b64d814de3cf684980368bced40e5b4ea` (initially clean).
- Sole writer; other worktrees and PR 232 are outside scope.
- Expected 6–10 source/test/document files, no regenerated editorial output.
- Reuse installed Node/Next/Playwright dependencies through an ignored local
  junction. No installs, persistent configuration, credentials, backend,
  hosting, caching semantics, publication, deployment, or production writes.
- Read root instructions, interpretation principles, operating, rendered-review,
  PR workflows, and verification skill. Rendering must preserve canonical
  meaning, evidence counts, exclusions, and progressive disclosure.

## Sequence and definition of done

1. Inspect and measure browser cold-context/warm-reload loading and recovery;
   distinguish browser cache from unobservable backend cold-start state.
2. Correct header occlusion and add only verified official readable link mappings;
   retain raw source provenance. Change loading only for reproduced routine defects.
3. Run focused unit/browser regression checks, lint/build, desktop/mobile rendered
   review, and inspect the exact diff.
4. Commit/push a normal feature branch, open and attach a separate draft PR.
   Freeze its head for controller-arranged independent review; do not claim ready
   before that review.

## Progress and evidence

- [x] Worktree placement, base, branch, and clean initial state verified.
- [x] Loading/recovery measurements and concrete diagnosis.
- [x] Bounded implementation and focused tests.
- [x] Rendered review and final diff inspection.
- [ ] Draft PR delivered; independent review pending controller.

## Discoveries / decisions

- Profile fetch precedes parallel positions/presentations; selected-issue receipts
  start after that pair completes. No timing cause inferred from prior observations.
- Representative heading had no scroll offset; other anchors used fixed offsets.
  The journey now measures the sticky header with ResizeObserver, applying its
  CSS height plus 1rem to anchor targets, including after wrap/resize/zoom.
- A queued ledger hash scroll could override a subsequent representative-header
  navigation. The callback now requires the original hash and a mounted effect.
  The new keyboard sequence reproduced this failure before correction and passes
  afterward at all four tested widths.
- Loading code is unchanged. The observed delay was predominantly waiting for
  API response bytes. Request scheduling, timeouts, caching, and backend design
  are outside this fix; no performance improvement is claimed.
- Final scope is 11 files, including the focused CI test-list addition and a
  reproducible timing probe. No generated editorial output or data mutation.

## Loading observations and reproduction

Public route: `/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119`
on `https://political-fingerprint.vercel.app`, October 26, 2026.
Installed Chromium/Playwright, 1440×1000, reduced motion; sequential fresh context
then reload in that context. Values below are seconds from navigation start.

| Start (America/New_York) | Browser state | DOM ready | Representative | Issue summary | Receipts |
| --- | --- | ---: | ---: | ---: | ---: |
| 15:00:56 | Fresh context | 2.883 | 46.161 | 50.526 | 51.350 |
| 15:01:47 | Immediate reload | 0.056 | 0.274 | 4.142 | 4.973 |
| 15:12:22 | Fresh context, probe verification | 2.681 | 3.031 | 7.429 | 8.254 |
| 15:12:30 | Immediate reload | 0.052 | 0.261 | 4.127 | 5.461 |

First pair: profile request start-to-first-byte was 42.891s / 0.106s;
positions took about 4.137s / 3.849s from request start timestamp through end;
presentations 0.844s / 0.776s; evidence 1.062s / 0.920s. All four API endpoints
returned 200 in both pairs, with no browser page errors. Counts remained
25 recorded / 17 reviewed-scope / 3 findings / 6 supporting votes / 8 unreviewed.
These are observations, not hosting-tier, database, or cold-start attribution.
Only the browser context/cache state is controlled; backend idle state is unknown.

Reproduce from repository root (two read-only page visits, existing dependencies):

```powershell
node scripts/measure_frontend_loading.mjs 'https://political-fingerprint.vercel.app/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119' .tmp/frontend-loading
```

The probe writes stages, per-request timing/status, coverage text, and screenshots.
It does not request secrets or alter cache behavior. Local evidence from this run:
`.tmp/frontend-pass/loading-measurements.json` (first pair) and
`.tmp/frontend-pass/reproducibility/loading-measurements.json` (committed probe).

## Observed recovery (local production build, controlled transport failures)

- Delayed positions: loading remains explicit, then the selected route and full
  coverage appear. Focus moved by the reader remains on their control.
- Profile 503: error and finder appear; browser reload recovers the same route.
- Positions 503: explicit unavailable state; changing Congress and back recovers.
- Presentations 503: summaries are unverified/unavailable; basic vote receipts
  remain available, with no fabricated reviewed findings. Reload recovers.
- Receipt 503/network failure: existing Retry recovers the same exact-action
  finding on desktop/mobile, with duplicate-click protection and focus retained.
  Repeated failures, stale responses after member/issue/scope changes, identity
  mismatch, legitimate empty receipts, and partial receipt notices remain tested.
- Follow-up limitation: profile/issue-summary requests have no dedicated retry
  button or application timeout. An indefinitely pending transport can continue
  showing loading. No arbitrary timeout or new recovery UX was introduced.

## Official vote verification and source boundary

Only House Clerk exact XML routes receive an additional readable URL. The
original `url` and input provenance objects remain unchanged; the receipt displays
both **Official vote** (readable page) and **Original vote source (XML)**.
Existing readable URLs, query/fragment variants, unknown hosts/formats, zero rolls,
pre-1990/future years, and unverified chambers retain their exact supplied URL.

On October 26, all 25 current Education source URLs were checked with public GETs:
each readable page returned 200 and contained an explicit link back to the exact
XML pathname. Additional zero-padding/year examples also passed:

- [2025 roll 313](https://clerk.house.gov/Votes/2025313): H.R. 1069, 119th Congress,
  first session, December 4, 2025; links `/evs/2025/roll313.xml`.
- [2025 roll 32](https://clerk.house.gov/Votes/202532?Page=2): links
  `/evs/2025/roll032.xml`; readable IDs do not zero-pad the roll.
- [2024 roll 1](https://clerk.house.gov/Votes/20241): 118th Congress, second session;
  links `/evs/2024/roll001.xml`.
- The [Clerk 1990 archive](https://clerk.house.gov/evs/1990/ROLL_000.asp)
  establishes the conservative year boundary; future years are not synthesized.

Exact local response-status/title/XML-link receipts for the 27 checks are retained
at `.tmp/frontend-pass/official-link-verification.json`. This confirms the mapping
convention and those records, not live availability of every historical vote.

Senate readable pages for 119/1 rolls 81 and 127 were visible through web retrieval,
but direct HTTP retrieval returned 403, and the exact HTML/XML target could not be
verified through the available retrieval path. Final code therefore does **not**
convert Senate XML to presumed `.htm` URLs. The Senate fixture tests exact raw-only
fallback, including invalid Congress identifiers. No access denial was bypassed.

## Validation, limitations, and reconciliation

- `node --test lib/officialVoteLinks.test.mjs lib/publicReceipt.test.mjs lib/frontendPassA.test.mjs`
  from `frontend`: 30 passed.
- `npm run lint`: passed, with eight pre-existing hook-dependency warnings in
  unrelated components. Build repeats those warnings; no new lint errors.
- `npm run build`: passed after final source changes.
- Production-mode Playwright: 89 passed / 1 optional screenshot-only test skipped
  across `frontend-loading-anchors`, `frontend-pass-a`,
  `production-evidence-integration`, and `record-card-release`.
  Final command from `frontend`:

```powershell
$env:PLAYWRIGHT_PRODUCTION_BUILD='1'
$env:FRONTEND_PASS_SCREENSHOT_DIR='../.tmp/frontend-pass/screenshots'
node node_modules/@playwright/test/cli.js test tests/frontend-loading-anchors.spec.mjs tests/frontend-pass-a.spec.mjs tests/production-evidence-integration.spec.mjs tests/record-card-release.spec.mjs --workers=2 --reporter=line
```

- Rendered review: 1440, 1024, 390, 320px; 200% zoom; keyboard/native hashes,
  resize, direct receipt links, selected-issue arrival, supporting-vote filtering.
  Representative heading clears the sticky header; House readable/raw links fit
  mobile; no horizontal overflow; coverage and progressive disclosure unchanged.
- Inspected screenshots under `.tmp/frontend-pass/screenshots/`:
  `representative-anchor-320.png`, `representative-anchor-390.png`,
  `education-receipt-1440.png`, `education-receipt-390.png`, and
  `official-sources-390.png`. These local artifacts are ignored, not PR contents.
- Earlier diagnostic development-mode runs exposed the corrected scroll race and
  strict-mode duplicate requests that conflict with existing single-attempt retry
  fixtures. Stopped that broad development run; canonical production mode passed.
  Sandbox subprocess/network errors were local tooling restrictions; authorized
  escalated build/browser/Git commands worked. No automatic-review rejection.
- `git diff --check`: passed; intended diff inspected. Publication state,
  evidence semantics, authored content, and other worktrees unchanged.

Production writes: none. Rollback: revert the bounded frontend commit; no data
rollback needed. Draft delivery and exact frozen identity are reported in the
task response. Independent final review remains a separate readiness gate;
no merge/deployment is authorized by this milestone.
