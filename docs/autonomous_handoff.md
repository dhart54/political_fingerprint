# Autonomous Handoff

Last updated: 2026-05-16

## Current Branch

- `main`

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
- Mobile voter journey polish:
  - committed as `64890da Polish mobile voter journey`
  - mobile hero no longer forces a full viewport
  - primary journey headings scale down on phones
  - individual issue-domain selection is now inside a fine-tune drawer
  - comparison supporting context keeps vote direction and issue focus only
- Insufficient-evidence copy:
  - committed as `24754c3 Clarify insufficient evidence states`
  - missing interpretation data now reads as source-grounded vote-meaning status
  - alignment/comparison/evidence empty states point users back to Inspect Votes instead of sounding broken
- Insufficient-evidence browser QA:
  - committed as `9b418b1 Complete evidence copy browser QA`
  - restored in-app browser automation from fallback bundled helper path
  - alignment/comparison now render deterministic insufficient-evidence fallback rows if the browser alignment fetch fails
  - browser QA confirmed the Cost of Living path no longer shows `Alignment check unavailable`
- Comparison selector UX:
  - comparison cards now occupy the primary comparison area by default
  - legislator search moved into a closed `Change Comparison Pair` drawer
  - pair swapping still supports setting either comparison side
- Launch trust clarity:
  - footer now shows compact Method, Evidence, and Limits notes
  - data window remains visible below those notes
- First-screen copy polish:
  - hero supporting copy now leads with ZIP, issue selection, and evidence inspection
  - ZIP lookup card now says `Start with your ZIP.`
  - ready-state copy reflects that the House profile opens automatically
  - issue picker explains that selected issues guide which records appear first without changing the vote record
- Staging-readiness accessibility/CORS polish:
  - `FRONTEND_ORIGINS` now configures explicit deployed frontend CORS origins
  - comparison overlay buttons expose selected state with `aria-pressed`
  - position issue cards expose selected state and clearer accessible names
  - deployment and accessibility docs now reflect the current staging setup
- Release-prep staging docs:
  - `docs/staging_readiness.md` records current status, intentional limits, env vars, deploy checks, and reviewer focus questions
  - deployment and monitoring docs point to the staging readiness checklist
- Comparison overlay cleanup:
  - visible `ALL / D / R` toggle removed from the issue-comparison header
  - `Overlay comparison is set to...` status copy removed
  - comparison still uses the default all-legislator context internally for supporting data
- Evidence bill grouping:
  - evidence rows now show roll-call count versus bill-or-measure count
  - related roll calls are grouped under the same bill title or measure label
  - methodology now documents that grouping is presentational and does not change metrics
- Final local staging verification:
  - full backend fixture suite passed
  - frontend build passed
  - local API checks passed
  - staging readiness summary updated
- ZIP comparison preset button states:
  - House-vs-senator preset buttons now show hover, focus, and selected states
  - selected preset is tracked with `aria-pressed`
  - clicking the senators preset updates the comparison pair and selected profile visibly
- Shelved product idea:
  - future deterministic "Voting neighbors" module recorded in `docs/product_v2_tasklist.md`
  - should avoid leaderboard language and explain overlap/evidence before launch consideration
- Evidence metadata compaction:
  - bulky `Classification` and raw `policy_vote` cards were removed from evidence rows
  - evidence rows now show compact `Included as eligible policy vote` context
  - source URLs remain available through a compact `Source` link
- Final frontend pass:
  - no additional pages recommended before staging; the one-page voter journey remains the clearest product shape
  - starter issue checks now show active selected state and `aria-pressed`
  - narrow evidence cards have tighter spacing and mobile-friendly text wrapping
- First staging deployment:
  - backend is live at `https://political-fingerprint.onrender.com`
  - frontend is live at `https://political-fingerprint.vercel.app`
  - Render-safe coverage route `/coverage/metadata` was added because `/metadata/coverage` did not reliably route through Render
  - frontend coverage metadata fetch falls back from `/metadata/coverage` to `/coverage/metadata`
- Offline manual interpretation workflow:
  - added migration `0003_vote_interpretation_details.sql` for cached plain-English vote meaning fields
  - added `backend/app/etl/manual_interpretations.py`
  - added exporter for bounded source packets from Supabase
  - added importer for reviewed interpretation JSON with neutral-language and schema validation
  - added workflow docs at `docs/manual_interpretation_workflow.md`
- First manual interpretation batch:
  - applied `0002_vote_interpretations.sql` and `0003_vote_interpretation_details.sql` to the configured Supabase database
  - exported `docs/interpretation_batches/batch_001_nc_starter_packets.json`
  - drafted `docs/interpretation_batches/batch_001_nc_starter_interpretations.json`
  - imported 48 records into Supabase with `--reviewed-by codex_manual_review`
  - status mix after import: 24 interpreted, 12 ambiguous, 12 insufficient evidence
