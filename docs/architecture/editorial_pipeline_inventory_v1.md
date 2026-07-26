# Editorial Pipeline Inventory V1

Baseline: `bc7617b05f33d56cf83c4bb7e4b8113b945a3998`.

The authoritative machine-readable inventory is
`docs/architecture/editorial_pipeline_inventory_v1.json`. Exact deleted paths,
test classifications, preservation hashes, and validation outcomes are in
`docs/editorial/editorial_hard_cutover_v1_receipt.json`.

## Ownership

New work has one executable semantic path:

```text
reviewed shared semantics + exact member states
  -> backend.app.semantic_ir.pipeline.run_editorial_pipeline
  -> backend.app.semantic_ir.compiler.compile_semantic_ir (exactly once)
  -> compiled-IR validation
  -> compiler-owned review route
  -> meaning-preserving adapters
  -> separate, unauthorized persistence/publication boundaries
```

The pre-IR semantic helpers, milestone generators, old-format frontend
adapters, registries, review fixtures, and rich renderer were deleted. There is
no legacy replay path or compatibility adapter.

## Classification summary

| Classification | Post-cutover meaning |
| --- | --- |
| `canonical_semantic` | Owns Semantic IR input, compilation, validation, or command orchestration. |
| `retained_acquisition` | Acquires, parses, normalizes, identifies, maps, caches, archives, or stores source evidence. |
| `retained_historical_evidence` | Frozen dossiers, manifests, proofs, receipts, provenance, and generated historical artifacts. |
| `retained_live_persistence_safety` | Production migration, import/export, backup, rollback, reconciliation, dependency discovery, and audit history. |
| `remove_legacy_execution` | Deleted old semantic or presentation execution recorded by the cutover receipt. |
| `unrelated` | Outside the editorial semantic architecture. |
| `blocking_requires_review` | Unresolved mixed responsibility. There are no entries. |

## State boundaries

- Accepted Semantic IR corpora and receipts remain unchanged.
- Frozen historical evidence remains in place but is not a canonical input.
- All source-acquisition capability remains available, including currently
  unused clients and parsers.
- The 71 persisted historical artifacts remain unpublished; persistence and
  publication tooling remains protected.
- The public representative route deliberately uses basic vote evidence and
  receipts. No old editorial registry exists.
- The former `/golden-render-fixture` route is absent.
- IR-native public presentation and database cleanup are deferred.

The cutover did not query or change production, persistence, publication,
deployment, migrations, or database state.
