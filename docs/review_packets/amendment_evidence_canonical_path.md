# Amendment Evidence Canonical Path Review Packet

## Scope

This milestone consolidated amendment-evidence architecture before the next 118th House amendment expansion. It added no new production classifications, interpretations, source families, schema changes, or production writes.

## What Changed

- Added `backend/app/etl/amendment_evidence.py` as the shared amendment evidence contract:
  - canonical stage list;
  - House and Senate amendment identity normalization;
  - interpretation counting-boundary validator;
  - production-write precondition validator.
- Wired House source packets through shared House amendment identity parsing while preserving the existing `parse_house_amendment_hint` API.
- Wired bounded write entry points through the shared `WritePrecondition` guard:
  - `senate_evidence_classification`;
  - `senate_enrichment_phase21`;
  - `senate_118_amendment_enrichment`;
  - `evidence_118_expansion`;
  - `session2_evidence_expansion`.
- Added `backend/tests/test_amendment_evidence.py`.
- Added mandatory backend CI slice in `.github/workflows/backend-tests.yml`.
- Pinned `backend/requirements.txt` to exact package versions used by the tested environment.
- Documented inventory, callers, call path, duplicated logic, and next House entry path in `docs/amendment_evidence_pipeline.md`.

## Guardrails

- Parent-measure context remains supporting context only for amendment votes.
- Procedural, ambiguous, and insufficient-evidence rows remain non-counting unless separately reviewed and approved.
- Not-voting remains excluded from support/opposition.
- LLMs remain outside eligibility, vote meaning, alignment, readiness, and evidence-tier decisions.
- Historical backfill modules were not removed because tests, review packets, and rollback provenance still reference them.

## Validation

- Baseline selected backend suite before code changes: `91 passed in 68.57s` after elevated rerun due Windows pytest basetemp cleanup permission error.
- Post-change selected backend suite: `98 passed in 68.67s` after elevated rerun due the same Windows pytest basetemp cleanup permission error.
- Full backend suite after corrections: `293 passed in 266.37s`.
- Full-suite cleanup/correction: updated stale tests to expect session-aware House/Senate roll-call ids and supported resolution references; added `sconres` to the Senate fact-only importer allowlist so Phase 14 dry-run matches its manifest.

## Production Writes

None performed.

## Next 118th House Handoff

Use `manual_interpretations` export, `amendment_companion_enrichment`, `source_packets`, `supervised_enrichment`, and the shared `amendment_evidence` contracts. Add structured package data/configuration first. Add a new permanent module only if a new authoritative House amendment source format cannot be represented by existing fetch/cache/adapters.
