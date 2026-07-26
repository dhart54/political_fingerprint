# Editorial Pipeline V1 Handoff

## Canonical architecture

New editorial semantic work enters
`backend.app.semantic_ir.pipeline.run_editorial_pipeline` with two authoritative
inputs: reviewed shared legislative semantics and exact member
action/service/evidence states.

The pipeline calls the pure, independently usable V1 compiler exactly once,
validates the compiled graph, preserves the compiler's review route, and creates
meaning-preserving review and presentation payloads. An optional persistence
proposal is a deep copy with explicit false authorization flags; it performs no
write. Publication remains a separate boundary with no pipeline operation.

Stage ownership:

1. Shared input and exact member states: reviewed authoring inputs.
2. Semantic compilation: `backend/app/semantic_ir/compiler.py`.
3. Compiled validation: `backend/app/semantic_ir/validation.py`.
4. Review routing: compiler-owned route, exposed by the review adapter.
5. Presentation and persistence proposal: `backend/app/semantic_ir/adapters.py`.
6. Publication: existing separately authorized registries; never implied here.

## Canonical commands

```powershell
# Draft-07, 16 references, focused/property/boundary tests, and docs integrity
python scripts/run_editorial_pipeline.py validate --tier semantic

# All accepted cases in one bounded domain
python scripts/run_editorial_pipeline.py validate --tier domain --domain ECONOMY_TAXES

# One or more representative accepted cases through the same public path
python scripts/run_editorial_pipeline.py validate --tier domain --case semir-dev-01-economy-funding-stages

# Only when broader boundaries changed; frontend/persistence checks are opt-in
python scripts/run_editorial_pipeline.py validate --tier release
python scripts/run_editorial_pipeline.py validate --tier release --include-frontend
python scripts/run_editorial_pipeline.py validate --tier release --include-persistence
```

All defaults are read-only, local, non-production, and non-publication.

## Accepted rules and references

- Contract and semantic rules:
  `docs/semantic_ir/editorial_semantic_ir_v1.md`.
- Draft-07 schema:
  `docs/semantic_ir/editorial_semantic_ir_v1.schema.json`.
- Twelve development references and receipt:
  `docs/semantic_ir/accepted/development_cases.json` and
  `docs/semantic_ir/accepted/acceptance_receipt.json`.
- Four held-out references and separate receipt:
  `docs/semantic_ir/accepted/held_out_cases.json` and
  `docs/semantic_ir/accepted/held_out_acceptance_receipt.json`.
- Answer-free held-out inputs:
  `docs/semantic_ir/held_out_inputs/held_out_cases.json`.

The held-out proof demonstrated partial-service/missing-evidence blocking,
source-conflict blocking without invented meaning, identity/title/order
invariance, and bounded cross-domain final-passage interpretation. Acceptance is
limited to the compiler/reference contract.

## Runtime, persistence, and publication boundaries

- The production frontend registry remains an empty frozen array.
- Economy, Justice, and Environment frontend artifacts remain review-only.
- The historical persistence receipt records 71 artifacts and zero publication
  rows; this milestone did not query or modify production.
- Canonical semantic/domain runs do not generate files or prepare persistence
  proposals.
- Even an explicitly requested in-memory persistence proposal remains
  unauthorized and unpublished.

See `docs/editorial/current_state_index.json` for the authoritative state map.

## Retained legacy paths

Pre-IR eligibility, overlay, inference, conclusion, ownership, and routing
modules remain for historical replay and regression tests. Economy, Justice, and
Environment milestone builders and artifact trees remain because they anchor
accepted references, proof packets, preservation receipts, or current review
fixtures. Existing public adapters remain as `retained_public_fallback` until a
separately reviewed runtime migration.

No legacy path is imported or selectable by the canonical command. Exact
classifications and evidence are in
`docs/architecture/editorial_pipeline_inventory_v1.json`.

## Removed superseded paths

None. No candidate satisfied all safe-removal requirements while preserving the
receipt and regression chains. Isolation is the chosen disposition.

## Follow-up work

- Commission a new real domain input manifest that supplies reviewed shared
  semantics and exact member states directly to the canonical pipeline.
- Add a separately reviewed IR-to-existing-public-view-model adapter and parity
  proof before changing frontend runtime ownership.
- Design a bounded IR persistence proposal contract only when a future milestone
  explicitly includes persistence work.
- Consider deletion of pre-IR generators only after public/runtime migration,
  parity, rollback, and remaining-reference proof.

## Recommended next product milestone

Run one newly commissioned, bounded issue domain from reviewed shared input
through the canonical pipeline, complete checkpoint-2 semantic review, and
produce review-only presentation payloads. Keep persistence and publication out
of scope until semantic and presentation parity are accepted.
