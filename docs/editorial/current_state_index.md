# Editorial Current-State Index

The machine-readable authority is
`docs/editorial/current_state_index.json`.

- Editorial Semantic IR V1 is the only executable editorial semantic
  architecture.
- Accepted references remain 12 development and four held-out cases.
- The pre-IR builders, milestone generators, old frontend adapters, registries,
  review fixtures, and rich renderer are deleted and cannot be replayed.
- Frozen dossiers, source manifests, proof packets, receipts, provenance, and
  generated historical evidence remain in place as noncanonical evidence.
- Acquisition capability and tests remain intact.
- The representative route deliberately renders basic vote evidence and source
  receipts. The former `/golden-render-fixture` route is absent.
- The 71 historically staged artifacts remain unpublished; persistence,
  publication, database, deployment, and production state were not changed by
  the cutover.

The exact deletion, test-transfer, preservation, route, and validation record is
`docs/editorial/editorial_hard_cutover_v1_receipt.json`.

Canonical commands:

```powershell
python scripts/run_editorial_pipeline.py validate --tier semantic
python scripts/run_editorial_pipeline.py validate --tier domain --domain ECONOMY_TAXES
python scripts/run_editorial_pipeline.py validate --tier release --include-frontend
```
