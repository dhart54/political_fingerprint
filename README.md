# Political Fingerprint

Deterministic civic analytics platform for understanding observable legislative behavior.

North star:

**Who represents me, how are they acting on the issues I care about, and what can I do next?**

The current product proves the first layer with current federal officials, interpreted vote records, issue preferences, and evidence drilldowns. The next product layer adds neutral civic actions for current representatives: contact, ask, thank, and track. Election and challenger context remains secondary and uses an evidence ladder: recorded governing behavior first, institutional record second, sourced stated positions third, and insufficient evidence when sources are weak or missing.

## Repository Structure

- `backend/` FastAPI application, ETL, metrics, tests, and migrations
- `frontend/` Next.js application
- `docs/` methodology and project documentation
- `scripts/` local utility scripts

## Local Setup

1. Copy `backend/.env.example` to `backend/.env`.
2. Copy `frontend/.env.example` to `frontend/.env.local`.
3. Use the task-defined commands as implementation progresses.

## Fastest Real-Data Path

See [docs/real_data_runbook.md](/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/real_data_runbook.md) for the quickest route to load a starter House+Senate real dataset into Postgres and then view it through the existing frontend.

## Product Direction

- [Product North Star](docs/product_north_star.md)
- [North-Star Action Plan](docs/north_star_action_plan.md)
- [Product Roadmap](docs/product_v2_tasklist.md)

## Verification Workflow

Use [docs/development_workflow.md](/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/development_workflow.md) for the fixture-mode, Supabase-mode, frontend build, and Windows Next.js cache reset commands.

## Deployment

Use [docs/deployment.md](/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/deployment.md) for the Render backend and Vercel frontend deployment checklist.

## Accessibility and Mobile Checks

Use [docs/accessibility_mobile_checklist.md](/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/accessibility_mobile_checklist.md) before sharing the voter journey outside development.

## Monitoring

Use [docs/monitoring.md](/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/monitoring.md) for the lightweight production monitoring and privacy guardrails.
