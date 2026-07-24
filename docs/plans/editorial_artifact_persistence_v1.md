# Milestone Plan: Editorial Artifact Persistence and Pending Seed V1

## Intent

- Immediate task: add an immutable, queryable PostgreSQL mirror for the accepted editorial artifacts and seed the four explicitly reviewed pending slices.
- Larger-goal alignment: establish durable provenance, review routing, validation history, and supersession without changing publication or runtime behavior.

## Outcome

- The reviewed Git artifacts remain canonical and round-trip through a versioned database store; production publication selectors still return zero rows.

## Scope And Boundaries

- In scope: additive migration `0016`, deterministic seed/import/export tooling, internal repository reads, exact-batch rollback mode, tests, production-safe application, and documentation.
- Out of scope: public routes, frontend read-path changes, publication, new issue research, recurring ingestion, or PR #100 changes.
- Files/systems likely touched: `backend/migrations`, `backend/app`, `backend/scripts`, `backend/tests`, `docs/editorial`, `docs/review_packets`, and the approved PostgreSQL target.

## Decision Envelope

- Codex may decide and execute: the additive relational contract and authorized exact migration/seed after every hard gate passes.
- Explicit approval required for: any destructive schema recovery, publication activation, runtime cutover, or content expansion beyond the reviewed artifacts.

## Definition Of Done

- [x] Additive schema enforces immutable versions, exact relationships, fail-closed publication, and backend-only access.
- [x] Deterministic reviewed manifest contains the required shared evidence and four pending real slices only.
- [x] Import/export, repository reads, migration validation, rollback readiness, and publication isolation are tested.
- [x] Disposable and approved-production validation are recorded, including canonical pre/post fingerprints.
- [x] Tests/build/validation recorded
- [x] Review packet or final documentation updated
- [x] Final reconciliation completed

## Baseline

- Branch/base commit: `codex/editorial-artifact-persistence-v1` / `88d6f3446f54b07735e084cbc958c1614b190fab`.
- Production/deployment state, if relevant: PR #99 merged; PR #100 is an untouched draft and documents that no eligible native cross-issue corpus exists.
- Tracked working tree: clean isolated worktree at milestone start.
- Known unrelated untracked artifacts: none in the isolated worktree.

## Implementation Sequence

1. Inventory the persistence, identity, security, migration, editorial-source, and publication contracts.
2. Implement and validate the additive schema, deterministic bundle, tooling, repository layer, and tests.
3. Apply only after disposable PostgreSQL, migration pin, target identity, rollback, and preflight gates pass; then perform postchecks.
4. Reconcile documentation, commit, push, and open the requested draft PR without merging.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Existing migrations end at `0015`; `0016` is the next additive identifier.
- Canonical members use `legislators.bioguide_id`; roll calls use chamber, Congress, session, and roll-call number; measures use Congress, bill type, and bill number.
- `vote_interpretations` is a mutable, one-row-per-roll interpretation table and cannot safely express immutable shared/member graphs or exact-version publication.
- The public schema is Supabase-exposed, and migration `0011` establishes backend-only RLS/grant conventions.
- The blind-candidate builder's shared-evidence glob depended on the caller's working directory. Resolving it from repository root restores deterministic source-identity checks without changing generated content.

## Decisions And Rationale

- Add a generic versioned artifact layer. This avoids rewriting or overloading canonical vote interpretations while retaining optional foreign keys to canonical legislators and roll calls.
- Keep reviewed repository files canonical during this phase. Database rows are a deterministic mirror identified by canonical JSON SHA-256 and originating commit.
- Keep all four slices pending, unpromoted, ineligible, and absent from both database and static frontend publication registries.

## Deviations Or Corrections

- Docker Desktop was initially unavailable to the sandbox; it was started explicitly and the isolated PostgreSQL 16 container was removed after validation.
- The full backend run needed ignored local source caches and an escalated pytest temp directory. With those available, 751 tests passed and one unrelated pre-existing exact-byte ZIP manifest pin failed (`expected df3201...`, repository bytes `243735...`). The required editorial, persistence, vector, property, source, and database suites passed.

## Validation Results

- Deterministic manifest: 71 artifacts across all 15 types, 95 relationships; manifest `f8c4c24f...`.
- Disposable PostgreSQL: migrations `0001`–`0016`, exact insert/export, idempotency, constraint/trigger/RLS/role denial, repository reads, and guard tests passed.
- Production: exact target verified; 71/95 committed atomically; four pending slices; zero publication rows and selector rows; export hashes exact; conflict and publication probes rejected with no committed probe rows; idempotent rerun inserted zero.
- Canonical production fingerprints for legislators, bills, roll calls, and vote interpretations were unchanged.
- Frontend Node: 136 passed. Lint: zero errors/eight pre-existing warnings. Next production build/type validation: passed.
- Backend: 751 passed/one unrelated pre-existing ZIP manifest pin failure. Dedicated persistence: 24 passed (15 deterministic + 9 executable PostgreSQL).
- All 48 standardization rules, 32 mutation cases, four semantic references, Justice 128-vector/property regressions, deterministic builders, JSON parsing, and diff hygiene passed.
- Public checks: frontend 200, backend health 200, no pending/rich editorial text in production HTML, and no editorial/artifact/publication path among 16 production OpenAPI paths.

## Production Writes

- Performed: yes
- Scope: additive migration `0016` and one exact seed batch only, if every gate passes.
- Expected effects: reviewed schema objects plus deterministic pending artifacts; zero publication rows; unchanged canonical tables and public behavior.
- Actual effects: exact `0016` objects plus one 71-artifact/95-relationship batch; publication remains zero and protected state is unchanged.

## Rollback Paths

- Exact-batch rollback deletes only relationships and versions owned by the pinned batch after verifying it is unpublished; schema recovery is forward-only.

## Blockers

- Cross-issue validation remains blocked because no eligible native evidence corpus exists. PR #100 is evidence only and is not modified.

## Final Reconciliation

- Definition of done satisfied: yes, subject to draft PR creation.
- Remaining limitations: no runtime database read path, publication approval, recurring ingestion, or new issue corpus is included.
- Recommended next step: build one new issue domain's shared evidence corpus, persist it through this store, then rerun cross-issue generality validation.
