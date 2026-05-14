# Autonomous Handoff

Last updated: 2026-05-14

## Current Branch

- `codex-product-engagement-pass`

## Completed and Committed

- Product v2 rules and methodology:
  - user-defined issue alignment is allowed
  - prescriptive voting advice remains prohibited
  - alignment must be evidence-based and non-ranking
- Product v2 tasklist:
  - `docs/product_v2_tasklist.md`
- Evidence drilldown:
  - backend endpoint for legislator/domain vote evidence
  - frontend evidence panel under Position by Issue
- Vote interpretation foundation:
  - `vote_interpretations` migration
  - deterministic `interpretation_v1`
  - ETL seed persistence
- Issue preference picker:
  - client-side issue selection and stance capture
- Alignment:
  - backend alignment endpoint
  - frontend alignment read
  - alignment cards link to vote evidence
- Comparison reframe:
  - committed as `fff81f8 Reframe comparison around selected issues`
  - comparison accepts the same issue preferences used by the alignment panel
  - both comparison sides show a `Your Issues` aligned/not-aligned/mixed/insufficient count
- Alignment state polish:
  - committed as `1e88a90 Polish alignment states`
  - preference picker no longer shows build-stage copy
  - alignment panel includes idle, loading, empty, mixed, and insufficient-evidence states
- Quick-read evidence links:
  - committed as `460db51 Link quick read to evidence`
  - quick-read domain and vote-direction cards can open underlying vote evidence
- Verification workflow docs:
  - committed as `084cfda Document verification workflow`
  - fixture/Supabase verification modes and Windows Next cache reset are documented
- Coverage metadata:
  - committed as `ab5f856 Surface coverage metadata`
  - `/metadata/coverage` returns source, window, counts, and source-link share
  - hero displays coverage window, loaded legislators, eligible roll calls, and source-link coverage
- Comparison context:
  - committed as `8d7026c Demote generic comparison context`
  - selected issue alignment remains primary; generic comparison reads are supporting context
- Loaded ZIP coverage:
  - committed as `2e66017 Expose loaded ZIP coverage`
  - `/lookup/zips` exposes database or fixture ZIP mappings for UI suggestions
- Deployment docs:
  - committed as `89de46b Document production deployment`
  - Render/Vercel setup, env vars, CORS, checks, and cost notes are documented
- Accessibility/mobile readiness:
  - committed as `11233a4 Add accessibility mobile checklist`
  - accessible names, selected states, and manual mobile QA checklist are in place
- Monitoring docs:
  - committed as `316ae36 Document lightweight monitoring`
  - Render/Vercel checks, privacy-safe logging, and release checklist are documented
- Browser QA alignment fallback:
  - committed as `af1178d Handle missing alignment interpretations`
  - database-backed alignment now returns insufficient-evidence rows when interpretation rows are unavailable
  - alignment copy now says `0 interpreted` rather than implying no classified roll calls exist
- Browser QA cache workflow:
  - committed as `4c64035 Record browser QA cache workflow`
  - Windows Next dev cache reset notes are documented
- Windows test workflow:
  - committed as `3d0c702 Stabilize Windows test workflow`
  - full backend fixture suite passes with `pytest --basetemp=..\.local\pytest_basetemp`
  - cache-source scaffold tests now allow real cached source counts
- Voter journey friction:
  - committed as `27e2051 Reduce voter journey friction`
  - ZIP lookup now auto-opens the House profile and seeds House-vs-senator comparison
  - issue starter checks let users begin with neutral `show_record` bundles
  - evidence source URLs are clickable and visible
- Inspectable comparison issue rows:
  - committed as `eeec66f Make comparison issue rows inspectable`
  - selected-issue comparison now shows per-issue rows for both officials
  - each comparison issue row can open the evidence drilldown for that official and issue
- Shortened voter journey:
  - committed as `95707b9 Shorten main voter journey`
  - main page now keeps ZIP lookup, quick read, issue alignment, position evidence, comparison, and lower profile switching
  - radar, drift, summary, and API health are removed from the main voter path
- Switch-official cleanup:
  - committed as `b519364 Clean up switch official utility`
  - old duplicate Active Legislator slab was replaced with a compact lower search utility
  - useful deleted-section signals remain compactly in Quick Read, hero coverage, and footer methodology/data-window context

## Active Checkpoint

Checkpoint target: `Mobile polish for shortened voter journey`.

Files in this checkpoint:

- `frontend/app/page.js`
- `frontend/components/AlignmentPanel.js`
- `frontend/components/ComparisonPanel.js`
- `frontend/components/IssuePreferencePanel.js`
- `frontend/components/PositionByIssue.js`
- `frontend/components/ProfileQuickRead.js`
- `frontend/components/ZipLookupPanel.js`
- `docs/product_v2_tasklist.md`
- `docs/autonomous_handoff.md`

