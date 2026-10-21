# Dormant bounded Health operator

This implements the existing exact-registration and V2 initial-publication
contracts for F000477 then M001184. It is an explicit command only, with no
startup, build, migration, deploy or scheduled hook. Engineering completion does
not record an owner decision or authorize any production operation.

The real owner registry and `operator_approval_registry.json` are empty.
`operator_production_bindings.json` remains pending. Pending receipts and requests
cannot satisfy execution gates. The approved content remains one exact House
action, S.2393 roll call180 in Congress119: one supporting notable choice for
Foushee and a non-directional Not Voting coverage boundary for Massie. No overall
Health conclusion, teaser or benchmark authority is created.

## Entry point and target

Run from the repository root with `python -m scripts.health_bounded_choice_operator`.
Use `--help` to inspect arguments. All operations require a new `--output` path;
existing output files are never overwritten. Credentials are read only from
`HEALTH_CHOICE_DATABASE_URL`, never command arguments or ordinary `DATABASE_URL`.
Errors omit arbitrary input and connection details. Do not print that environment
variable, put credentials in receipts, or save them in Git.

The default `--target production-green` permits only the direct verified-TLS
route `db.yalpfkaxkxebwolhorha.supabase.co:5432`, database `postgres`, user
`postgres`, `sslmode=verify-full`. Actual connection/database/role/port and TLS
are checked. Pooler, hostaddr, service, options and inherited routing overrides
are rejected. This is a hard target restriction, not proof of Render's configured
database or Vercel's current API origin.

`--target owned-loopback` accepts only the actual loopback database
`pf_health_choice_test` with its owned test superuser. It changes routing only:
the same ordinary owner, catalog and V2 verifiers run. Automated tests place
clearly labeled TEST ONLY evidence in temporary trust-store data paths; none is
exported as a real approval or used against Green.

## Operation order and separate authorities

| Operation | Required inputs | Effect |
| --- | --- | --- |
| `prepare-registration` | `--candidate` | Read-only target/baseline observation and nonauthorizing exact one-row request |
| `register` | `--request`, `--approval-id`, `--confirm` | Exactly one separately approved owner audit row |
| `prepare-publication` | `--candidate`, `--context` | Read-only per-member V2 write-set request after both owner registrations |
| `publish` | `--request`, `--approval-id`, `--confirm` | One batch, four artifacts, three relationships and one active registry row |
| `inspect-publication` | `--request`, `--approval-id` | Read-only recovery of an exact committed execution report |
| `rollback` | `--request`, `--approval-id`, `--execution-report`, `--confirm` | Exact inverse of one publication, retaining owner evidence |

Each operation also needs `--output`. Example preparation syntax, usable only
after genuine candidate acceptance and the separately authorized schema setup:

```powershell
python -m scripts.health_bounded_choice_operator prepare-registration --candidate accepted-foushee.json --output foushee-registration-request.json
```

This example supplies no acceptance, registration or execution authority. The
operator does not apply the staged migration. No migration executor, timeout
policy or production schema permission is inferred from this command.

Record genuine owner decisions under the existing fixed owner trust registry
first. A registration request binds the accepted candidate, exact row/plan,
two-member subject, actual target, complete five-table baseline and one-row caps.
It cannot be reused after the baseline changes; prepare and approve the second
member's registration against the first member's retained audit row.

For publication, `--context` contains the existing V2 `preparation` binding and
`runtime` stable binding. Both owner rows must match the exact shared pair and
trusted owner bytes. Publish Foushee first; prepare Massie's distinct baseline
after that publication. Production runtime evidence is freshly observed from
Render health; an optional `--runtime-proof` file supports the owned rehearsal,
and cannot replace production observation.

The fixed operator catalog pins each separately reviewed approval's operation,
path beneath `operator_approvals/`, raw file hash, canonical subject hash, actual
target hash, direct owner provenance and production-binding observation hash.
The command accepts only a catalog ID, never arbitrary authority supplied by CLI.
Registration requires the existing literal separate-positive registration
decision, exact caps and target/baseline/row bindings, reviewer and UTC timestamp.
Publication and rollback require the existing positive V2 authority, including
its exact bounded rollback action. Pending preparation is not that authority.

New registration/publication additionally require fresh, pinned, authorized
connector observations for Render-to-Green and Vercel project/API bindings, plus
matching reviewed source commits for publication. The loader checks recorded
evidence; it does not discover or authenticate platform configuration itself.
No genuine records exist yet. A 200 health response or successful preview cannot
substitute for the unresolved production bindings.

## Atomicity and recovery

Registration/publication recheck the complete baseline while holding all five
editorial table locks. DML counters across user tables enforce exact insert,
update and delete caps, including immediate and deferred trigger side effects.
Publication checks every stored batch/artifact/relationship/registry field,
including strict JSON types and the exact activation-authority hash. Removing
only that deterministic delta must reproduce the complete approved baseline.
An altered, inactive or same-count graph fails before commit.

If output is lost after an uncertain exit, never blindly retry publication.
`inspect-publication` uses a repeatable-read, read-only transaction and the same
exact-state verifier to recover a report. Later member changes must be reconciled
first. Changed edges, authority metadata, artifacts or baseline bytes deny recovery
without writing. Preserve the original request, authority and output as audit
material outside the credential store.

Rollback uses the original exact trusted authority, fresh actual database target,
current-state fingerprint, owned IDs and final baseline-restoration check. It
does not depend on a refreshed global deployment-observation file or current
source/owner-evidence files. Roll back Massie before Foushee. A failure of the
second transaction retains the first until its exact separately authorized
rollback. Owner decisions are immutable audit evidence and are never erased.

Compatibility schema rollback remains a distinct reviewed SQL artifact; it
restores legacy serving while retaining owner audit rows and required CHECK
helpers, revoking nonowner access and forcing RLS. Full audit erasure is excluded.

## Validation and release gates

`backend/tests/test_health_bounded_choice_operator.py` invokes the actual CLI
entry point and real verifiers against owned PostgreSQL with ordinary defaults.
It covers two registrations, sequential V2 publication, public selectors,
lost-report recovery, replay, exact reverse rollback, stale/racing baselines,
bad/pending/changed approvals, target routing, immediate/deferred side effects,
BEFORE INSERT row rewrites and target-like service_role default ACLs. The exact
head CI lane includes this file. See `RELEASE-DECISION.md` for pending production
decisions and `pending-release-decisions.json` for their null fields.
