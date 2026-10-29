# Positions read connection experiment

Intent: test whether serial precomputed reads can share a positions-worker-owned
connection while preserving every existing query and transaction boundary.
Base: d43425905207ef66e5268edbe0e36252f79ff4d8; prior work preserved.
Branch: codex/positions-read-connection-experiment. Production remains unchanged.

Scope: db.py opt-in helper, precomputed query helper, positions handler only,
focused tests and a disposable local benchmark. Publication loader, repositories,
global connection API, other endpoints and writers retain independent ownership.
No SQL/order/parameter, caching, pooling, concurrency, isolation/autocommit policy,
editorial, schema, infrastructure or deployment change is authorized.

Sequence: implement lazy worker-owned scope; test ownership/fault/parity contracts;
run disposable loopback PostgreSQL transaction tests and paired benchmark; freeze
exact files for existing reviewer; save verified shutdown archive by 19:04 UTC.

Definition of done: unchanged response/query contracts, per-query rollback and
cursor cleanup, isolated worker lifetime including late cancellation, real local
transaction checks, measured local baseline/candidate comparison, independent
review and durable shutdown checkpoint. Partial work remains explicitly partial.

Design: ContextVar plus owner-thread/active/borrow guards. Successful reads rollback
before reuse; failed query/reset discards connection. Final owner cleanup never
runs from ASGI final-send. No request-wide transaction or committing context.
Retain legacy injectable precomputed.get_connection seam for existing tests.

Evidence limits: two retained production positions records showed 44–53 percent
connection wall time; this does not establish production gains or historic tail
causes. Local benchmarks are not production measurements.

Progress: implementation complete; 158 focused tests passed, including four
real disposable PostgreSQL cases (READ COMMITTED/REPEATABLE READ snapshot refresh,
idle transaction boundaries, transaction-local session/prepared-state reset,
failed-query disposal). Actual ASGI cancellation with a continuing sync worker,
copied-context/thread guards, faults, all scopes, four-domain dispatch and query
order/parameter parity are covered. Existing publication/receipt tests pass.

Final guarded benchmark: eight paired trials, one warmup pair, alternating mode
order, 39 identical synthetic parameterized SELECTs per trial on owned loopback
PostgreSQL 17.5, psycopg 3.3.3, no injected latency. Baseline median 595.483 ms
(407.935–898.546), candidate median 16.614 ms (15.028–118.133); 39 versus one
connection. Raw results: .tmp/positions-reuse/benchmark-final.json. This is a
synthetic local microbenchmark, not a full API or production performance result.

Corrections: Windows inherited pipe handles stalled initial pg_ctl subprocess
capture; stopped the owned cluster normally and switched command output to files.
An initial file-backed initdb log placement made its data directory nonempty;
moved command logs outside it. Independent review identified inherited PGHOSTADDR
redirection risk; helper now pins hostaddr and refuses inherited libpq settings
without inspecting their values. An attempted empty service override failed
closed locally and was replaced with that explicit environment guard. Pre-guard
results are historical, superseded by final guarded tests/benchmark. Each
successful cluster verified its exact owned data-directory identity. No claim
that the pre-guard harness alone guaranteed loopback under every environment.

Final exact-target independent review pending at freeze. Only a clean review may
permit a local commit; otherwise preserve staged diff/archive for shutdown.
Production writes: none. Rollback: abandon isolated unmerged local branch.
Stop conditions: unsafe session semantics, broader selector changes, unresolved
ownership/transaction gates, or shutdown boundary. No push/PR/rollout authority.


## October 29 local continuation

Preserve the original staged tree 98236f7bb66e41297b72a9bcad4663316edd8e6e and sealed checkpoint. New source deltas remain unstaged; the original HTTP test is preserved separately as .tmp/positions-reuse/http-before-lifecycle-2026-10-29.py.

Intent: close local real-SQL route and connection-lifetime gaps without production, publication authority, selector, transaction, query-order, CI/configuration, or architecture changes. Apply existing migrations only in the owned disposable cluster and reuse test-only governed fixtures. Compare fresh reads, original held reuse, and release-before-publication reuse. Add targeted real route parity/failure/concurrency checks; measure opens, peak ownership and hold intervals separately. Review exact changed files with the existing independent reviewer.

Definition of done: focused tests pass, owned cluster shutdown is verified, original index/checkpoint seals remain intact, exact new deltas/evidence are sealed, and independent review is complete. Any unavailable governed site fixture or deployed compatibility remains an explicit release gate. No commit/push/PR/merge or rollout is authorized.

Progress: fixture and lifecycle implementation in progress; targeted validation and review pending. Rollback is the exact preserved index/source archive for tracked changes and preserved original HTTP source for that addition; no rollback action is being performed.

