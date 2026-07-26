# Editorial Semantic IR V1 Held-Out Correction And Acceptance

Status: complete

Starting commit: `c7b99ef0be5ac95884ecaac141c6a0e7b770647d`

## Intent

- Correct the two generalized compiler defects exposed by the first held-out
  proof and accept the reviewed cross-domain constraint.
- Close the isolated Semantic IR generalization proof across all 12 development
  references and all four held-out references without runtime adoption.

## Outcome

- The compiler keeps service and evidence states orthogonal, blocks behavioral
  propositions when typed exact-action source constraints require it, accepts
  path-valid shared-review metadata, and preserves bounded cross-domain meaning.

## Scope And Boundaries

- In scope: isolated compiler, schema/validator, focused and property tests,
  required accepted metadata, held-out accepted corpus/receipts, contract docs,
  and this plan.
- Out of scope: original held-out inputs and first-pass artifacts, runtime
  routes, frontend, legacy builders, persistence, databases, production,
  publication, promotion, deployment, and full-member generation.
- Expected fan-out: approximately 8-12 changed files; semantic validation only;
  expected runtime 20-40 minutes.

## Decision Envelope

- Sol may implement the explicitly authorized service/evidence, typed
  source-effect, bounded cross-domain, and path-aware input-boundary decisions.
- New semantics outside those decisions, production effects, publication,
  approval, merge, and deployment require separate authorization.
- Interpretation boundary: conclusions remain bounded to exact reviewed actions;
  rendering cannot infer motive or unrelated package-wide meaning.

## Definition Of Done

- [x] All 12 existing and four held-out accepted references compare exactly.
- [x] Cases 1-4 match the authorized outcomes and case 3 remains invariant.
- [x] Anonymous property tests and anti-branch scans prove general correction.
- [x] Original held-out inputs and PR #109 proof artifacts remain unchanged.
- [x] Focused semantic, governance, and diff validation is recorded.
- [x] Final diff/behavior reconciliation is complete.
- [x] Intended changes are committed, pushed, and opened as a draft PR.

## Baseline

- Branch: `codex/editorial-semantic-ir-held-out-correction-v1`
- Base: clean current `origin/main` at
  `c7b99ef0be5ac95884ecaac141c6a0e7b770647d` (merged PR #109).
- Production/deployment state: untouched; no production writes authorized.
- Known unrelated tracked or untracked artifacts: none at start.

## Implementation Sequence

1. Map compiler, schema, validator, proof artifacts, and held-out packet shapes.
2. Implement generalized contract and compiler corrections.
3. Create accepted held-out references and bounded acceptance receipts.
4. Add comparison, mutation, input-boundary, and protected-integrity tests.
5. Run the semantic loop, governance, scans, integrity proof, and diff review.
6. Commit, push, and open the requested draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The first-pass proof artifacts already isolate the two engine defects and the
  accepted case-4 semantic boundary; they are protected historical inputs here.
- Service and evidence resolution were previously coupled in coverage,
  boundary, accounting, and route selection. The corrected coverage treats
  missing evidence independently while reserving outside service for two
  verified statuses.
- The recursive input guard treated a field name as output-only regardless of
  path. A direct shared-review dependency legitimately owns `review_route`;
  root and member-output locations remain prohibited.
- Follow-up review found `semantic_effect` attached to the wrong Draft-07
  `required` array. Ajv 6.15 was already available through the frontend
  lockfile/runtime, so actual schema validation was added without a dependency
  change.

## Decisions And Rationale

- Typed semantic effects will drive compiler behavior; no prose parsing or
  case/member/action/domain-specific branching is permitted.
- A `blocks_behavioral_propositions` constraint removes only the affected
  accepted action from proposition selection, preserves raw action coverage,
  records an explicit reason, and blocks the result.
- `bounds_cross_domain_attribution` constrains later rendering without
  suppressing the reviewed bounded action proposition.

## Deviations Or Corrections

- Branch creation required the repository's protected Git-metadata permission;
  it succeeded without changing the worktree baseline.
- Corrected the schema-only `semantic_effect` requirement: method boundaries do
  not require it, while source/render constraints do. Compiler semantics,
  accepted outputs, and protected artifacts were not changed.

## Validation Results

- `python scripts/validate_editorial_semantic_ir.py --json`: passed; 12
  development references, 4 accepted held-out references, and 4 original
  answer-free inputs; 0.0968 s wall (0.0274 s internal).
- `python scripts/compare_accepted_semantic_references.py --json`: all 16
  comparisons passed; 0.0716 s wall (0.0044 s internal).
- `python -m unittest backend.tests.test_editorial_semantic_ir`: 25 passed,
  including anonymous service/evidence, source-conflict, case-3 invariance,
  path-aware input, anti-branch, and protected-integrity properties; 0.2518 s
  wall (0.156 s unittest).
- `node scripts/validate_editorial_semantic_ir_schema.mjs`: actual Draft-07
  validation passed for both accepted corpora and the original held-out input
  corpus; method-boundary, missing-effect rejection, and typed-effect
  regressions passed.
- Focused suite after the Draft-07 correction: 26 tests passed in 0.225 s.
- `python scripts/check_documentation_governance.py`: passed; 0.1601 s wall.
- `git diff --check`: passed; 0.0529 s wall.
- Focused measured wall time: 0.6332 s.
- Protected SHA-256 values remain
  `767cbacce790c45537833e46e59fe4b1c558b440c2844835a07414e45396a9d1`,
  `ecb85fcbf4d9eb813569f3182596768c70886ad24b5945a600a5222e07afe2c7`,
  and `fc7a355e05fd6bccd0a35685a2e817ffd6b52fa1a0da250f4524be1c54d1729d`.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the milestone commit; no external data rollback is applicable.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes. The 12-file implementation commit
  `53b38ef84d886f81174058e82ba7a4b73cc5701c` is pushed and draft PR #110 is
  open at `https://github.com/dhart54/political_fingerprint/pull/110`.
- Remaining limitations: acceptance is confined to the Semantic IR
  compiler/reference contract; no runtime or publication authority is granted.
- Recommended next step: review draft PR #110; do not merge automatically.
  The Draft-07 correction remains on the same branch and PR.
