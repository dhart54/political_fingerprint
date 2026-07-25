# Milestone Plan: Commissioning Domain V1

## Intent

- Immediate task: Commission one new 119th-Congress House issue corpus from official-source discovery through shared evidence, generic synthesis, review-only rendering, immutable persistence, and bounded pending production staging.
- Larger-goal alignment: Prove the complete editorial corpus pipeline can generalize beyond Economy and Justice before any multi-domain batch expansion.

## Outcome

- User-visible or operational result: One safely bounded new-domain corpus and a diverse real-member review cohort run through the generic pipeline, with failures preserved, novel shared meaning routed once, and all artifacts pending and unpublished.

## Scope And Boundaries

- In scope: Deterministic domain selection, official House/Congress.gov research, 6–10 substantive actions, 3–5 episodes, shared dossiers and traits, member overlays, all-House/vector/mutation evaluation, generic review fixtures, immutable batch tooling, disposable PostgreSQL proof, and an exact bounded production pending-batch write if every hard gate passes.
- Out of scope: Economy or Justice expansion, broad House publication, multi-domain batch work, schema migration `0017`, public database read routes, production registry entries, human approval, benchmark promotion, production eligibility, merge, or deployment.
- Files/systems likely touched: `backend/app/summaries`, focused builders/tests, `backend/app/editorial_artifacts`, `backend/scripts`, `docs/editorial/commissioning_domain_v1`, selected-domain dossiers, review packets, review-only frontend registry/fixtures/tests, and this plan.

## Decision Envelope

- Codex may decide and execute: Deterministic selection and tie-breaks; official-source collection; established-contract traits/relationships; generalized pipeline corrections with regression proof; review-only rendering; exact batch/rollback tooling; disposable validation; the pre-authorized exact pending production batch after every gate; commit, push, and draft PR.
- Explicit approval required for: Any new schema, unresolved civic meaning, unsafe authoritative-source conflict, unbounded write, publication/approval/promotion, production registry addition, merge, deployment, or multi-domain expansion.

## Definition Of Done

