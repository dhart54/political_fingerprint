# Milestone Plan: Editorial Semantic IR and Candidate Acceptance Corpus V1

## Intent

- Immediate task: Define a versioned semantic intermediate representation and
  assemble a compact, non-authoritative acceptance corpus for external semantic
  review.
- Larger-goal alignment: Move political-meaning review ahead of prose,
  rendering, persistence, population generation, and publication.

## Outcome

- User-visible or operational result: Reviewers can inspect proposition graphs,
  conclusion plans, evidence ownership, and held-out structural questions using
  repository JSON without running the frontend or database.

## Scope And Boundaries

- In scope: Semantic IR V1 schema/design, dependency inventory, 12 development
  candidate cases, 4 held-out inputs, a fast deterministic validator, focused
  tests, and compact review packets.
- Out of scope: New dossiers or domains, legacy refactors, production semantic
  engine work, prose generation, frontend changes, persistence, migrations,
  population regeneration, approval, promotion, publication, and production
  operations.
- Files/systems likely touched: This plan, `docs/semantic_ir/**`, four required
  review-packet files, and one focused validator/test pair.

## Decision Envelope

- Codex may decide and execute: The V1 JSON shape, stable-ID conventions,
  candidate/held-out selection from existing materials, deterministic
  cross-reference checks, and compact packet organization within the locked
  scope.
- Explicit approval required for: New civic semantics outside the established
  workflow, conflicting authoritative-source resolution, additional domains,
  changes to existing dossiers or engines, persistence, publication, or
  exceeding the 35-file change budget.

## Definition Of Done

- [x] Current semantic representations are classified with fan-out documented.
- [x] Semantic IR V1 schema and invariant contract are complete.
- [x] Twelve development candidates and four held-out inputs validate.
- [x] Candidates remain `candidate_pending_external_semantic_review`; held-out
      files contain no expected propositions or conclusions.
- [x] Fast semantic loop runs in seconds without frontend or database work.
- [x] Tests/build/validation recorded.
- [x] Review packet and dependency inventory updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/editorial-semantic-ir-gold-v1` from exact
  `origin/main` `b49d380acd1e1d80dc462a8159d1155c320241f1`.
- Production/deployment state, if relevant: No production action authorized.
  The frontend production registry is frozen and empty.
- Tracked working tree: Clean before branch creation; local `main`, `HEAD`, and
  `origin/main` matched after merged PR #105.
- Known unrelated untracked artifacts: None.
- Change budget: 13 expected files after consolidating each corpus split into
  one reviewable JSON file; five focused validation commands; semantic loop
  expected under 30 seconds. No frontend build, Playwright, screenshots,
  PostgreSQL, broad backend suite, or population regeneration.

## Implementation Sequence

1. Inventory semantic representations and select structurally covering cases.
2. Define the schema, stable identities, stage boundaries, and invariants.
3. Author development and held-out JSON inputs from existing reviewed sources.
4. Implement focused deterministic validation and tests.
5. Build review/dependency packets, validate, reconcile, and publish a draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Existing semantics are distributed across dossier JSON, episode maps,
  conclusion builders, member overlays, persistence manifests, frontend
  adapters, review fixtures, and validation reports.
- Interpretation boundary: the canonical V1 result is a proposition graph and
  conclusion plan. Example prose is non-authoritative and rendering may not add
  analytical meaning.

## Decisions And Rationale

- Use one consolidated JSON corpus for development cases and one for held-out
  inputs. Case IDs and object boundaries keep review explicit while avoiding
  sixteen nearly identical file wrappers.
- Overlap structural purposes across cases to cover all twenty requested
  conditions with twelve development cases and four held-out cases.
- Reuse existing dossier/source/action identifiers; do not restate or revise
  dossier facts.

## Deviations Or Corrections

- The preflight estimate assumed one file per case. Consolidating each split
  reduced expected file count without changing the 12/4 case design.

## Validation Results

- Baseline documentation governance: passed.
- Draft-07 JSON Schema validation with the existing local Ajv runtime: passed
  for both corpus files.
- Focused semantic validation: passed for 12 development candidates and 4
  held-out inputs; measured validator-internal runtime was 0.0061 seconds.
- Focused invariant tests: 5 passed.
- Documentation governance: passed.
- JSON parsing and reference-path checks: passed.
- `git diff --check`: passed.
- No frontend build, browser test, database operation, broad backend suite, or
  population regeneration was run.

## Production Writes

- Performed: no
- Scope: none authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Repository-only: revert the scoped milestone commit. No production or
  persistence rollback exists because this milestone performs no such writes.

## Blockers

- None at plan creation.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: Candidate semantics require external review and are
  not gold, approved, benchmark, production-eligible, or published.
- Recommended next step: external semantic review of development candidates and
  separately maintained expected results for held-out inputs.
