# Amendment Evidence Pipeline Inventory And Canonical Path

This document records the evidence-based inventory for the amendment-source consolidation milestone. It does not authorize new production classifications, interpretations, or schema changes.

## Inventory

| Surface | Active caller or runbook | Classification | Notes |
| --- | --- | --- | --- |
| `backend/app/etl/amendment_evidence.py` | `source_packets`, bounded write modules, `test_amendment_evidence.py` | canonical reusable runtime | Shared amendment identity, canonical stage list, interpretation counting boundary, and production-write preconditions. |
| `backend/app/etl/fetch_sources.py` | `docs/methodology.md`, contact workflow, chamber adapters, live/historical/current refresh | canonical reusable runtime | Fetch/cache utility for House Clerk, Senate XML, members, and Congress.gov bill/subresource cache. |
| `backend/app/etl/congress_adapter.py` | House/Senate adapters, manual packets, source packets, tests | canonical reusable runtime | Normalizes Congress.gov bill cache and enrichment subresources. |
| `backend/app/etl/house_clerk_adapter.py` | `ingest`, current/historical refresh, live pipeline, tests | source adapter | House roll-call XML adapter; preserves House roll/session identity. |
| `backend/app/etl/senate_xml_adapter.py` | `ingest`, Senate fact/amendment import, current/historical refresh, tests | source adapter | Senate XML adapter; preserves Senate roll/session identity and parent bill parsing. |
| `backend/app/etl/source_packets.py` | `amendment_companion_enrichment`, `test_source_packets.py` | canonical reusable runtime | Builds Congress.gov source packets from existing cache; now uses shared House amendment identity parsing. |
| `backend/app/etl/manual_interpretations.py` | `docs/manual_interpretation_workflow.md`, Phase 21 import, tests | canonical reusable runtime | Export/import of reviewed interpretation packets; validates neutral language and support/opposition boundaries. |
| `backend/app/etl/supervised_enrichment.py` | `docs/methodology.md`, `docs/review_packets/supervised_enrichment_operating_model_phase_7.md`, tests | canonical reusable runtime | Offline review-artifact validator and approval checklist; no production writes. |
| `backend/app/etl/vote_context.py` | API fallback, seed, fact import, current/historical refresh, tests | canonical reusable runtime | Builds vote type/result/member context used by packets and API. |
| `backend/app/etl/compute.py`, `classify.py`, `interpret.py`, `ingest.py`, `run_all.py`, `seed.py` | development workflow, deployment docs, API fallback, tests | canonical reusable runtime | Fixture/precompute path from source rows to public outputs. |
| `backend/app/api/precomputed.py` and API route wrappers | public API, Render smoke workflow, tests | canonical reusable runtime | Serializes public profile, position, evidence, alignment, comparison, lookup, and metadata outputs. Includes `senate_amendment_references` in evidence rows. |
| `backend/app/etl/amendment_companion_enrichment.py` | `docs/methodology.md`, `docs/review_packets/generalized_amendment_companion_enrichment_phase_2.md`, tests | bounded job/orchestrator | Offline House amendment companion workflow. Reads manual packets and cache, writes review artifacts only. |
| `backend/app/etl/senate_amendment_facts.py` | Phase 16-19 review packets, tests | bounded job/orchestrator | Senate amendment fact manifest, schema compatibility, dry-run/import path. Production writes require exact approval and rollback. |
| `backend/app/etl/senate_evidence_classification.py` | Phase 20B review packets, tests | bounded job/orchestrator | Deterministic classification of already-loaded Senate facts. Now uses shared write preconditions. |
| `backend/app/etl/senate_enrichment_phase21.py` | Phase 21 review packets, tests | bounded job/orchestrator | Priority Senate classification and interpretation batch workflow. Now uses shared write preconditions. |
| `backend/app/etl/senate_118_amendment_enrichment.py` | active plan `118th_senate_amendment_source_enrichment.md`, review packet, tests | bounded job/orchestrator | 118th Senate amendment source packets and update path. Closest model for next House amendment milestone. |
| `backend/app/etl/evidence_118_expansion.py` | active plan/review packet for 118th historical expansion, tests | historical backfill | Completed 118th expansion backfill. Kept importable for rollback/audit/tests; now uses shared write preconditions. |
| `backend/app/etl/session2_evidence_expansion.py` | 2026/session-2 plan, methodology idempotency note, tests | historical backfill | Completed session-2 expansion backfill. Kept importable for rollback/audit/tests; now uses shared write preconditions. |
| `backend/app/etl/ndaa_amendment_interpretations.py` | NDAA review packets, tests | historical backfill | One-time NDAA amendment interpretation support retained for provenance. |
| `backend/app/etl/senate_fact_import.py` | Phase 12/14 review packets, tests | historical backfill | Fact-only Senate import path, predecessor to amendment fact import. Retained for audit and test coverage. |
| `backend/app/etl/current_congress_refresh.py`, `historical_congress_refresh.py`, `live_pipeline.py` | workflow docs, methodology, tests | bounded job/orchestrator | Broader roll-call ingestion/refresh; adjacent to amendment evidence but not amendment-family-specific. |
| `scripts/run_real_data_*.py` | script entry points and tests | bounded job/orchestrator | Local live-pipeline runners with dry-run option. |
| `backend/tests/test_*amend*`, `test_source_packets.py`, `test_supervised_enrichment.py`, `test_manual_interpretations.py`, API tests | CI and local validation | test or fixture | Contract and regression coverage for source packets, identity, write gates, API evidence serialization, and public output behavior. |
| `docs/review_packets/*.md`, `*.json`, `*.sql` | review/audit provenance | historical backfill | Completed preflight, rollback, manifest, and post-validation artifacts. Do not remove based on filename alone. |

