# Deployment

Political Fingerprint deploys as two services:

- backend API on Render: https://political-fingerprint.onrender.com
- frontend Next.js app on Vercel: https://political-fingerprint.vercel.app

Use `docs/staging_readiness.md` for the exact staging checklist before sharing a deployment.

Official references:

- Render FastAPI deployment: https://render.com/docs/deploy-fastapi
- Vercel Next.js deployment: https://vercel.com/docs/concepts/next.js/overview
- Vercel environment variables: https://vercel.com/docs/environment-variables

## Backend - Render

Create a Render Web Service from the repository.

Recommended settings:

- Root Directory: `backend`
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Environment variables:

```text
DATABASE_URL=<supabase-postgres-pooler-url>
CLASSIFICATION_VERSION=v1
FRONTEND_ORIGINS=https://<vercel-project>.vercel.app
CONGRESS_API_KEY=<optional-for-live-ingestion>
```

Render provides `$PORT` at runtime. The backend start command must bind to `0.0.0.0` and use `$PORT`.

Post-deploy checks:

```text
GET https://political-fingerprint.onrender.com/health
GET https://political-fingerprint.onrender.com/coverage/metadata
GET https://political-fingerprint.onrender.com/lookup/zips
```

Expected behavior:

- `/health` returns `{"status":"ok"}`
- `/coverage/metadata` returns window and source coverage metadata
- `/lookup/zips` returns the loaded ZIP mappings from Supabase, or fixture fallback if the database is unavailable

Operational hardening target: backend health or coverage metadata should make fixture fallback visible. When production data is expected, release checks should confirm the response reports the live database source and expected precompute window, not only that the endpoint shape is valid.

## Frontend - Vercel

Create a Vercel project from the same repository.

Recommended settings:

- Framework Preset: Next.js
- Root Directory: `frontend`
- Build Command: `npm run build`
- Install Command: default is acceptable
- Output Directory: default is acceptable

Environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://political-fingerprint.onrender.com
```

`NEXT_PUBLIC_API_BASE_URL` is read by client-side code, so it must be set for the Vercel environment before building the deployment.

Post-deploy checks:

1. Open https://political-fingerprint.vercel.app.
2. Confirm the hero coverage line loads from the Render API.
3. Run a ZIP lookup using one of the loaded ZIP suggestions.
4. Open a House profile.
5. Select one issue preference and confirm the alignment section loads.
6. Open vote evidence from Quick Read or alignment.

## CORS

The backend always allows local frontend origins. For staging or production, set `FRONTEND_ORIGINS` to a comma-separated list of deployed frontend origins.

Example Render value:

```text
FRONTEND_ORIGINS=https://political-fingerprint.vercel.app,https://<custom-domain>
```

Keep the list explicit. Do not use a wildcard origin for production.

## Data Refresh

For the current product state, prioritize product quality over scheduled data pulls.

Manual refresh path:

```powershell
cd backend
python -m app.etl.run_all --fixtures
```

Use live ingestion only after the interpretation and evidence flows are stable enough to justify routine pulls.

## Cost Notes

To stay under the project cost target:

- keep shared aggregates precomputed in Supabase
- avoid runtime recomputation of fingerprints, medians, drift, summaries, or interpretations
- keep frontend rendering static/client-side against API reads
- schedule data refreshes only after the product flow is worth refreshing
