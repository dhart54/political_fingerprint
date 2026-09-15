# Isolated normalized green build and cutover review

Status: managed-green validation passed; final exact-head CI/retry results are recorded on the draft PR. Not cutover authority.

## Bound identities
- Accepted normalization head: 3de786cc1e536d90eeb2b38f36c87b9b9cb447ca.
- Merged main / backend implementation: 638eac771e2d32db27258716c6334e2a7d7ea089.
- Blue: wfhnmuxlbfpweupisfao, session pooler aws-1-us-east-1.pooler.supabase.com:5432, postgres, us-east-1, PostgreSQL17.6.
- Green: yalpfkaxkxebwolhorha, session pooler aws-0-us-east-1.pooler.supabase.com:5432, postgres, us-east-1, PostgreSQL17.6, Free/Nano. Public traffic is not routed here.
- Render: srv-d84abkuq1p3s738qd1i0, backend directory, pip install -r requirements.txt; no pre-deploy command; uvicorn app.main:app --host 0.0.0.0 --port $PORT.

## Fresh source and package
Capture time: 2026-09-15 03:23:25.792161+00:00. Capture manifest SHA256: 0d34a073f3bfcd1a3118d60602c9bc3c95a651991416a113bbe48f6584e3f71a.
Package manifest SHA256: dc49918d0d169728583f9bcad17d9a36075cb5a7b6839a932c7c3dd09fb2b745.
Normalized custom dump SHA256: d257544a83b6d4678387973d64668149b9a1e30de9b30b4de2624bb6f18feceb.
Normalized SQL SHA256: e9dc11ddeec423c264ab3c35e201e49b1fc0b16fbf1c6ec23fc4b425a49ad2f6.

Fresh capture uses an exported REPEATABLE READ READ ONLY snapshot for the native pg_dump and all rows/hashes. It preserves exact primary keys, timestamps, source identities, all stored analytics, 158 editorial artifacts, eight batches, 167 relationships, and four registry roots. All17 sequence states are checked before/after capture. No source recomputation or cleanup.

A native restore exposed two serialization hazards in the earlier fixture-based comparison: Supabase defaults extra_float_digits=0, which rounds text output, and ORDER BY first two columns is not a total order for some composite primary keys. Exact capture/hash comparison now uses extra_float_digits=3 and the complete primary key. This preserves the underlying stored float values; it does not round or discard data. API comparisons use the actual blue/green runtime default0. The original immutable CI fixture is not replaced. Historical normalization semantics are unchanged.

## Writer inventory and freeze
Render workspace has one project, one Production environment and one Python web service; no worker or cron service. Build/start commands do not write data. Repository has no scheduled GitHub workflow or runtime scheduler. Alignment POST computes a response without persistence. No matching local scheduled task by name or action. Blue cron is absent, realtime publication has no tables, service state is empty. Manual ETL/editorial operators remain paused. No blue database writes were used to freeze it. Repeat source hash/sequence checks immediately before load and again before any future cutover; if changed, stop for a fresh validated capture.

## Safety and managed-service reconciliation
The accepted disposable runner is unchanged. A separate operator binds exact blue/green identities, accepted main, source capture, package/SQL/guard/permissions digests, empty destination schema and load mode. An explicit --confirm-green-load is required before connection/write work. Blue connections default read-only and use read-only transactions. Only the exact green DSN reaches psql. Load uses --single-transaction and ON_ERROR_STOP with an in-transaction empty-schema guard and advisory lock. Exact completed-state retries report zero writes; partial/conflicting state is refused. There is no cleanup, blue-mutation, deployment or cutover mode.

Only public application objects are loaded. Supabase-managed roles/passwords/schemas are not restored. Schema-public creation/ownership/ACL dump entries are excluded; application RLS/triggers/functions/types are retained. Explicit post-load revokes protect public tables/views/sequences/functions and future defaults from anon/authenticated/PUBLIC. Data API is disabled. No GitHub integration, add-on or paid plan was enabled. Green lacks pg_graphql because Data API is disabled; the app has no dependency on it. Existing pgcrypto, uuid-ossp, plpgsql, pg_stat_statements and vault extensions are retained, not overwritten. Auth/Storage/Vault/Realtimes subscriptions and migration-history/service inventories are empty; any population is a stop condition.

## Validation
Fresh local PG17 proof passed: all28 original logical table streams, all17 sequences, 525 complete API outputs across15 members and118/119/all, all active adapters, insertion/repeat, shared drift, compatibility CRUD, migration ambiguity rollback, exact rollback and fresh dump/restore. Fresh compact restore:229,919,891 bytes. API digest:18ef4e9d0258757d39db93b3ad0581088a55b7798c0ea6611115cdb415d266ab. Full original float precision is also verified against the actual native source dump.
Focused operator/normalization tests:12 passed. Actual managed-green and exact-head CI results are attached to the draft PR and final report.

