# Validated green Supabase build

## Intent and scope
Build an isolated normalized green target from a fresh unchanged blue snapshot. Stop before cutover. Preserve accepted normalization implementation and all editorial history. No blue writes, production configuration changes, live deployments, M15B activation, or destructive project cleanup.

## Baseline
Accepted PR188 head 3de786cc1e536d90eeb2b38f36c87b9b9cb447ca merged at 638eac771e2d32db27258716c6334e2a7d7ea089. New branch codex/green-normalized-migration. Blue wfhnmuxlbfpweupisfao; green yalpfkaxkxebwolhorha, same us-east-1 region, Free/Nano. Unrelated root work and ZIPs remain untouched.

## Decision envelope and sequence
1. Inventory writers and target/service state read-only; establish no autonomous mutation during capture.
2. Capture public schema/data, sequences, governance and logical hashes using an explicitly read-only source connection.
3. Normalize on a dedicated local PostgreSQL17 clone; run full original-column/API/sequence/ETL/performance proof and fresh restore.
4. Bind a separate green executor to exact source/destination, source/package hashes, accepted main and mode; reject nonempty or partial state. Preserve disposable guard.
5. Load only compact application state into green with explicit confirmation; preserve Supabase-managed schemas/roles/settings.
6. Prove actual managed-green data/API/security/ETL/size parity; prepare precise cutover/rollback and one draft PR.

## Definition of done
- [x] Fresh frozen source capture and hashes
- [x] Target-bound executor and focused safety tests
- [x] Full local PostgreSQL17 proof
- [ ] Actual green parity, security and size proof
- [ ] Review packet, cutover/rollback procedure, draft PR

## Discoveries and deviations
PR188 merge unexpectedly triggered existing Render deploy hook; live backend now reports merge SHA. No configuration changes or database writes occurred. This was reported immediately; do not perform another deployment. Automatic smoke fails for nonexistent leg_alex_morgan (404); checked Foushee endpoints return200. Merge backend CI passes.
Previous read-only audit at 2026-09-15 03:04:45 UTC found unchanged 28 table counts, all17 sequences, editorial hashes and four roots; zero shared ambiguity; services empty and cron absent. Local PG17.5 binaries available; existing local PG17/18 services must not be altered.

## Validation / progress
Implementation in progress. Green initially Coming up. Password remains protected outside Git; never log DSNs or credentials.

## Writes and rollback
Blue writes: no. Green writes: none yet. Green load must be atomic and refuse partial/conflicting state; no destructive cleanup. Before production writers resume, future rollback restores blue URL, legacy flag and prior backend deployment. After green production writes, separate reconciliation is required.

## Blockers / final reconciliation
Await green readiness and protected connection credential. Complete hosted writer inventory and verify exact managed-green state before readiness. Cutover remains prohibited.

Writer inventory: Render workspace has one project/environment and one Python web service, no worker/cron service. Build pip install; no pre-deploy command; start uvicorn only. Repository has no scheduled workflow or application scheduler; alignment POST computes a response without persistence. No matching Windows scheduled tasks. Supabase cron absent and service data empty in read-only inventory. No autonomous writer identified; manual ETL/editorial operators remain paused throughout this task. No database write was used to freeze blue.

Green initial load succeeded:232,156,307 bytes,28 logical streams and17 sequences exact. Managed API/role/ETL proof in progress.34 local guard/historical tests passed. Source-schema binding strengthened for final recheck/retry; original execution manifest retained.
