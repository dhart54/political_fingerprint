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

## Active Checkpoint

Checkpoint target: `Reframe comparison around selected issues`.

Files in this checkpoint:

- `frontend/app/page.js`
- `frontend/components/ComparisonPanel.js`
- `docs/product_v2_tasklist.md`
- `docs/autonomous_handoff.md`

Intent of current changes:

- pass `issuePreferences` into comparison
- fetch alignment for both comparison sides
- show a `Your Issues` comparison metric for each side
- mark Phase 7 comparison reframe tasks in the tasklist

## Verification Already Run For Current Work

Backend focused tests passed, though the shell wrapper timed out after output:

```powershell
$env:DATABASE_URL='postgresql://invalid'; pytest tests\test_api_alignment.py tests\test_api_compare.py
```

Reported result:

- `10 passed`

## Still Needed For This Checkpoint

1. Run frontend build:

```powershell
cd frontend
npm run build
```

2. If the dev server is running, clear stale Next cache before browser refresh:

```powershell
netstat -ano | findstr :3000
Stop-Process -Id <PID> -Force
Remove-Item -LiteralPath frontend\.next -Recurse -Force
Start-Process -FilePath npx.cmd -ArgumentList 'next','dev','-H','127.0.0.1','-p','3000' -WorkingDirectory '<repo>\frontend' -WindowStyle Hidden
```

3. Stage and commit these checkpoint files:

```powershell
git add frontend/app/page.js frontend/components/ComparisonPanel.js docs/product_v2_tasklist.md docs/autonomous_handoff.md
git commit -m "Reframe comparison around selected issues"
```

## Next Product Tasks After Commit

Work from `docs/product_v2_tasklist.md` in this order:

1. Preserve neutral copy review for alignment/comparison UI.
2. Improve empty, mixed, and insufficient-evidence states in the preference/alignment flow.
3. Make quick-read claims traceable to evidence rows.
4. Decide whether generic comparison remains useful as secondary context.
5. Document fixture-mode versus Supabase-mode verification commands.

## Operating Mode

- Batch 2-4 related changes per checkpoint.
- Prefer targeted tests during development.
- Run full frontend build before UI commits.
- Avoid browser automation unless visual behavior is uncertain.
- Keep this file updated before stopping if work is incomplete.