- Evidence-row interpretation UI:
  - backend position evidence rows now include cached interpretation status, support/oppose positions, plain-English summary, yea/nay meaning, policy effect, issue facet, confidence, source basis, and uncertainty note
  - frontend evidence rows now render a `DC-Speak Breakdown` block when cached interpretation details or uncertainty notes exist
  - ambiguous and insufficient-evidence votes are shown as evidence limits rather than inferred policy reads

## Active Checkpoint

No active uncommitted checkpoint.

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
- `cd frontend; npm run build` passed for the insufficient-evidence copy checkpoint
- direct API checks passed for ZIP `27701` and Cost of Living alignment returning `insufficient_evidence`
- browser QA for the insufficient-evidence path later completed after restoring the browser helper from the fallback bundled marketplace path
- `cd frontend; npm run build` passed for the insufficient-evidence browser QA fallback checkpoint
- `cd frontend; npm run build` passed for the comparison pair-edit drawer checkpoint
- browser QA passed for the comparison pair-edit drawer checkpoint:
  - ZIP `27701` loads Valerie P. Foushee
  - Cost of Living starter applies selected issues
  - issue comparison renders side-by-side rows
  - `Change Comparison Pair` drawer and search input exist
  - searching `Schiff` and setting the right side updates comparison to Adam B. Schiff
  - no runtime error overlay, stale webpack overlay, `Comparison unavailable`, or `Alignment check unavailable` text appeared
- sandboxed backend fixture runs reached test execution but hit Windows temp-directory cleanup `PermissionError` on `.local\pytest_basetemp*`
- escalated backend fixture suite passed with `$env:DATABASE_URL='postgresql://invalid'; pytest --basetemp=..\.local\pytest_basetemp_comparison_drawer_admin` (`144 passed`)
- `cd frontend; npm run build` passed for the launch trust clarity checkpoint
- browser QA passed for the launch trust clarity checkpoint:
  - ZIP `27701` loads Valerie P. Foushee
  - Cost of Living starter still applies selected issues
  - issue comparison still renders
  - Method, Evidence, and Limits footer notes render once as expected
  - data window remains visible
  - no runtime or stale webpack overlay text appeared
- mobile-path browser smoke before first-screen copy polish reached ZIP lookup, issue starter, evidence, comparison, switch-official search, and trust footer with no runtime overlay
- `cd frontend; npm run build` passed for the first-screen copy polish checkpoint
- browser QA passed for the first-screen copy polish checkpoint:
  - new hero, ZIP, auto-open, and issue-picker copy rendered
  - ZIP `27701` loads Valerie P. Foushee
  - Cost of Living starter selects 3 issues
  - issue comparison renders
  - no runtime or stale webpack overlay text appeared
- `$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_app_config.py tests\test_api_metadata.py tests\test_api_lookup.py` passed (`9 passed`)
- `cd frontend; npm run build` passed for the staging-readiness accessibility/CORS checkpoint
- browser QA passed for the staging-readiness accessibility/CORS checkpoint:
  - default profile path loads
  - Cost of Living starter selects 3 issues
  - issue comparison renders
  - comparison overlay exposes selected state with `aria-pressed`
  - position issue card exposes selected state after selection
  - evidence opens from a selected issue card
  - no runtime or stale webpack overlay text appeared
  - note: the in-app browser helper hit a virtual-clipboard issue when filling ZIP, so this specific QA run used the default loaded profile path for the ARIA checks
- docs guardrail/search check passed for the release-prep staging docs checkpoint; remaining matches are existing guardrail/tasklist references
- `cd frontend; npm run build` passed for the comparison overlay/evidence grouping checkpoint
- browser QA passed for the comparison overlay/evidence grouping checkpoint:
  - issue comparison renders
  - visible `ALL / D / R` toggle is absent from the comparison header
  - `Overlay comparison is set...` copy is absent
  - evidence panel shows roll-call count across bill-or-measure count
  - evidence rows render under bill groups
  - no runtime or stale webpack overlay text appeared
- final local staging verification passed:
  - escalated full backend fixture suite: `$env:DATABASE_URL='postgresql://invalid'; pytest --basetemp=..\.local\pytest_basetemp_final_staging_admin` (`146 passed`)
  - `cd frontend; npm run build` passed
  - local API checks passed for `/health`, `/metadata/coverage`, `/lookup/zips`, and `/lookup/zip/27701`
  - in-app browser rendered the local page with ZIP `27701`, Valerie P. Foushee, issue comparison, removed comparison overlay toggle, switch-official utility, footer trust notes, and no runtime/stale webpack overlay text
  - note: the final click-based browser smoke was partially limited by the in-app browser helper timing out on click actions; prior browser checks in this branch covered starter issue selection, evidence opening, evidence grouping, and comparison rendering
