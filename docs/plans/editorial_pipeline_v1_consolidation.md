# Milestone Plan: Editorial Pipeline V1 Consolidation

## Intent

- Immediate task: make Editorial Semantic IR V1 the sole new-work semantic
  generation path and explicitly isolate older generators and public fallbacks.
- Larger-goal alignment: reduce semantic drift and generated-artifact fan-out
  while preserving civic-integrity, runtime, persistence, and publication gates.

## Outcome

- One read-only canonical orchestration API and developer CLI compile reviewed
  shared semantics and exact member states exactly once, then expose non-semantic
  adapters for review, presentation, and optional persistence proposals.
- Machine-readable inventory and current-state indexes identify every material
  current, fallback, and historical lane without directory-recency inference.

## Scope And Boundaries

- In scope: Semantic IR orchestration/adapters, one validation CLI, focused
  tests, architecture inventory, current-state index, handoff, and documentation.
- Out of scope: semantic conclusion/copy changes, frontend/runtime changes,
  persistence batches, registries, database work, production, publication,
  deployment, and full-population regeneration.
- Expected change size: approximately 10-14 files; no generated corpus fan-out.
- Expected removals: none unless reference inspection proves a path both
  superseded and unused; retain milestone generators as replay-only and current
  public data paths as explicit fallbacks.
- Validation tiers: semantic loop and bounded representative domain/case loop;
  release loop only if an unexpected runtime boundary is touched.
- Estimated local runtime: 10-20 minutes including tests and governance checks.

## Decision Envelope

- Codex may decide and execute: API/CLI shape, fail-closed adapters, inventory
  classifications, focused tests, and documentation within established V1 rules.
- Explicit approval required for: semantic methodology changes, public output
  changes, persistence/publication/production effects, migration, merge, deploy.

## Definition Of Done

- [x] All new semantic output passes through the V1 compiler exactly once.
- [x] Downstream adapters cannot add analytical meaning.
- [x] Canonical semantic/domain commands and representative cases pass.
- [x] Current, fallback, review-only, staged, and historical state is indexed.
- [x] Legacy generators are either safely removed or fail-closed/indexed.
- [x] Public, production, persistence, publication, and accepted corpora unchanged.
- [x] Tests, documentation governance, and diff checks recorded.
- [x] Handoff and final reconciliation completed.

## Baseline

- Branch: `codex/editorial-pipeline-v1-consolidation`
- Base commit: `0343a0771973ea4b085627fcb9b26387092ba302`
- Base identity: clean `origin/main` after merged PR #110.
- Production/deployment state: not queried or changed; repository-only milestone.
- Tracked working tree: clean before branch creation.
- Known unrelated untracked artifacts: none.

## Implementation Sequence

1. Complete bounded architecture inventory and state manifests.
2. Add canonical orchestration, non-semantic adapters, and CLI.
3. Add bypass/isolation/representative-case tests and canonical documentation.
4. Run semantic and bounded domain proof, integrity checks, and final diff review.
5. Commit, push, and open the requested draft PR.

## Progress Checklist

- [x] Discovery; baseline and primary owners identified
- [x] Inventory and current-state manifests
- [x] Canonical orchestration and adapters
- [x] Canonical command surface and tests
- [x] Validation and integrity proof
- [x] Documentation and handoff
- [x] Commit/PR readiness

## Discoveries

- The pure compiler is already canonical and input-only at
  `backend/app/semantic_ir/compiler.py`.
- Twelve development and four held-out cases are accepted semantic references.
- Older summary modules and milestone builders predate the normalized graph and
  must not be selectable for newly commissioned work.
- Current public frontend artifacts and persistence mirrors have separate state
  gates and must remain fallback/adapter paths in this milestone.
- No legacy path met every safe-removal condition; correction receipts,
  accepted-reference provenance, or focused regression coverage still use each
  material candidate.

## Decisions And Rationale

- Preserve the pure compiler API independently and wrap it with a small pipeline.
- Treat accepted reference cases as bounded replay inputs, not new commissioning.
- Use explicit adapter allowlists over generic callbacks so downstream stages
  cannot create propositions, synthesis, ownership, or review routes.
- Prefer indexed retention over unsafe deletion of receipt-bearing generators.

## Deviations Or Corrections

- The domain tier is deliberately described as accepted-reference replay, not
  new full-domain population generation. No new commissioning input manifest was
  authorized or available, and overstating replay as generation would blur the
  evidence boundary.
- No files were removed. Isolation satisfied the milestone without breaking
  provenance or receipt chains.

## Validation Results

- Canonical semantic command: pass in approximately 0.81 seconds total wall
  time; its five stages reported 0.1438s Draft-07, 0.0751s corpus integrity,
  0.0675s 16-reference comparison, 0.3404s focused tests, and 0.1220s
  documentation governance.
- Canonical domain command: all 16 accepted references across Economy, Justice,
  and Environment passed through the public pipeline in 0.0137s.
- Representative required cases passed: Economy, Justice, Environment,
  source-conflict blocked, and partial-service/missing-evidence blocked.
- Adapter/compiler-call/input-only guardrail tests: six focused pipeline tests
  passed; combined Semantic IR and pipeline suite passed.
- Protected frontend/runtime, persistence, migration, accepted-corpus, held-out,
  and publication paths: no diff.
- JSON index parsing and `git diff --check`: pass.

## Production Writes

- Performed: no
- Scope: repository files only
- Expected effects: none
- Actual effects: no protected runtime, persistence, production, publication,
  accepted-reference, or proof-receipt path changed.

## Rollback Paths

- Revert the branch commit; no database, production, registry, or publication
  state is involved.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes; canonical ownership, adapter isolation,
  command consolidation, state discovery, representative proof, and handoff are
  complete.
- Remaining limitations: the domain loop currently replays accepted bounded
  references; newly commissioned full-domain input is intentionally future work.
- Recommended next step: commission one bounded new domain directly into
  reviewed shared semantics and exact member states, then calibrate review-only
  presentation from the canonical payload.
# Superseded execution note

The retention decisions in this historical plan were superseded by
`docs/plans/editorial_hard_cutover_v1_spec.md`. The listed pre-IR replay
implementations and old public fallback adapters were deleted in Editorial Hard
Cutover V1; only their frozen historical evidence remains.