No module was proven obsolete or superseded enough to remove during this milestone. Historical modules remain importable because tests, review packets, and rollback provenance still reference them.

## Data Flow

1. `fetch_sources` caches House Clerk XML, Senate XML, members, and Congress.gov bill/subresources.
2. Chamber adapters normalize cached XML into roll calls, bills, votes, and context-ready rows.
3. `vote_context` builds member-level vote type/result/context without deciding issue meaning.
4. Source-packet builders combine roll-call facts, Congress.gov bill/subresources, and amendment identity into review packets.
5. Deterministic classification code evaluates eligibility and issue domain; amendment rows use direct amendment purpose/identity before parent context.
6. Manual or supervised interpretation packages validate source basis, neutral language, support/opposition positions, and non-counting procedural/ambiguous boundaries.
7. Bounded write entry points run preflight, require exact approval, name exact target rows, require rollback location, and then write only approved tables.
8. Recompute paths refresh precomputed outputs after approved writes.
9. API readers serialize precomputed/profile/evidence outputs, including amendment reference context where present.
10. Post-write validation and idempotency checks confirm no unexpected support/opposition, alignment, readiness, chamber, session, or public-output changes.

## Duplicated Logic Found

- Amendment identity parsing existed separately in House source packets, Senate amendment fact manifests, Senate classification manifests, and 118th Senate source packets.
- Write gates repeatedly checked approval phrases, dry-run errors, rollback SQL paths, and zero interpretation writes in local ways.
- Classification rollback SQL generation is still milestone-specific because inserted/updated row restoration differs by package.
- Interpretation package validation existed in both `manual_interpretations` and Phase 21 batch validation; Phase 21 intentionally adds milestone caps and amendment/final-passage checks on top of the reusable manual validator.

## Canonical Amendment Evidence Path

Use `backend/app/etl/amendment_evidence.py` as the shared contract and keep source-family code as configuration or bounded orchestration unless a source truly needs a new adapter.

1. Fetch/cache source records with `fetch_sources`.
2. Normalize identity and relationships with `AmendmentIdentity`; preserve amendment-to-amendment, en-bloc/printed amendment labels, parent measure, chamber, Congress, and session.
3. Validate direct-source grounding. Amendment purpose/text/description is primary; parent measure context is supporting only.
4. Classify eligibility and issue deterministically. No LLM or source packet may decide support/opposition.
5. Build interpretation package through manual/supervised validators.
6. Preview writes with exact target row ids, table effects, counting impact, and not-voting/procedural treatment.
7. Capture rollback before writes.
8. Perform bounded writes only through entry points guarded by `WritePrecondition`.
9. Recompute affected precomputed outputs.
10. Reconcile API/public outputs and table counts.
11. Rerun preflight/import or idempotency checks to prove no additional writes are needed.

## Next 118th House Amendment Entry

The next House amendment milestone should not add a new permanent ETL module by default. It should:

- export scoped manual packets with `manual_interpretations`;
- feed those packets to `amendment_companion_enrichment` and `source_packets`;
- rely on `parse_house_amendment_identity` for printed amendment identity;
- add structured package data or configuration for the selected House amendment families;
- validate candidate records with `supervised_enrichment` and `manual_interpretations`;
- use a small bounded orchestrator only if the package needs production-backed preflight, rollback generation, and import caps that cannot be expressed as data/configuration.

A new permanent source adapter would be justified only if House amendment text must come from a new authoritative source format that `fetch_sources`, Congress.gov bill amendments, or existing House Clerk XML cannot represent.
