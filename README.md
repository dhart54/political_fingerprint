# Political Fingerprint

Deterministic civic analytics platform for understanding observable legislative behavior.

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

## Verification Workflow

Use [docs/development_workflow.md](/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/development_workflow.md) for the fixture-mode, Supabase-mode, frontend build, and Windows Next.js cache reset commands.