## October 29 hosted validation (supersedes earlier delivery restrictions)

The user approved applying the reviewed CI job, committing/pushing the existing
experiment branch, and opening draft PR #244 for hosted testing only. No merge,
deployment, production write, or editorial acceptance is authorized. Local
lifecycle/publication evidence and independent source reviews are preserved in
the ignored .tmp/positions-reuse evidence folders; the initial index is archived.

First hosted head: 0067a79c57201f37b9876897343b84db7cd8d807. Backend run
40954704773 and Education run 40954705016 exposed two blocking compatibility
issues: Windows image PGUSER/PGPASSWORD defaults stopped the strict environment
guard before pytest; scoped rollback reached the existing operator-owned borrowed
transaction and invalidated public postcondition/idempotency checks.

Correction: clear only the five documented image defaults in the test process,
retaining rejection of all other PG-prefixed settings and the unchanged owned
loopback harness. Make BorrowedConnection.rollback a no-op, matching its close
ownership boundary, so only the operator ends its transaction. Add two real
PostgreSQL regressions for retained writes and owner-controlled failed-read
recovery, raising the new job's exact count from 144 to 146. Verify shutdown in
the three known disposable fixture roots after hosted tests. No runtime SQL,
publication guard, migration, or connection ownership policy is weakened.

Focused correction validation: 73 tests passed, including six real PostgreSQL
cases. Hosted successor checks and independent successor review remain pending.
Completion requires terminal hosted outcomes tied to the reviewed successor;
production compatibility and performance remain unproven by these fixtures.

Second hosted head 0655ccad0275e70cab85a3e9490b920fef6dbb88 passed source review
and the Education locator job (101 tests). Its Windows job reached pytest:
51 passed and 95 setup errors, all from initdb failing to chmod precreated data
directories. No cluster started; all three attempted directories had no PID file.
The next harness correction lets initdb create the new UUID directory itself,
refusing any existing path or symlink. It uses PostgreSQL's normal creation path;
no ACL edits, service changes, endpoint relaxation, or environment-guard changes.

## Linux Python 3.14.3 continuation

Baseline e25c0223b86037f653113acd1d344d1dddb1ccae completed independent review,
12 Backend and two Education jobs; original receipts remain sealed in
.tmp/positions-reuse/hosted-delivery-2026-10-29. Main remains d4342590.

Trusted controller read-only Render evidence identifies live deploy
dep-dbgd4s7avr4c73dmfgfg on srv-d84abkuq1p3s738qd1i0 at full main SHA
d43425905207ef66e5268edbe0e36252f79ff4d8, Linux Python3.14.3 and psycopg/binary3.3.3.
Endpoint/pooler mode, PostgreSQL version, timeouts, session/preparation behavior,
capacity and effective app-role privileges remain unknown. This task does not
repeat production inspection or treat a Python match as full production parity.

Authorized outcome: add a Linux3.14.3 real-PostgreSQL readiness gate on draftPR244,
preserving the Windows3.11/PG17 gate and all existing jobs. Five intended files:
workflow, test-only platform adapter, three offline adapter cases, this plan, and
a proposal-only sanitized runtime diagnostic. No production application edits.

Use setup-python@v5 exact3.14.3 and ubuntu-24.04's preinstalled PostgreSQL16.
No installation on the user's PC, sudo/service changes, binary downloads outside
standard hosted Python provisioning, or credential/endpoint inputs. Linux fixture
uses fixed binaries and disables Unix sockets; all existing loopback, environment,
account, ownership and normal shutdown guards remain. The same six readiness
files must yield146 cases without skips. Keep adapter tests separate from that
count and retain Linux JUnit/cleanup receipts as bounded seven-day CI artifacts.

Sequence: verify official guidance and baseline; implement small adapter/job;
run focused local adapter and Windows harness checks; independently review delta;
commit/push this branch; monitor all successor checks to terminal and retain exact
head/failed-attempt evidence. Prepare the sanitized diagnostic proposal without
executing it. Definition of done includes both platform gates, unchanged earlier
jobs, independent source/hosted review, clean worktree and closed owned clusters.
Rollback: revert this unmerged continuation; no production rollback is needed.
Production writes/diagnostic execution: none authorized or performed.

Primary provisioning references:
- https://github.com/actions/setup-python/blob/v5/README.md
- https://github.com/actions/setup-python/blob/main/docs/advanced-usage.md
- https://github.com/actions/python-versions/blob/main/versions-manifest.json
- https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md
- https://github.com/actions/runner-images/blob/main/images/ubuntu/scripts/build/install-postgresql.sh
- https://www.postgresql.org/docs/16/runtime-config-connection.html
- https://www.postgresql.org/docs/17/app-initdb.html
