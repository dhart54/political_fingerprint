# Editorial Semantic IR Engine V1

Status: active

Starting commit: `db848088b3d7bd168c7742e47978ef386129ca56`

## Milestone intent

Promote the 12 externally accepted Phase A development cases into the canonical
Semantic IR V1 accepted-reference corpus and implement one pure, deterministic
compiler that reproduces their member-level semantic structures from input-only
evidence.

## Scope and boundary

- Move the accepted corpus to `docs/semantic_ir/accepted/development_cases.json`
  with the distinct `accepted_semantic_reference` state and
  `accepted_semantic_reference_corpus` kind.
- Preserve the Phase A candidate review packet as historical review evidence.
- Record machine-readable and human-readable acceptance receipts.
- Keep reviewed shared action meaning, eligibility, episode/family structure,
  policy traits and relationships, source constraints, and focused-fixture scope
  as compiler inputs.
- Derive coverage, propositions, synthesis, boundaries, accounting, conclusion
  membership, presentation ownership, and deterministic review routing.
- Keep the compiler file-agnostic and isolated from runtime routes, persistence,
  frontend, dossiers, public conclusions, registries, and legacy builders.
- Keep all four held-out inputs byte-identical and answer-free.

Non-scope: held-out expected answers, legacy migration, frontend or browser work,
database or production writes, publication, promotion outside the semantic test
contract, deployment, and full-population generation.

## Implementation sequence

- [x] Verify clean, current `origin/main`; record the exact start.
- [x] Promote and validate the accepted-reference corpus and receipts.
- [x] Implement the pure input projection and deterministic compiler.
- [x] Add 12 reference comparisons plus invariance and anti-overfitting tests.
- [x] Update the contract, schema, architecture notes, and documentation indexes.
- [x] Run focused validation, inspect the final diff, and reconcile all gates.
- [x] Commit, push, and open the requested draft PR without merging.

## Definition of done

All 12 accepted cases compile to semantic equality from payloads that exclude
expected output fields; accepted actions have complete accounting; identity,
party, titles, ordering, and equivalent stable IDs do not alter selection;
engine source contains no accepted case/member identifiers; held-out bytes and
answer-free status are unchanged; focused semantic and governance checks pass;
and no public/runtime behavior changes.

## Validation

- `python scripts/validate_editorial_semantic_ir.py`
- `python -m unittest backend.tests.test_editorial_semantic_ir`
- focused compiler comparison, unit, property, anti-overfitting, accounting,
  and held-out-integrity tests
- `python scripts/check_documentation_governance.py`
- `git diff --check`

Record semantic-loop, accepted-reference comparison, and total focused runtimes
in the completion report.