Completed in this checkpoint:

- removed forced mobile full-viewport hero height while preserving desktop hero framing
- scaled large headings down on mobile across the primary journey
- moved individual issue-domain selection into a fine-tune drawer to reduce vertical fatigue after starter checks
- removed drift/summary rows and copy from comparison supporting context; comparison now keeps vote direction and issue focus only
- kept removed radar/drift/summary/API health sections out of the main page

Verification already run for this checkpoint:

- `cd frontend; npm run build` passed
- browser QA at 390x844 passed: ZIP `27701` loads Valerie P. Foushee, starter checks render, fine-tune drawer renders, comparison remains visible, removed summary/drift copy is absent
- mobile interaction QA passed: Cost of Living selects 3 issues, alignment loads insufficient-evidence rows, Open Votes opens evidence, source links render
- browser console errors were empty
- browser viewport was reset after mobile QA

Next exact steps after committing:

1. Polish insufficient-evidence copy so missing interpretation data feels useful and intentional.
2. Focus on `AlignmentPanel`, `ComparisonPanel`, and `PositionByIssue` empty/evidence states.
3. Run `cd frontend; npm run build`.
4. Browser QA ZIP `27701` -> starter check -> insufficient evidence -> evidence.
5. Commit checkpoint and push if requested.

## Verification Already Run

Latest checks:

```powershell
$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_api_alignment.py tests\test_api_compare.py
npm run build
$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_api_metadata.py tests\test_api_lookup.py
```

Reported results:

- `10 passed`
- frontend build passed
- `$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_api_metadata.py tests\test_api_lookup.py` passed (`6 passed`)
- `cd frontend; npm run build` passed
- in-app browser is now unblocked after starting backend/frontend servers
- stale `__webpack_modules__[moduleId] is not a function` overlay was fixed by stopping Next, deleting `frontend/.next`, and restarting dev server
- browser QA passed for ZIP lookup, opening a House profile, selecting an issue, insufficient-evidence alignment fallback, alignment evidence, Quick Read evidence, and comparison supporting context
- mobile-sized browser smoke check passed after clearing `frontend/.next` and restarting Next dev
- `$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_db_read_layer.py tests\test_api_alignment.py` passed (`11 passed`)
- `cd frontend; npm run build` passed after the alignment copy fix
- full `pytest` without `--basetemp` is blocked by `C:\Users\Dylan\AppData\Local\Temp\pytest-of-Dylan` permissions
- `$env:DATABASE_URL='postgresql://invalid'; pytest --basetemp=..\.local\pytest_basetemp` passed outside the sandbox (`144 passed`)
- `cd frontend; npm run build` passed for the voter journey friction checkpoint
- browser QA passed after the voter journey friction checkpoint: reload opens ZIP `27701` to `Valerie P. Foushee`, starter checks select issues, evidence source links render, and console errors are empty
- `cd frontend; npm run build` passed for the comparison issue-row checkpoint
- browser QA passed after the comparison issue-row checkpoint: selected issue rows render for both comparison sides, and Inspect Votes opens evidence for House and Senate officials
- `cd frontend; npm run build` passed for the shortened voter journey checkpoint
- browser QA passed after the shortened voter journey checkpoint: late dashboard sections are gone and evidence still opens from the shortened path
- `cd frontend; npm run build` passed for the switch-official cleanup checkpoint
- browser QA passed after the switch-official cleanup checkpoint: stale search copy is gone and compact retained signals still render
- `cd frontend; npm run build` passed for the mobile polish checkpoint
- browser QA passed at 390x844 after the mobile polish checkpoint: profile, starter checks, fine-tune drawer, alignment, evidence, and source links work with no console errors

If the dev server is running and the browser looks stale, clear the Next cache before refresh:

```powershell
netstat -ano | findstr :3000
Stop-Process -Id <PID> -Force
Remove-Item -LiteralPath frontend\.next -Recurse -Force
Start-Process -FilePath npx.cmd -ArgumentList 'next','dev','-H','127.0.0.1','-p','3000' -WorkingDirectory '<repo>\frontend' -WindowStyle Hidden
```

## Next Product Tasks After Commit

Work from `docs/product_v2_tasklist.md` in this order:

1. Polish insufficient-evidence copy so honest missing-data states feel useful rather than broken.
2. Prefer focused backend tests while developing, then run the full backend fixture suite with `pytest --basetemp=..\.local\pytest_basetemp` before the next checkpoint.

## Operating Mode

- Batch 2-4 related changes per checkpoint.
- Prefer targeted tests during development.
- Run full frontend build before UI commits.
- Avoid browser automation unless visual behavior is uncertain.
- Keep this file updated before stopping if work is incomplete.
