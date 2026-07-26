# Editorial Semantic IR V1 Held-Out Generalization Proof

Status: complete

Starting commit: `cc70e7d58e264e535548aab313681b655e684772`

## Intent

- Evaluate the four committed held-out cases from authoritative evidence using
  accepted Semantic IR V1 rules and the merged deterministic compiler.
- Demonstrate fresh-context generalization without changing the engine,
  accepted references, schema, held-out inputs, or source dossiers.

## Scope And Boundaries

- In scope: input-only shared semantic proposals, adversarial self-review,
  unchanged compilation, semantic-first result artifacts, review routing, and
  the bounded semantic validation loop.
- Out of scope: engine or schema changes, semantic acceptance, hidden expected
  outputs, dossier edits, frontend rendering, persistence, production,
  publication, merge, or deployment.
- Expected fan-out: four new proof/review artifacts plus this plan; semantic
  validation only; runtime expected in seconds to low minutes.

## Decision Envelope

- Sol may apply established V1 rules, correct supported input-packet defects,
  compile unchanged, and route genuinely novel or unsupported semantics.
- New semantics remain proposals. Engine correction, acceptance, production
  use, publication, and merge require later authorization.

## Definition Of Done

- [x] Four input-only packets distinguish established, proposed, unresolved,
  and unsupported semantics.
- [x] Each packet receives adversarial review before unchanged compilation.
- [x] Exact compiler results and defensibility/review judgments are recorded.
- [x] Protected files and inputs are byte-identical to the starting commit.
- [x] Bounded semantic, property, packet, and governance checks pass.
- [x] Staged `git diff --check` passes.
- [x] Intended files are committed, pushed, and presented in draft PR #109.

## Baseline

- Branch: `codex/editorial-semantic-ir-held-out-v1`
- Base: clean current `origin/main` at
  `cc70e7d58e264e535548aab313681b655e684772` (merged PR #108).
- Production/deployment state: untouched; no production writes authorized.
- Known unrelated tracked or untracked artifacts: none at start.

## Implementation Sequence

1. Inspect held-out authoritative inputs, referenced dossiers, accepted rules,
   compiler behavior, and validation contracts.
2. Author and adversarially review four input-only packets.
3. Compile each packet unchanged; preserve exact outputs or failures.
4. Produce the machine and human review artifacts.
5. Run bounded validation and byte-identity proofs; inspect the final diff.
6. Commit, push, and open the requested draft PR.

## Progress

- [x] Baseline confirmed and branch created.
- [x] Evidence and established-rule inspection complete.
- [x] Shared semantic packets complete.
- [x] Compilation and judgments complete.
- [x] Validation and protected-file proofs complete.
- [x] Commit and draft PR complete.

## Discoveries And Decisions

- Interpretation boundary: conclusions must remain bounded to exact reviewed
  actions; member identity and party cannot alter shared semantics.
- The local `gh` keyring credential is stale. SSH Git access and the connected
  GitHub app will be used for the authorized publish flow if available.
- Case 1 is blocked: the compiler reports two unresolved Missing Evidence
  actions as both missing-evidence boundaries and outside-service coverage,
  with `missing_evidence_actions` incorrectly equal to zero.
- Case 2 is blocked: the compiler emits a substantive support proposition from
  an explicitly unresolved action meaning whose supplied Congress source
  conflicts with the recorded roll.
- Case 3 is defensible and invariant under action/episode/trait order plus
  member-identity and party mutation.
- Case 4 safely excludes roll 5, compiles roll 7 as a bounded final-passage
  notable choice, and requires human review of the proposed render constraint.
- Follow-up: the schema's typed shared-review dependency requires a
  `review_route`, while the compiler's recursive input-only guard forbids that
  field. The redundant dependency was omitted; the source constraint preserves
  the case-2 block without changing the engine.

## Deviations Or Corrections

- An initial packet replay command contained a test-harness typo (`assertion`
  was undefined). It was corrected without changing artifacts; the rerun
  passed.

## Validation Results

- `python scripts/validate_editorial_semantic_ir.py`: passed, 0.079 s.
- `python scripts/compare_accepted_semantic_references.py`: passed, 0.079 s.
- `python -m unittest backend.tests.test_editorial_semantic_ir`: 18 passed,
  0.146 s wall time (0.031 s unittest time).
- New-packet input-only, held-out status/action identity, exact replay, and
  case-3 invariance checks: passed, 0.055 s.
- `python scripts/check_documentation_governance.py`: passed, 0.150 s.
- Documentation governance rerun after Markdown fence correction: passed,
  0.130 s.
- Compiler, schema, accepted-reference corpus/receipts, and held-out input blob
  hashes match the starting commit exactly.
- `git diff --check`: passed, 0.035 s.
- Focused measured validation runtime so far: 0.674 s.

## Production Writes And Rollback

- Production writes performed: no.
- Repository rollback: revert the milestone commit; no external data rollback
  is applicable.

## Blockers

- No semantic or validation blocker to opening the review PR. Two held-out
  cases intentionally route as blocked findings for later engine work.

## Final Reconciliation

- Definition of done satisfied: yes. Five proof-only files were committed and
  pushed; draft PR #109 is open against `main`.
- Remaining limitation: external semantic review is required by design.
- Recommended next step: external review of the four held-out results.
