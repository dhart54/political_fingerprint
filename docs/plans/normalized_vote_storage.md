# Normalized vote storage execution plan

## Intent and bounds
Preserve all logical vote, API, analytics and governed editorial data while removing repeated roll-level context. Implement and prove off production; one draft PR; no merge, deployment, project creation, environment changes or production writes. M15B remains paused.

## Baseline
Verified main: 5843bab9b1bed3e5db57976bae3b05466f2cbafe. Isolated branch codex/normalize-vote-storage; unrelated root work untouched.
Read-only production census on 2026-09-15 01:57:51 UTC: 814,963 context rows, 2,298 rolls. Exact null-aware distinct comparison found zero conflicting rolls for chamber_session, vote_type, final_result, vote_margin, winning_position, party_vote_totals, bipartisan_majority, sponsor_party, context_source_list and context_version.

## Sequence / definition of done
- [x] Initial producer/consumer trace and exact shared-field equality.
- [ ] Choose smallest sound schema; bounded physical size estimate before implementation.
- [ ] Staged migration, deterministic ETL integration and compatibility reads.
- [ ] Actual source data / broad fixture complete parity, integrity, idempotency and failure proof.
- [ ] Realistic PostgreSQL storage and query benchmarks.
- [ ] Blue/green plan including all governed and service state, rollback and authorization gates.
- [ ] Relevant local tests, exact-head hosted CI, final diff review and draft PR.

Expected scope: approximately 10-20 implementation/test/document files; no generated editorial changes. Release-tier validation is required for this storage boundary. Historical pinned proofs retain their historical schema; normalized proof explicitly opts into the staged migration.

## Design investigation
A: existing roll_calls fields; B: typed one-to-one context relation; C: only JSON extraction. Choose A: roll_calls is the existing canonical owner. Add typed context fields there, retain a narrow member-context table, and expose the original vote_contexts logical columns through a join view. B adds a second one-to-one roll identity without an independent lifecycle; C leaves small but avoidable shared scalar duplication. The explicit context_version records derived-context availability; it does not replace source roll identity. Never choose arbitrary values on conflict. Preserve original timestamps and member-specific values. Database representation changes must retain the exact logical vote_contexts projection.

## Production and rollback
Production writes performed: no. Production migration execution is not authorized. Prefer a fresh green project because the source already exceeds its quota; retain untouched blue for connection rollback. No physical reclamation is claimed before old physical storage is removed or a green database is built.

## Blockers and reconciliation
Validation in progress. No readiness claim. Local Docker is starting; hosted PostgreSQL remains available if local engine cannot run.

## Pre-implementation size model
Production main context heap is 459,923,456 bytes and its indexes total 50,413,568 bytes. The sampled row is 531 bytes; two JSON fields account for about 404 bytes. Removing those alone leaves approximately 127 bytes per member before page packing. Retaining existing index cost and adding 25% packing margin gives about 130 MB member heap + 51 MB indexes + under 2 MB roll context, versus 510 MB currently. Estimated database end state: approximately 327 MB (conservative); moving all ten shared fields should reduce it further, toward 285 MB. These are estimates, not measured compaction results. At least 100 MB decimal headroom is plausible without removing evidence or indexes. Real PostgreSQL benchmark must confirm.

## First hosted proof
Commit 22954b62a25d250f5d905fb10669171a4436f3f7, run 34920042645: all nine jobs passed. Full actual cardinality restored; all 28 original table/column streams identical; 525 complete API outputs for 15 members identical (118/119/all); database 641,557,007 -> 238,436,879 bytes. Narrow member relation 100,040,704 bytes; roll relation 2,932,736 bytes. Conservative projection preserving other production allocation: 245,353,619 bytes. Benchmarks (ms before/after): history 2.796/3.882; evidence .244/.279; fingerprint 2.034/1.600; roll .122/.129; batch 6.150/8.365. Final expanded proof adds explicit 118, all active producer adapters, compatibility CRUD, conflict rejection, rollback and fresh normalized dump/restore.

Local focused tests: 34 pass. The broad local ingestion run exposes absent ignored backend/data_sources/senate_xml caches before exercising the changed code. Those historical tests and missing cache paths are unchanged from main; classify separately from normalization regressions. No cache substitute or weakened assertion is introduced.

## Expanded proof
986fe113fb347004c8d0f0ee00d3a3f665130900 / run 34920627839: all nine jobs pass, including all-scope complete API parity, full original table parity, active writer ingestion/idempotency, compatibility CRUD, ambiguity refusal/rollback and fresh compact dump/restore. Fresh restored DB: 230,121,999 bytes. Final head completes sequence preservation, detailed physical accounting and production-major-version PostgreSQL 17 coverage. Local broad result: 113 pass, 13 absent historical Senate XML cache failures. No production writes.
