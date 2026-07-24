# Milestone Plan: Current House Member Metadata Schema Application and Bounded Seed V1

## Intent And Outcome

- Apply reviewed migration `0014` and atomically seed exactly snapshot `house-119-20260713T011722Z` into its six tables.
- Preserve immutable provenance while leaving legislators, ZIP data, routes, flags, frontend, and runtime behavior unchanged.

## Scope, Boundaries, And Decision Envelope

- Authorized writes: migration `0014`; one plain-insert seed of the six pinned previews; explicit snapshot-only rollback capability.
- Forbidden: any other migration/snapshot, updates/upserts, legislator or ZIP mutation, route/flag/frontend/runtime change, raw-source refresh, schema drop, or merge.
- Stop on stale/pin/schema/identity/count/route/flag/ZIP/atomicity mismatch or any post-write difference.

## Definition Of Done

- [x] Dedicated four-mode tool and deterministic tests pass.
- [x] Read-only preflight proves every hard gate and captures rollback posture.
- [x] Schema plus one snapshot commit atomically under an advisory lock.
- [x] Read-only postcheck proves exact schema, rows, preview equality, domains, lineage, and unchanged production state.
- [x] Packets, commit, push, and draft PR are complete; rollback remains unexecuted.

## Baseline

- Branch: `codex/current-house-member-metadata-schema-seed-v1` from `12e0bbf9c22d2083e78433951858f6b5ea2f071d`.
- Approved snapshot: `house-119-20260713T011722Z`; six committed checksum-pinned previews.
- Expected target: configured `backend/.env` Supabase; raw URL and credentials must never be recorded.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence And Progress

- [x] Reconcile authorization, branch, runbook, migration, and preview contract.
- [x] Implement application/rollback tool and packet structure.
- [x] Run static/mocked tests.
- [x] Run production read-only preflight and inspect result.
- [x] Execute the single authorized atomic schema-plus-seed transaction.
- [x] Run postcheck, full tests, JSON validation, and diff hygiene.
- [x] Commit, push, and open the requested draft PR.

## Discoveries And Decisions

- Transaction wrappers will be stripped only when they are the exact first `BEGIN;` and last `COMMIT;`; remaining reviewed SQL executes unchanged inside the application transaction.
- Preview natural keys and exact non-generated columns define database-to-preview comparison; generated IDs/timestamps are excluded.

## Validation Results

- Preflight: snapshot age one day; all six tables absent; snapshot absent; ZIP rows zero; routes/flag safe; 437 member and 441 seat identities exact; auto-select zero.
- Migration SHA-256: `b80484c2555562033657f6838d3645b1d41ff24d13310a5e72278370bc570ae6`; additive-envelope and exact-wrapper checks passed.
- Atomic commit counts: 1 snapshot, 486 artifacts, 437 member rows, 441 seat rows, 874 member links, 882 seat links.
- Database-to-preview equality and canonical SHA-256 matched for all six datasets.
- Domain postcheck: 431 voting representatives, five delegates, one resident commissioner, 437 filled seats, four vacancies, zero conflicts/unknown/primary-only seats.
- Pre/post legislators fingerprint: 637 rows, `87c12b1054b5390af3a4bc16a1234ecb71ef10edd52b6ad700441e122f1ae7b7`, unchanged. ZIP rows remain zero; routes and flag remain unchanged.
- Tool tests: 24 passed. Combined metadata/readiness/ZIP suite: 106 passed. Required JSON and diff checks passed.

## Production Writes Performed

- Committed: migration `0014` plus exactly one approved snapshot across its six tables, in one transaction under the milestone advisory lock.
- No legislators, ZIP, route, flag, frontend, or runtime mutation occurred.

## Deviations Or Corrections

- First application attempt stopped before DDL because a repeat-absence query indexed a dict row as a tuple; transaction rolled back and all tables were verified absent.
- Second attempt executed transactional DDL but stopped at the first insert because `executemany` required a cursor; DDL and seed rolled back atomically and all tables were again verified absent.
- Regression tests were added for both defects. The subsequent transaction was the only committed application.

## Rollback Path

- Exact confirmed command deletes only the approved snapshot row; reviewed cascading foreign keys remove its dependent rows while leaving schema intact.

## Blockers

- None currently; all hard gates remain authoritative.

## Final Reconciliation

- Definition of done satisfied. Schema and seed are present exactly once, postchecks are clean, rollback is available but unexecuted, and no unauthorized state changed.
- Recommended next milestone: ZIP overlap sensitivity and bounded mapping-stage design V1.

## PR #88 Retained-Tool Hardening Correction

### Correction Boundary

- [x] No migration application, seed rerun, rollback, or production DML/DDL.
- [x] The only production interaction was the approved `--postcheck-only` inspection with transaction-level read-only enforcement.
- [x] Historical application outcomes remain distinct from the current verification.