- ZIP comparison preset button-state verification passed:
  - `cd frontend; npm run build` passed
  - browser QA confirmed `aria-pressed` moves from House vs Senator to House vs Other Senator to Compare Senators
  - browser QA confirmed the comparison section updates to Ted Budd vs Thom Tillis after selecting Compare Senators
  - no runtime or stale webpack overlay text appeared
- Evidence metadata compaction verification passed:
  - `cd frontend; npm run build` passed
  - browser QA confirmed evidence rows show `Included as eligible policy vote`
  - browser QA confirmed compact `Source` links render
  - browser QA confirmed raw `policy_vote`, bulky `Classification` labels, runtime overlays, and stale webpack overlays are absent
- Final frontend pass verification passed:
  - first sandboxed `cd frontend; npm run build` hit Windows `spawn EPERM`; escalated rerun passed
  - stale Next webpack overlay appeared after build and was cleared by the documented `frontend/.next` cache reset
  - browser QA confirmed starter checks switch from `Starter Check` to `Active Check`
  - browser QA confirmed active starter checks expose selected state with `aria-pressed`
  - browser QA confirmed evidence still opens, compact source links render, raw `policy_vote` is absent, and no runtime/stale webpack overlay appears
- Staging local release gate passed:
  - sandboxed backend fixture suite reached all tests but hit the known Windows pytest temp cleanup permission issue
  - escalated rerun passed with `$env:DATABASE_URL='postgresql://invalid'; pytest --basetemp=..\.local\pytest_basetemp_release_staging_admin` (`146 passed`)
  - sandboxed frontend build hit Windows `spawn EPERM`
  - escalated rerun of `cd frontend; npm run build` passed
- Render-safe coverage route checkpoint:
  - `$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_api_metadata.py` passed (`2 passed`)
  - sandboxed `cd frontend; npm run build` hit Windows `spawn EPERM`
  - escalated rerun of `cd frontend; npm run build` passed
  - pushed commit `72779f6 Add Render-safe coverage metadata route` to `main`
- Deployed staging smoke check passed:
  - Render checks passed for `/health`, `/coverage/metadata`, `/lookup/zips`, and `/lookup/zip/27701`
  - Vercel first-screen check confirmed title, hero, coverage metadata, ZIP input, and no runtime overlay
  - browser smoke confirmed ZIP `27701`, House profile, senators, Quick Read, active starter check, alignment, comparison, evidence, source links, comparison-pair drawer, footer trust notes, and empty console error log
- Offline manual interpretation workflow verification:
  - first sandboxed targeted pytest hit the known Windows temp permission issue
  - escalated rerun passed with `$env:DATABASE_URL='postgresql://invalid'; pytest --basetemp=..\.local\pytest_basetemp_manual_interpret_admin tests\test_manual_interpretations.py tests\test_migrations.py tests\test_seed.py` (`14 passed`)
- First manual interpretation batch verification:
  - Supabase schema check confirmed new cached interpretation detail columns
  - importer returned `imported_count: 48` with no validation errors
  - Supabase status count check returned 24 interpreted, 12 ambiguous, and 12 insufficient-evidence records
  - targeted backend checks passed with `$env:DATABASE_URL='postgresql://invalid'; pytest --basetemp=..\.local\pytest_basetemp_manual_interpret_admin_3 tests\test_manual_interpretations.py tests\test_migrations.py` (`7 passed`)
- Evidence-row interpretation UI verification:
  - `$env:DATABASE_URL='postgresql://invalid'; pytest --basetemp=..\.local\pytest_basetemp_interpret_ui tests\test_api_positions.py tests\test_db_read_layer.py` passed (`11 passed`)
  - sandboxed `cd frontend; npm run build` hit Windows `spawn EPERM`
  - escalated rerun of `cd frontend; npm run build` passed
  - direct Supabase-backed backend response check confirmed `leg_valerie_p_foushee` `ECONOMY_TAXES` evidence rows now include cached interpretation fields

If the dev server is running and the browser looks stale, clear the Next cache before refresh:

```powershell
netstat -ano | findstr :3000
Stop-Process -Id <PID> -Force
Remove-Item -LiteralPath frontend\.next -Recurse -Force
Start-Process -FilePath npx.cmd -ArgumentList 'next','dev','-H','127.0.0.1','-p','3000' -WorkingDirectory '<repo>\frontend' -WindowStyle Hidden
```

## Next Product Tasks After Commit

Work from `docs/product_v2_tasklist.md` in this order:

1. Smoke-test the deployed evidence-row interpretation UI after Render/Vercel redeploy.
2. Add neutral issue pattern cards that aggregate cached interpreted vote meanings.

## Operating Mode

- Batch 2-4 related changes per checkpoint.
- Prefer targeted tests during development.
- Run full frontend build before UI commits.
- Avoid browser automation unless visual behavior is uncertain.
- Keep this file updated before stopping if work is incomplete.
