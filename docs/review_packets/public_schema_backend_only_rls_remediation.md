# Public Schema Backend-Only RLS Remediation

## Security Advisor Finding

Supabase Security Advisor reported `rls_disabled_in_public`: tables in the API-exposed `public` schema did not have Row Level Security enabled.

This was treated as a bounded production security remediation. The production migration has already been applied and validated.

## Affected Tables

The read-only production inventory found RLS disabled on these 17 `public` tables:

- `bills`
- `candidate_evidence`
- `chamber_medians`
- `drift_scores`
- `fingerprints`
- `legislator_contacts`
- `legislators`
- `race_candidates`
- `roll_calls`
- `senate_amendment_references`
- `summaries`
- `upcoming_races`
- `vote_classifications`
- `vote_contexts`
- `vote_interpretations`
- `votes_cast`
- `zip_district_map`

Prior state:

- RLS disabled on every table above.
- No RLS policies existed.
- `anon` and `authenticated` had broad table privileges.
- `postgres` and `service_role` had table privileges.

## Confirmed Application Access Model

Repository inspection confirmed the browser does not access Supabase directly. The frontend calls the Render API through `NEXT_PUBLIC_API_BASE_URL`. The backend uses direct Postgres through `DATABASE_URL` via `psycopg`.

Intended table access model:

- backend-only through Render/direct Postgres;
- no browser Supabase Data API access;
- no `anon` or `authenticated` table access required.

No secret values, connection strings, or tokens are included in this artifact.

## Migration Behavior

Migration:

`backend/migrations/0011_public_schema_backend_only_rls.sql`

The migration:

- revokes all table privileges in `public` from `anon` and `authenticated`;
- revokes all sequence privileges in `public` from `anon` and `authenticated`;
- revokes future default table and sequence privileges in `public` from `anon` and `authenticated`;
- enables RLS on exactly the 17 affected public tables;
- creates no permissive public policies;
- performs no row-data insert, update, delete, or truncate;
- leaves backend direct Postgres access intact.

## Rollback Behavior And Warning

Rollback artifact:

`docs/review_packets/public_schema_backend_only_rls_rollback.sql`

The rollback targets the same 17 tables, disables RLS, and restores broad `anon` and `authenticated` grants.

Warning: the rollback restores the previously insecure public-schema posture. It should be used only as an emergency service-restoration measure. A forward fix that preserves RLS is preferred if backend access fails. Running rollback may reintroduce anonymous/authenticated Supabase Data API access.

## Production Application Status

Production remediation was applied on June 16, 2026.

Post-application SQL validation confirmed:

- all 17 tables have `relrowsecurity = true`;
- `anon` and `authenticated` table grants are removed;
- no public RLS policies exist;
- anonymous read attempts fail with `permission denied`;
- authenticated read attempts fail with `permission denied`;
- anonymous write attempts fail with `permission denied`;
- backend direct Postgres access remained operational;
- public frontend and Render API smoke checks still passed.

No row data changed.

## Render Smoke Workflow

The original `Render backend smoke` run failed because `RENDER_DEPLOY_HOOK_URL` was absent and `/health` timed out while the backend was not redeployed. After the repository secret was configured, the rerun succeeded:

- deploy hook triggered;
- wait step completed;
- `/health` passed;
- Valerie `/positions` included `interpreted_total`;
- Valerie evidence included `interpretation_status`.

## Log And Rotation Notes

Database-visible activity showed expected Supabase/PostgREST/Supavisor/admin sessions and expected historical app/import statements under `postgres`. Those database views do not provide full IP/origin API audit detail.

Key rotation is not currently required absent evidence of secret exposure or suspicious access. The anon key is public by design; the important remediation was removing its table access.

## Manual Follow-Up

- Refresh Supabase Security Advisor and confirm `rls_disabled_in_public` clears.
- Inspect Supabase dashboard API/database logs for anonymous writes, deletes, or bulk reads from unexpected origins or IP patterns.
- Avoid rollback unless necessary for emergency service restoration.
- Prefer a forward fix that keeps RLS enabled if any backend access issue is discovered.