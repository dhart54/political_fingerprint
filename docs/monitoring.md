# Lightweight Monitoring

The goal is basic production visibility without pushing the project over the monthly cost target.

## Backend

Start with platform logs and health checks.

Render checks:

- watch deploy logs after every release
- verify `GET /health`
- verify `GET /coverage/metadata`
- verify one known `GET /lookup/zip/{zip_code}` request

Recommended log signals:

- repeated 500 responses
- database connection failures
- empty coverage metadata after a deployment
- ZIP lookup 404 spikes after data refreshes
- alignment endpoint errors

Keep backend error responses explicit and neutral. Do not hide API failures behind invented fallback claims on the client.

## Frontend

Start with Vercel deployment logs and browser console checks.

Recommended checks after deploy:

- home page loads without client-side errors
- hero coverage metadata loads
- ZIP suggestions render
- issue preference selection updates alignment
- evidence buttons open the evidence panel

If a paid tool is later justified, add one low-volume frontend error tracker and sample conservatively. Do not add monitoring that captures personal political preferences or user-entered issue selections.

## Privacy Guardrails

Do not log:

- user issue preferences
- ZIP lookups tied to a persistent user id
- inferred alignment results tied to an identifiable user
- any prescriptive voting language

Safe to log:

- endpoint path
- status code
- response time
- coarse deployment environment
- aggregate error counts

## Manual Release Checklist

Before sharing a deployment, run the fuller staging sequence in `docs/staging_readiness.md`. Minimum checks:

1. Run backend fixture tests.
2. Run frontend build.
3. Confirm Render `/health`.
4. Confirm Render `/coverage/metadata`.
5. Confirm Vercel can reach the Render API.
6. Run one ZIP lookup.
7. Open one evidence panel.
8. Check logs for backend or frontend errors.
