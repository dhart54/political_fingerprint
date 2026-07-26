# Editorial Pipeline V1 Handoff

## Post-cutover architecture

Editorial Semantic IR V1 is the repository's only executable editorial semantic
architecture. New work enters
`backend.app.semantic_ir.pipeline.run_editorial_pipeline` with reviewed shared
legislative semantics and exact member action, service, and evidence states.

The pipeline calls the pure compiler exactly once, validates the compiled graph,
preserves compiler-owned review routing, and exposes only meaning-preserving
review, presentation, and optional inert persistence-proposal payloads.
Publication remains a separate, unauthorized boundary.

Stage ownership:

1. Reviewed shared input and exact member states.
2. Semantic compilation in `backend/app/semantic_ir/compiler.py`.
3. Compiled validation in `backend/app/semantic_ir/validation.py`.
4. Compiler-owned review routing.
5. Meaning-preserving adapters in `backend/app/semantic_ir/adapters.py`.
6. Separately authorized persistence and publication systems.

The pre-IR eligibility, overlay, inference, conclusion, ownership, and routing
modules and milestone-specific builders were deleted in Editorial Hard Cutover
V1. They are not available for replay. Frozen outputs remain historical evidence
and are validated directly without executing their former generators.

## Preserved boundaries

- Accepted development and held-out Semantic IR references and receipts remain
  unchanged.
- Dossiers, manifests, proof packets, provenance, preservation receipts, raw
  evidence, and historical generated artifacts remain frozen.
- All acquisition clients, scrapers, downloaders, parsers, pagination, retries,
  caching, normalization, stable identifiers, source mappings, raw storage, and
  acquisition tests remain available.
- Migration `0016`, `backend/app/editorial_artifacts/`, import/export, backup,
  rollback, reconciliation, dependency-discovery tooling, and immutable audit
  history remain available and unchanged.
- Historical artifacts are not canonical inputs and do not imply current
  semantic authority, approval, production eligibility, or publication.

The exact classifications, deleted paths, transferred tests, preserved hashes,
and validation results are recorded in
`docs/editorial/editorial_hard_cutover_v1_receipt.json`.
The complete 119-file frozen-tree hash set is recorded in
`docs/editorial/frozen_historical_evidence_manifest_v1.json`.

## Frontend state

The old-format rich editorial runtime, selectors, registries, presentation
adapters, React components, fixture data, and review route are removed.

The representative page deliberately uses the basic evidence path:

- issue and representative selection remain available;
- the top profile panel reports neutral action and issue-area coverage only;
- exact vote evidence and official receipts remain available;
- procedural, limited-context, Present, and Not Voting states remain distinct;
- expected-but-missing actions are not supplied by the current production API
  and are not synthesized in React;
- React does not construct a broad analytical conclusion from vote counts;
- `/golden-render-fixture` is absent and returns 404.

An IR-native rich presentation is deferred to a separately reviewed milestone.
Database cleanup is also deferred and requires production dependency discovery,
validated recovery, and separate destructive authorization.

## Canonical commands

```powershell
python scripts/run_editorial_pipeline.py validate --tier semantic
python scripts/run_editorial_pipeline.py validate --tier domain --domain ECONOMY_TAXES
python scripts/run_editorial_pipeline.py validate --tier domain --case semir-dev-04-justice-mixed-fentanyl-trajectory
python scripts/run_editorial_pipeline.py validate --tier release --include-frontend
```

All commands are local and read-only. They do not authorize persistence,
publication, promotion, merge, deployment, or production access.
