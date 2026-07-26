# Editorial Pipeline Inventory V1

Baseline: `0343a0771973ea4b085627fcb9b26387092ba302`.

The authoritative inventory is
`docs/architecture/editorial_pipeline_inventory_v1.json`. It records purpose,
callers, inputs, outputs, semantic authority, effects, disposition, and evidence
for each material lane.

## Ownership

New work has one semantic path:

```text
reviewed shared semantics + exact member states
  -> backend.app.semantic_ir.pipeline.run_editorial_pipeline
  -> backend.app.semantic_ir.compiler.compile_semantic_ir (exactly once)
  -> compiled-IR validation
  -> compiler-owned review route
  -> meaning-preserving presentation payload
  -> optional inert persistence proposal
  -> separate, unauthorized-by-default publication boundary
```

The compiler remains independently usable. The pipeline never imports dossiers,
vote-vector generators, pre-IR inference, pre-IR conclusion synthesis,
persistence stores, frontend registries, or publication selectors.

## Classification summary

| Classification | Meaning in this inventory |
| --- | --- |
| `canonical` | Owns new-work semantic input, compilation, validation, or command orchestration. |
| `canonical_adapter` | Consumes established meaning or validates it without adding meaning. |
| `retained_public_fallback` | Existing runtime/public boundary retained unchanged for current pages. |
| `historical_replay_only` | Receipt-bearing or milestone-specific path available only by deliberate direct invocation. |
| `superseded_remove` | Proven safe to delete now. There are no entries. |
| `unrelated` | Outside the bounded inventory and omitted from the entry list. |
| `unknown_requires_review` | Material path whose disposition cannot be established. There are no entries. |

No file qualified for deletion. The older builders still support tests,
accepted-reference provenance, correction receipts, or current review fixtures.
Indexing and excluding them from the canonical command is safer than deleting or
moving their artifact trees.

## State boundaries

- The production frontend registry remains the frozen empty array at
  `frontend/lib/editorialIssueProductionSlices.mjs`.
- Review-only Economy, Justice, and Environment modules remain outside that
  registry.
- The historical persistence receipt records 71 stored artifacts and zero
  publication-registry rows. This milestone neither queries nor changes it.
- A semantic run creates no presentation file, persistence batch, registry
  selection, database write, frontend regeneration, or publication action.
- Release checks are opt-in and flags merely select checks; they confer no
  production, persistence, publication, merge, or deployment authority.

## Legacy isolation proof

- `scripts/run_editorial_pipeline.py` imports the V1 pipeline and accepted
  reference comparator only.
- Focused tests reject expected-output fields at new-work input.
- A compiler-call spy proves one compiler invocation per pipeline run.
- Adapter equality and deterministic digests prove adapters do not mutate or
  synthesize proposition graphs or conclusion plans.
- Historical builders have no flag or selection route on the canonical CLI.