## Exact later cutover sequence — DO NOT EXECUTE NOW
1. Confirm manual operators remain paused and repeat full blue source/sequence/schema identity and green package/parity checks. Stop on any delta. Confirm independent acceptance of actual-green proof and resolve the previously disclosed automatic-deploy exception.
2. Confirm green yalpfkaxkxebwolhorha, PostgreSQL17.6, expected package digest and measured size below400MB. Preserve current blue credentials and prior accepted backend deployment identity outside Git.
3. In Render service srv-d84abkuq1p3s738qd1i0 > Environment, replace DATABASE_URL with the protected green session-pooler URL and set NORMALIZED_VOTE_STORAGE=1. Do not paste credentials into terminal command history, Git or reports. This change can trigger deployment; explicit cutover authority is required before saving it.
4. Deploy exactly 638eac771e2d32db27258716c6334e2a7d7ea089 (or a separately reviewed replacement). Confirm /health reports this SHA, and establish database provenance using the green target identity and exact public read parity. No schema migration/startup ETL is part of this deploy.
5. Run full read-only parity across15 members,118/119/all and all domains, including positions/evidence/fingerprints/editorial/summaries/drift; confirm all four Foushee roots and accepted wording. Confirm database-source provenance and green measured size.
6. Keep all writers paused pending explicit acceptance. No fake durable action and no M15B persistence/activation. Only after acceptance may separately permitted routine writers resume with NORMALIZED_VOTE_STORAGE=1.
7. Vercel requires no URL change: it continues calling https://political-fingerprint.onrender.com. No public API contract or frontend code changed. Verify the deployed frontend uses that same URL; do not update Supabase keys in frontend because this app uses backend-only Postgres access.

## Exact rollback before production writes resume
Restore blue DATABASE_URL for wfhnmuxlbfpweupisfao, set NORMALIZED_VOTE_STORAGE=0, restore the prior accepted backend code/configuration (pre-merge accepted main5843bab9b1bed3e5db57976bae3b05466f2cbafe), and deploy/restart as required. Verify health SHA, blue identity, database provenance, original source/sequence/registry hashes and the complete read-only smoke. Retain green for diagnosis. Do not delete, pause, compact or migrate blue. Once green has accepted production writes, stop: connection rollback alone is insufficient and requires separate reviewed reconciliation.

## Disclosed integration deviation
PR188 merge triggered the pre-existing Render deploy hook despite this milestone's deployment restriction. Live backend now reports638eac771e2d32db27258716c6334e2a7d7ea089; no configuration or database write accompanied it. No further deploy or revert was performed. Automatic smoke fails on nonexistent leg_alex_morgan (404), while health and checked Foushee routes return200. Post-merge backend CI passed. This exception remains disclosed for the user's disposition; it does not authorize cutover.

## M15B and remaining boundary
M15B remains paused. After a future accepted cutover it needs new target identity, fresh baseline/runtime/preflight, refreshed persistence preparation and separate authorization. Current task stops before Render/Vercel changes, routing traffic, production writers or blue retirement.

References: https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore and https://www.postgresql.org/docs/17/app-pgrestore.html.

## Actual green load and final recheck binding
Initial atomic application load succeeded:232,156,307 bytes; all28 logical streams and17 sequences exact. Managed API/role/ETL proof passed. Final verification manifest ae88c92bc33352046527e25caf4638fd7ab68e510bd8975e18a0011bc5a02eea retains identical source/package/SQL identities and adds native-restored source-schema binding530b43ca6da9863237c827188d67f75844abf214b6df5c20cd54c944803710c7. Original load manifest retained; no data/package regenerated. Focused guards plus historical checks34 passed. Deployed Vercel bundle app/page-90ba53cd2230a3c3.js embeds https://political-fingerprint.onrender.com; no frontend configuration change is needed.

## Managed Supabase result
Actual green PostgreSQL17.6 proof passed. Database231,500,947 bytes (initial load232,156,307; normal managed maintenance/packing accounts for the small physical difference). Member relation100,302,848 bytes, roll relation2,113,536 bytes. All28 logical table streams,17 sequences, complete editorial content/provenance and registry rows match after rollback-only writes. All525 complete API outputs match, digest18ef4e9d0258757d39db93b3ad0581088a55b7798c0ea6611115cdb415d266ab.

Actual managed postgres connection has rolsuper=false and rolbypassrls=true, matching the existing backend connection class rather than the local superuser. Every protected table/view/sequence denies anon/authenticated privileges, and actual SET ROLE SELECT on vote_contexts fails for both. security_invoker=true is verified. All active ETL adapters, repeated equal ingestion, shared drift rejection, compatibility insert/update/delete and exact rollback passed; zero durable synthetic records and original sequence values retained. Data API is disabled in project settings; unauthenticated REST access returns401. No service-state population or realtime-published table was introduced.

Managed-green median query times: history7.345ms, issue evidence0.619ms, fingerprint2.887ms, roll lookup0.222ms, batch17.432ms. All pass the accepted practical bound; hardware differs from the local clone, so these are not presented as isolated normalization overhead.

Source schema digest is independently restored from the fresh native dump and rechecked against blue. Final completed-state retry must report writes=0. Exact-head hosted results and final disposition are recorded in PR189 without embedding a self-referential commit hash here.