### Hardened Contracts

- [x] Migration `0014` is byte-pinned to SHA-256 `b80484c2555562033657f6838d3645b1d41ff24d13310a5e72278370bc570ae6` before every operational mode.
- [x] The production target is pinned to `postgresql://[masked]@aws-1-us-east-1.pooler.supabase.com:5432/postgres`; username and password are required and the raw URL is never reported.
- [x] The complete migration-derived schema signature fails closed on exact columns, PostgreSQL types, nullability, defaults, primary/unique/check constraints, foreign keys, delete actions, composite keys, and the reviewed index.
- [x] Rollback acquires the application advisory lock, verifies exact target counts, deletes only the approved snapshot parent row, and proves unrelated rows plus protected tables remain unchanged.

### Correction Validation

- [x] Dedicated hardening suite: 46 passed, including executable fake-database apply/postcheck/rollback behavior and every insert-phase rollback.
- [x] Combined metadata/readiness/ZIP suite: 107 passed.
- [x] Read-only production postcheck: counts `1 / 486 / 437 / 441 / 874 / 882`; all database-to-preview equality and canonical checksum checks passed.
- [x] Exact schema contract: all eight fail-closed verification fields true.
- [x] Legislators fingerprint unchanged at `637 / 87c12b1054b5390af3a4bc16a1234ecb71ef10edd52b6ad700441e122f1ae7b7`; ZIP rows remain zero; production auto-select remains zero.
- [x] Route and feature-flag safety checks remain unchanged; JSON validation and diff hygiene passed.

### Correction Reconciliation

- Migration not reapplied; seed not rerun; rollback not executed.
- No production or runtime mutation occurred during this correction.

## PR #88 Durable Postcheck And Rollback Correction

### Durable Freshness Contract

- [x] `--preflight-only` and `--apply-and-seed` enforce the seven-day application authorization window.
- [x] `--postcheck-only` and `--rollback-snapshot` always verify snapshot ID, preview pins/counts, migration hash, and exact target, but treat age as informational.
- [x] Durable modes report snapshot age, application-window status, whether the mode enforces freshness, and continued postcheck/rollback availability outside the window.
- [x] Eight-day executable tests prove both application modes reject and both durable modes accept without calling production.

### Rollback Live-Schema Gate

- [x] Postcheck and rollback share the same exact live-schema inspector.
- [x] Rollback takes the advisory lock and validates all six tables, types, nullability, defaults, complete constraint set, foreign keys, delete actions, and required index before the sole approved snapshot DELETE.
- [x] Eight schema-drift tests prove missing cascade, changed FK target/check/unique/type/default/nullability/index all abort before DELETE.
- [x] Snapshot-scoped rollback with an unrelated snapshot remains executable in the fake database and preserves unrelated rows.

### Durable Correction Validation

- [x] Dedicated application/postcheck/rollback suite: 58 passed.
- [x] Combined metadata/readiness/ZIP suite: 119 passed.
- [x] Read-only production postcheck: snapshot age 1 day, within original application window, freshness informational for postcheck, and durable postcheck/rollback availability true.
- [x] Production counts and canonical checksums remain exact at `1 / 486 / 437 / 441 / 874 / 882`.
- [x] Legislators fingerprint remains `637 / 87c12b1054b5390af3a4bc16a1234ecb71ef10edd52b6ad700441e122f1ae7b7`; ZIP rows and production auto-select remain zero.
- [x] Migration not reapplied, seed not rerun, rollback not executed, and all correction database inspection was read-only.

## PR #88 Project-Specific Target Identity Correction

### Username Identity Contract

- [x] The exact approved normalized database username is pinned only by SHA-256; plaintext username, password, and raw URL remain uncommitted and unreported.
- [x] Normalization strictly validates percent escapes, URL-decodes as strict UTF-8, applies Unicode NFC, and preserves case.
- [x] Same-database different usernames and case changes fail closed; a correctly percent-encoded equivalent normalizes to the same identity.
- [x] Missing usernames, malformed percent escapes, and invalid UTF-8 fail before any database inspection.
- [x] Masked metadata reports only `username_present`, `username_identity_pinned`, and `username_sha256_matches` booleans.

### Target Identity Validation

- [x] Dedicated application/postcheck/rollback/target suite: 62 passed.
- [x] Combined metadata/readiness/ZIP suite: 123 passed.
- [x] Read-only production postcheck confirmed the exact username identity, migration pin, target tuple, and full schema contract.
- [x] Counts and checksums remain exact at `1 / 486 / 437 / 441 / 874 / 882`; legislators remain `637 / 87c12b1054b5390af3a4bc16a1234ecb71ef10edd52b6ad700441e122f1ae7b7`; ZIP rows and production eligibility remain zero.
- [x] Routes and feature flag remain unchanged; migration was not reapplied, seed was not rerun, rollback was not executed, and the correction interaction was read-only.
