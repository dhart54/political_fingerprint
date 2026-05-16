# Staging Readiness

This is the release-prep checklist for sharing Political Fingerprint in a staging environment.

## Current Status

The main voter path is ready for staging review:

- ZIP lookup loads a House representative and two senators.
- The House profile opens automatically after lookup.
- Quick Read summarizes issue focus, vote direction, data volume, and drift context.
- Starter issue checks let users select a useful bundle quickly.
- Alignment labels remain evidence-based: aligned, not aligned, mixed, or insufficient evidence.
- Evidence drilldowns expose roll calls, vote position, classification reason, and source URL when available.
- Comparison keeps selected issues primary and supports changing the comparison pair.
- The footer explains method, evidence, limits, and data window.

Public staging URLs:

- Backend: `https://political-fingerprint.onrender.com`
- Frontend: `https://political-fingerprint.vercel.app`

## Latest Local Verification

Last local release-prep check: 2026-05-15.

Passed:

- full backend fixture suite: `146 passed`
- frontend production build: `npm run build`
- local API checks:
  - `GET /health`
  - `GET /coverage/metadata`
  - `GET /lookup/zips`
  - `GET /lookup/zip/27701`
- in-app browser rendered the local page without runtime or stale webpack overlay text
- rendered page confirmed ZIP `27701`, Valerie P. Foushee, issue comparison, removed comparison overlay toggle, switch-official utility, and footer trust notes

Browser automation note:

- click-based browser smoke was partially limited by the in-app browser helper timing out on click actions
- prior browser checks in this branch covered starter issue selection, evidence opening, evidence grouping, and comparison rendering after the same code path

## Intentional Limits

These are acceptable for staging and should not block review:

- Loaded ZIP coverage depends on the current Supabase or fixture dataset.
- Alignment can show insufficient evidence when vote meaning is not source-grounded.
- Live data refreshes are still manual.
- The product does not order politicians, infer motive, or tell users how to vote.
- The lower switch-official search is an exploration utility, not the primary path.

## Required Environment

Backend on Render:

```text
DATABASE_URL=<supabase-postgres-pooler-url>
CLASSIFICATION_VERSION=v1
FRONTEND_ORIGINS=https://<vercel-project>.vercel.app
CONGRESS_API_KEY=<optional-for-live-ingestion>
```

Frontend on Vercel:

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-service>.onrender.com
```

## Pre-Deploy Checks

Run locally before promoting a branch:

```powershell
cd backend
$env:DATABASE_URL='postgresql://invalid'
pytest --basetemp=..\.local\pytest_basetemp_release
```

```powershell
cd frontend
npm run build
```

If Windows blocks pytest temp cleanup in the sandbox, rerun the backend suite outside the sandbox with a fresh `--basetemp` path.

## Backend Checks

After Render deploy:

```text
GET https://<render-service>.onrender.com/health
GET https://<render-service>.onrender.com/coverage/metadata
GET https://<render-service>.onrender.com/lookup/zips
GET https://<render-service>.onrender.com/lookup/zip/<loaded-zip>
```

Expected:

- `/health` returns `{"status":"ok"}`.
- `/coverage/metadata` returns window dates, roll-call counts, and source-link share.
- `/lookup/zips` returns at least one loaded ZIP mapping.
- `/lookup/zip/<loaded-zip>` returns a House representative and senators.

## Frontend Checks

After Vercel deploy:

1. Open the Vercel URL.
2. Confirm the hero coverage line loads from Render.
3. Use a loaded ZIP suggestion.
4. Confirm the House profile opens automatically.
5. Select `Cost of Living`.
6. Confirm alignment cards render.
7. Open `Inspect Votes`.
8. Confirm evidence rows or an insufficient-evidence state render.
9. Confirm `Issue Comparison` renders the same selected issues.
10. Open `Change Comparison Pair` and search for another official.
11. Confirm Method, Evidence, Limits, and Data window appear in the footer.

Latest deployed smoke check: 2026-05-16.

Passed:

- Render `GET /health`
- Render `GET /coverage/metadata`
- Render `GET /lookup/zips`
- Render `GET /lookup/zip/27701`
- Vercel page loads with the expected title and hero
- hero coverage line loads from Render
- ZIP `27701` loads Valerie P. Foushee, Ted Budd, and Thom Tillis
- `Cost of Living` starter check becomes active and selects three issues
- alignment and issue comparison render without unavailable states
- evidence opens, bill groups render, source links remain visible, and raw `policy_vote` does not appear
- `Change Comparison Pair` drawer exposes search
- Method, Evidence, Limits, and data window render in the footer
- browser console error log was empty during the smoke path

## Staging Review Focus

Reviewers should answer:

- Can a new user understand the first screen in under 10 seconds?
- Does the ZIP-to-issues path feel quick?
- Are insufficient-evidence states clear rather than broken-looking?
- Are source links and classification reasons easy enough to find?
- Does the comparison view feel descriptive instead of persuasive?
- Does any copy sound like a voting recommendation?
