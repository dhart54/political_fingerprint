# Editorial Current-State Index

The machine-readable authority is
`docs/editorial/current_state_index.json`. State is derived from its explicit
manifests and receipts, never directory modification time.

- New work owner: `backend.app.semantic_ir.pipeline.run_editorial_pipeline`.
- Accepted semantic references: 12 development plus four held-out cases.
- Commissioning domains represented by accepted references: `ECONOMY_TAXES`,
  `JUSTICE_PUBLIC_SAFETY`, and `ENVIRONMENT_ENERGY`.
- Public editorial registry: zero slices, explicitly recorded by
  `frontend/lib/editorialIssueProductionSlices.mjs`.
- Review-only artifacts: Economy, Justice, and Environment manifests listed in
  the JSON index.
- Persisted but unpublished historical state: 71 artifacts and zero publication
  selections, recorded by the persistence seed manifest and review packet.
- Historical/superseded artifacts: discoverable through the architecture
  inventory; none are implicit new-work inputs.

Canonical commands:

```powershell
python scripts/run_editorial_pipeline.py validate --tier semantic
python scripts/run_editorial_pipeline.py validate --tier domain --domain ECONOMY_TAXES
python scripts/run_editorial_pipeline.py validate --tier release
```

The release tier is not the default. Add `--include-persistence` or
`--include-frontend` only when those boundaries changed. No validation command
authorizes a write, publication, merge, or deployment.
