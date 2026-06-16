# Bounded Production Write Workflow

Use this runbook only when the milestone explicitly authorizes a production write class or the user gives explicit approval.

## Preflight

Confirm:

- intended state or authoritative source basis
- exact target rows, roll calls, objects, or schema objects
- included and excluded tables
- predicted inserts, updates, deletes, and skips
- predicted support/opposition, readiness, alignment, API, and UI impact where relevant
- not-voting and procedural treatment
- security and least-privilege posture
- rollback path created before the write

Stop if the intended state cannot be reconstructed or source support is ambiguous.

## Authorization

A milestone may pre-authorize a bounded class of write. If so, Codex does not need another handoff after successful preflight when every predefined gate passes.

Explicit authorization is still required for:

- new schema decisions
- destructive operations
- ambiguous civic semantics
- unbounded imports
- writes outside the milestone decision envelope
- service, secret, or environment changes not already covered

## Rollback

Create rollback before writing.

Rollback should:

- be scoped to the target rows or objects
- restore prior values for updates
- delete only newly inserted rows for inserts
- avoid touching unrelated tables
- warn or abort when interpreted/counting rows would be affected unexpectedly
- be preserved as a review artifact

## Execute

- Use the narrowest write command available.
- Keep package size within caps.
- Do not write forbidden tables.
- Do not infer support/opposition or interpretation meaning during fact-only writes.
- Do not expose secrets in commands, logs, docs, or PRs.

## Post-Write Validation

Validate:

- actual inserts, updates, deletes, and skips by table
- content matches approved records
- expected versus actual support/opposition/readiness/alignment effects
- procedural rows remain non-counting
- not-voting remains excluded
- fact tables and interpretation tables changed only as authorized
- idempotency or skip-existing behavior
- no unexpected House/Senate, chamber, API, or UI effects

Stop and report if actual effects differ materially from preflight.

## Audit Trail

Document:

- authorization language or milestone decision envelope
- preflight results
- write command or mode
- actual results
- validation queries/results
- rollback artifact path
- remaining risks and follow-up gates