- [x] Candidate-domain inventory and deterministic selection are complete and preserved.
- [x] Accepted actions have exact official identities, sources, claim maps, and rejection receipts.
- [x] Shared dossiers, episodes, traits, relationships, semantic freeze, and review routes pass.
- [x] Deterministic member cohort, all-House/vector evaluation, mutations, and invariance checks pass or route exact failures.
- [x] Generic review-only frontend renders bounded examples without domain/member/vector branching.
- [x] Immutable pending artifact graph and exact-batch rollback tooling are complete.
- [x] Disposable PostgreSQL, import/export equality, idempotency, conflict/orphan/publication guards, RLS, and rollback proof pass.
- [x] Authorized production staging is applied only if every hard gate passes, then postchecked and proven idempotent.
- [x] Existing 71/95 seed, canonical tables, database selector/registry, and static registry remain unchanged.
- [ ] Required test, build, rendered, documentation, review-packet, commit, push, and draft-PR gates complete.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/commissioning-domain-v1` from exact fetched `origin/main` `08e675e2039d76f16b8c9576e4b5a8254bc44d72`.
- Production/deployment state: Migration `0016` complete; seed batch exact at 71 artifacts/95 relationships; four pending presentations; database registry 0; publication selector 0; static frontend production registry empty; no public database artifact route.
- Tracked working tree: Clean before branch creation; all registered child worktrees external to the root.
- Known unrelated untracked artifacts: Existing ignored caches/test directories remain untouched.

## Implementation Sequence

1. Inventory candidate domains from repository data and bounded official-source discovery; freeze deterministic scoring and selection.
2. Resolve exact actions, sources, claims, episodes, traits, relationships, absences, and rejection reasons.
3. Freeze shared corpus and semantic hashes before deterministic member selection.
4. Generate overlays/propositions/presentations, preserve first failures, and run actual-member/vector/mutation invariance evaluation.
5. Commission generic review rendering and build the exact immutable pending batch plus rollback.
6. Validate on disposable PostgreSQL and run all regression, render, lint, build, and documentation gates.
7. If all hard gates pass, apply and postcheck the exact authorized production pending batch.
8. Finalize receipts, reconcile this plan, commit, push, and open a draft PR without merge.

## Progress Checklist

- [x] Startup repository and production baselines
- [x] Domain selection and official-source research
- [x] Shared corpus and freeze
- [x] Member/vector/mutation evaluation
- [x] Review frontend commissioning
- [x] Persistence and disposable PostgreSQL
- [x] Production staging
- [x] Full validation and documentation
- [ ] Commit/PR readiness

## Discoveries

- The earlier blocked cross-issue branch stopped because no already-prepared corpus met its gates; this milestone explicitly authorizes building a missing corpus from official sources.
- The immutable V1 seed pins mixed LF/CRLF byte hashes. A bounded try/finally restored the reviewed byte forms for read-only verification, then restored the clean checkout. This is an operating-system normalization issue, not semantic or database drift.
- Production baseline: exact schema, 71/95 seed, semantic equality, unchanged canonical fingerprints, registry 0, selector 0, and pending slice count 4.
- Environment & Energy won the deterministic six-domain inventory with score 91 and supplied eight safe actions across four policy episodes.
- The accepted corpus uses 15 official congressional sources, maps 66 supported claims, and preserves six supported absences without inventing argument symmetry.
- The House cohort input contained 432 members, 369 complete Yes/No records, and 42 unique vectors. The eight-member cohort includes one two-vote coverage edge and a same-vector cross-party pair.
- Windows element screenshots can inherit horizontal scroll after nested disclosure interaction even when the document has no overflow; resetting `window.scrollX` before capture produced stable bounded evidence without a product-code change.

## Decisions And Rationale

- Keep domain selection evidence-first: source completeness, episode/action diversity, vector diversity, bounded scope, and unresolved-source minimization only.
- Treat the prior blocked branch as read-only evidence; do not merge or copy its result as current implementation.
- Preserve member neutrality and proposition-first synthesis boundaries from the governing workflow and interpretation principles.
- Reuse the existing ontology shape. Route six new source-grounded values and one related-proposal relationship type once as shared human exceptions.
- Keep all 432-member, 42-vector, 256-binary-vector, and 17-mutation evaluations non-persisted; persist only the eight selected real-member slices.

## Deviations Or Corrections

- `COMM-V1-001`: replaced opaque repeated H.R. 6938 titles with exact shared stage identities.
- `COMM-V1-002`: grouped source-grounded related proposals as one episode per policy family rather than overstating independent evidence.
- `COMM-V1-003`: the first disposable relationship graph used labels outside migration 0016; PostgreSQL rolled the transaction back, and the generalized graph was remapped to the existing vocabulary.
- A broad backend run exposed six production-database-versus-fixture expectations and two pre-existing Windows CRLF byte pins. The fixture subset passed 11/11 under an isolated one-second connection fallback; relevant semantic and persistence regressions passed separately.

## Validation Results

- Git/documentation/worktree startup gates: passed.
- Production read-only preflight/postcheck: exact schema and 71/95 seed; registry and selector zero; canonical fingerprints unchanged; semantic round-trip equal.
- Static registry: `Object.freeze([])`.
- Public backend router inspection: no editorial-artifact database route.
- Deterministic commissioning builder: pass; commissioning tests: 8 passed.
- Relevant backend editorial/persistence regressions: 91 passed, 1 known byte-pin case deselected.
- Broad backend observation: 743 passed, 9 skipped, 8 classified pre-existing environment/CRLF failures.
- Frontend unit tests: 140 passed.
- Frontend lint: pass with 8 pre-existing hook warnings.
- Frontend production build: pass.
- Playwright golden render: 13 passed, 12 intentional skips; four commissioning screenshots visually inspected.
- Documentation governance and `git diff --check`: pass.
- Disposable PostgreSQL: exact 74/68 apply/export, 0/0 idempotent reapply, publication/conflict/orphan guards, RLS/privileges, exact rollback, and clean reapply passed.

## Production Writes

- Performed: yes
- Scope: One exact commissioning-domain pending batch only after every hard gate.
- Expected effects: New immutable pending artifacts and exact relationships only; zero updates/deletes/publication rows; existing 71/95 batch and canonical tables unchanged.
- Actual effects: 74 artifacts and 68 relationships inserted in one transaction; second exact apply inserted 0/0; semantic export matched; 12 total pending presentations; registry 0; selector 0; original seed 71/95; canonical fingerprints unchanged.

## Rollback Paths

- Repository: revert only scoped commissioning commits.
- Database: exact-batch, manifest/hash/count/publication-guarded rollback tooling created and transaction-tested before any production write; do not execute without explicit direction.

## Blockers

- None at plan creation.

## Final Reconciliation

- Definition of done satisfied: Implementation, staging, and validation complete; commit/push/draft-PR handoff remains.
- Remaining limitations: Six new trait values, one candidate relationship type, related-proposal episode judgments, six supported argument absences, and all member presentations remain pending human review. The corpus is bounded and is not a complete environmental record.
- Recommended next step: Human review of the shared ontology/relationship package and routed member presentations, then a separate decision on controlled multi-domain batch expansion. Do not publish or promote automatically.
