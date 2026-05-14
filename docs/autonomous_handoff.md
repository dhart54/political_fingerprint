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

## Active Checkpoint

Checkpoint target: `Polish alignment empty states and neutral copy`.

Files in this checkpoint:

- `frontend/components/AlignmentPanel.js`
- `frontend/components/IssuePreferencePanel.js`
- `frontend/components/SummaryPanel.js`
- `docs/product_v2_tasklist.md`
- `docs/autonomous_handoff.md`

Intent of current changes:

- remove build-stage copy from the preference picker
- add explicit idle, loading, empty, mixed, and insufficient-evidence states
- remove a prohibited-term-adjacent public UI mention from the summary helper copy
- mark neutral-copy and state-polish tasks complete

## Verification Already Run For Current Work

Latest committed comparison checkpoint verification:

```powershell
$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_api_alignment.py tests\test_api_compare.py
npm run build
```

Reported results:

- `10 passed`
- frontend build passed

Current checkpoint still needs verification:

- `cd frontend; npm run build` passed
- browser smoke test attempted, but the in-app browser blocked `http://127.0.0.1:3000/` and `http://localhost:3000/` with `ERR_BLOCKED_BY_CLIENT`

If the dev server is running and the browser looks stale, clear the Next cache before refresh:

```powershell
netstat -ano | findstr :3000
Stop-Process -Id <PID> -Force
Remove-Item -LiteralPath frontend\.next -Recurse -Force
Start-Process -FilePath npx.cmd -ArgumentList 'next','dev','-H','127.0.0.1','-p','3000' -WorkingDirectory '<repo>\frontend' -WindowStyle Hidden
```

After verification, stage and commit these checkpoint files:

```powershell
git add frontend/components/AlignmentPanel.js frontend/components/IssuePreferencePanel.js docs/product_v2_tasklist.md docs/autonomous_handoff.md
git commit -m "Polish alignment states"
```

## Next Product Tasks After Commit

Work from `docs/product_v2_tasklist.md` in this order:

1. Make each quick-read claim traceable to evidence rows.
2. Decide whether generic comparison remains useful as secondary context.
3. Document fixture-mode versus Supabase-mode verification commands.
4. Document Windows Next.js cache reset workflow.
5. Improve ZIP coverage beyond fixture/demo mappings.

## Operating Mode

- Batch 2-4 related changes per checkpoint.
- Prefer targeted tests during development.
- Run full frontend build before UI commits.
- Avoid browser automation unless visual behavior is uncertain.
- Keep this file updated before stopping if work is incomplete.
