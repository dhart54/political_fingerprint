# Minimal sanitized runtime diagnostic proposal

Status: PROPOSAL ONLY. No production introspection is authorized or executed by
this document. This is a one-off diagnostic, not a new endpoint, access mechanism,
agent, metrics system, dependency, deployment, or persistent configuration.

## Known provenance and remaining questions

Controller-provided read-only Render evidence binds live deploy
dep-dbgd4s7avr4c73dmfgfg, service srv-d84abkuq1p3s738qd1i0, to main
d43425905207ef66e5268edbe0e36252f79ff4d8: Linux Python3.14.3 and
psycopg/psycopg-binary3.3.3 (cp314 Linux wheel).
[Existing Render service](https://dashboard.render.com/web/srv-d84abkuq1p3s738qd1i0)

CI is intended to match Linux/Python/driver versions using PostgreSQL16, while
retaining Windows/Python3.11/PostgreSQL17 coverage. Neither test database version
is asserted to match production. The actual endpoint/pooler mode, server version,
timeouts/session defaults, prepared-statement behavior, capacity and role powers
are still unknown. Existing deployment metadata does not establish them. No
credential-bearing configuration read is proposed as a shortcut.

## Proposed authorization envelope

If separately approved, an operator would run a reviewed, temporary diagnostic
through an already authorized console in the existing service, as its ordinary
app user. Use the existing application connection factory; no new account, role,
secret, host, network rule, pooler access or persistent files. Verify the intended
deploy before running. At most one existing-runtime connection;
at most 25 fixed SQL operations total, including transaction-control statements;
a 60-second overall deadline, 3-second per-statement cap, and no retries. No application table
rows, DDL, writes, grants, role switches, application requests or registry reads.
If the existing console/factory cannot enforce these bounds without a new access
or configuration change, stop and return `unavailable`.

Read effective defaults before applying transaction-local diagnostic limits;
report original values distinctly. Use READ ONLY transactions and always roll
back/close in the owning process. Do not open a second session for comparison.
No persistent session setting is changed. Connection timeout must be bounded by
an external deadline without relabeling that imposed bound as the application's
effective connect timeout.

## Output allowlist

Emit one schema-validated object containing only fixed keys, booleans, bounded
numbers and the listed enums. No environment dumps, DSNs, hostnames, ports,
database/user/role/object identifiers, backend/process IDs, SQL text, statement names, private rows,
credential values, raw driver objects, stack traces or raw error messages.
Unknown, unsupported or denied fields become `unknown`/`unavailable`; errors use
only `permission_denied`, `timeout`, `unsupported`, or `failed`. Validate the whole
object before emitting; on schema failure emit only `failed`. Disable query/error
echo in the diagnostic. Never include exception strings in output or artifacts.

| Group | Allowed observations |
| --- | --- |
| Runtime | Linux boolean; Python/driver/libpq numeric version components; server major version only |
| Endpoint | `direct`, `session_pool`, `transaction_pool`, `statement_pool`, `other`, `unknown`; authoritative provider metadata required |
| Connection | autocommit boolean; isolation enum; effective read-only boolean; configured connect-timeout category `unset`/`bounded`/`unknown` |
| Timeouts | statement, lock, idle-in-transaction and idle-session timeout milliseconds, capped at 24h with `above_cap`; missing settings `unavailable` |
| Preparation | threshold `disabled`/bounded integer/`above_probe_cap`; prepared-max bounded integer/`unbounded`; aggregate prepared-count buckets `zero`/`nonzero` only |
| Role | effective superuser/bypass-RLS/create-role/create-database booleans; fixed-group aggregate read/write/owner capability booleans; no identifiers |
| Cleanup | rollback attempted/succeeded, connection closed, deadline reached booleans |

Provider endpoint classification must come from a sanitized provider control-plane
field or operator attestation, without exposing or parsing credential values.
If none is available, mode stays `unknown`. Stable backend/session observations
cannot prove a pooler mode. Pooler-specific behavior and capacity remain unknown
unless authoritative, already-accessible sanitized metadata establishes them.

For preparation, inspect the existing connection's configured attributes, then
optionally repeat a fixed constant SELECT within READ ONLY transactions, up to 10
executions and only if its existing threshold fits that cap. Do not force
preparation, disable it, change prepared-max, or fetch prepared SQL/names. Report
aggregate prepared-count buckets before/after normal rollback. This observes
this bounded path only; it does not certify all pooler lifetimes or production
load. If additional server/session activity is required, propose it separately.

Role checks use fixed built-in catalog predicates for the current app user and
fixed relation groups already required by the positions path. Return only
aggregate capability booleans; do not select application rows or enumerate role
membership. These booleans do not prove RLS-visible row access or authorize any
write. Missing privileges are a diagnostic result, never grounds to grant them.

## Review and decision

Before execution approval, supply the exact short diagnostic implementation,
allowlist schema and fixed operation list for independent review, with deadline
and cleanup tests against disposable fixtures. This document grants no execution
authority. Retain only the sanitized result and deploy-binding receipt. Treat
unresolved provider mode, defaults, preparation, role or timeout behavior as a
remaining compatibility question; CI success alone cannot close it.

References: [Psycopg preparation](https://www.psycopg.org/psycopg3/docs/advanced/prepare.html),
[PostgreSQL session defaults](https://www.postgresql.org/docs/17/runtime-config-client.html),
[PostgreSQL privilege predicates](https://www.postgresql.org/docs/17/functions-info.html).
