# Legislative vote storage normalization â€” migration review

Status: implementation and hosted proof in progress. This is not production execution authority.

## Diagnosis and exact field classification
The current ETL computes one context per roll, then copies shared values into each member row. Current/historical Congress refresh, Senate fact/amendment import and fixture seeding are the active producers. They all use `build_vote_contexts`; that deterministic semantic calculation is unchanged.

| Fields | Meaning / new owner |
|---|---|
| chamber_session | Shared historical compatibility snapshot; preserve separately from canonical roll_calls.session |
| vote_type | Shared derived classification of roll question/description; roll_calls.context_vote_type |
| final_result, vote_margin, winning_position | Shared derived vote result; typed roll_calls context columns |
| party_vote_totals | Shared derived party counts, one JSONB value per roll |
| bipartisan_majority | Existing shared derived boolean; unchanged definition |
| sponsor_party | Shared compatibility field (currently null); retain rather than discard |
| context_source_list | Shared source identities, one JSONB value per roll |
| context_version | Shared deterministic computation version/availability marker |
| roll_call_id, legislator_id | Member-context identity; foreign keys to unchanged canonical entities |
| member_position, member_party, member_party_majority_position, member_voted_with_party_majority, member_voted_with_winning_side | Member-specific values; preserved verbatim, not recomputed |
| created_at, updated_at | Per-member historical timestamps; preserved verbatim |

The exact production null-aware census covered 814,963 rows and 2,298 rolls, not a sample. All ten candidate shared fields have zero within-roll conflicts. New imports reject ambiguity and drift rather than selecting an arbitrary member's version.

## Model choice and schema
Choose **A: existing roll_calls**. It is already the canonical roll identity and correct owner of these shared facts. B (a new 1:1 context table) adds an unnecessary identity join. C (moving only the two JSON fields) saves most space but leaves avoidable shared scalar duplication. No EAV, generic payload, editorial redesign, new governance version, or interpretation change.

Before: roll_calls + votes_cast + wide physical vote_contexts (814,963 repeated contexts).
After: roll_calls with ten typed nullable `context_*` columns (2,298 initialized owners) + unchanged votes_cast + narrow vote_context_members (814,963 rows). A security-invoker vote_contexts view projects the exact original column names/order/types and joins the owner. Uninitialized context is permitted for a canonical roll that has no member context, matching the prior optional relation. Triggers reject member rows without initialized owners and changes to shared facts while member rows exist.

RLS remains enabled on canonical rolls and is enabled on member rows. Anonymous/authenticated/PUBLIC access to the new view/table is revoked. No security-definer elevation is introduced. The backend continues using its existing database access boundary.

## Producers, consumers and compatibility
- Current Congress refresh (also used by historical refresh), Senate fact import, Senate amendment import, and seed bulk writes use the normalized adapter when explicitly configured with `NORMALIZED_VOTE_STORAGE=1`.
- The adapter validates the complete batch, locks canonical roll owners in deterministic order, initializes each shared owner once, inserts only new member rows, and rejects existing shared/member drift. Repeated equal ingestion writes zero rows.
- Existing legacy-schema behavior remains the default until separately authorized cutover. Enabling the flag against a legacy schema fails; failing to enable it for normalized bulk ETL fails instead of silently duplicating data.
- Public evidence/history queries, manual interpretation reads, universe discovery, historical/session-2/Senate evidence readers continue through the same logical vote_contexts name. No public frontend/API field is changed.
- Compatibility INSERT/UPDATE/DELETE triggers support logical one-row tools. Raw ON CONFLICT bulk operations and TRUNCATE require the adapted producers; they are not claimed to work automatically on a view.
- Historical production operators retain their exact target/schema/authority gates. Old production authorizations must not be replayed against a new target. Their historical regression schema is unchanged; the migration is staged and opt-in.
- Fingerprint computation, classifiers, summaries and drift calculations are unchanged. Original data columns are compared exactly, including timestamps.

## Storage and performance proof
Baseline production: 653,929,619 bytes; contexts 510,492,672 bytes; roll_calls 1,056,768 bytes. Existing context indexes total 50,413,568 bytes. The pre-implementation conservative estimate is around 327 MB total (roughly 130 MB member heap + 51 MB index allowance + under 2 MB owner context + existing other data). The optimistic all-ten-field model is approximately 285 MB. These remain estimates until hosted measurements below are filled.

The 7,465,932-byte public-only snapshot (SHA256 5c3bbf50327d3a531cec21518b9165b68f8d05a7866a20e3c3d421260a916f7d) preserves all 28 public tables. Its representation stores shared contexts once only after proving exact equality in the same read-only transaction. It is not a reduced member sample. It includes 158 editorial artifacts, eight batches, 167 relationships and all four publication rows. A supplemental read-only capture at 2026-09-15 02:20:34 UTC preserves all 17 sequence last_value/is_called pairs, including intentional gaps (artifact sequence 247 with active Education artifact 245). Sequence state is checked after normalization and fresh restore. Sequence reads are not MVCC snapshots; final cutover requires a fresh capture under the write freeze.

The existing PostgreSQL CI lane explicitly checks out the PR head, restores actual complete cardinalities, compares original table streams and complete API JSON, checks migration parity, measures physical storage and benchmarks five paths. No timestamps or response fields are removed from parity comparisons. Existing legitimate 404 responses are compared with their complete status/detail/headers; server errors fail the proof. Scopes are 118, 119 and all. Public records are never generated synthetically for the production snapshot.

A single full-population proof is justified for this migration; no permanent additional CI job is introduced. It is change-gated to affected ETL/schema/proof/workflow paths so unrelated future PRs do not replay the population. Docker is unavailable locally (engine returns HTTP 500), so actual PostgreSQL evidence comes from hosted CI. Local focused tests: 34 passed. First hosted proof on 22954b62a25d250f5d905fb10669171a4436f3f7: all nine jobs passed (run 34920042645). Full 28-table parity and 525 API responses for 15 representatives passed. Fresh legacy database: 641,557,007 bytes; normalized: **238,436,879 bytes** (227.39 MiB). Narrow member relation: 100,040,704 bytes; roll relation: 2,932,736 bytes. Keeping every other production relation allocation unchanged projects **245,353,619 bytes**, leaving 254.65 MB below a 500,000,000-byte quota. Reserve another 30 MB for managed overhead/growth uncertainty: still roughly 275 MB, well below the 400 MB target.

| Query | Before ms | Normalized ms |
|---|---:|---:|
| Representative history | 2.796 | 3.882 |
| Issue evidence | .244 | .279 |
| Fingerprint aggregation | 2.034 | 1.600 |
| Roll lookup | .122 | .129 |
| Batch analysis | 6.150 | 8.365 |

Five warmed EXPLAIN ANALYZE executions per path; median reported. History/batch gain a hash join against the 2,298-row roll relation; evidence/roll lookup retain indexed member/roll access. No index was added in response to speculative performance fears. Physical savings are measured in a disposable PostgreSQL 16 database; final green PostgreSQL version and managed-service behavior must also pass pre-cutover validation. The final expanded head, on PostgreSQL 17 to match production’s major version, additionally covers explicit 118, active producer adapters, compatibility CRUD, migration ambiguity rollback and a fresh normalized dump/restore; results pending.

The broader local regression run produced **113 passes and 13 historical cache-dependent failures**. Local broad historical ingestion tests requiring ignored Senate XML caches cannot run in a clean checkout: missing backend/data_sources/senate_xml/members.xml, before changed code is exercised. No production source fetch or fixture substitution was used to hide the baseline limitation.

## Recommended production strategy: blue/green, not in-place
Do not load the old 624 MB layout into a fresh Free project first. Normalize on a separately authorized disposable/local clone, verify it, then load only the compact normalized end state into green. Dropping columns alone does not reclaim their physical bytes. The staged migration creates a compact member relation, checks exact complete parity, and drops the old physical relation on the clone. A logical restore of the resulting schema/data creates compact files in green.

In-place is not recommended: source database already exceeds the quota; migration requires a replacement member heap/indexes, roll updates, parity-sort temporary files, WAL and locks while old storage still exists. Actual available disk/WAL quota is not established. No in-place or compaction production commands are authorized or supplied as executable defaults.

### Exact proposed sequence, after separate authorization
1. Verify current source identity, main/implementation head, source size, read-only default state, data/registry hashes and complete field-equality census. Confirm a second project slot and Free resource limits. Reserve time for validation. Do not disable quota protections.
2. Freeze all application/ETL/editorial writes operationally for the final capture and cutover window; public reads continue. Keep M15B paused. If writes cannot be frozen, stop: no unproven dual-write/delta-replication design is included.
3. Take a fresh consistent logical export using a reviewed least-privilege read-only session and a protected external credential mechanism. Copy every public table, original primary keys, timestamps, sequences, constraints, RLS, grants, triggers and functions. Preserve all editorial artifacts, payloads, content hashes, batch identities, relationships, registry pointers and publication metadata exactly. Do not regenerate governed or derived state.
4. Restore that export into a controlled disposable clone with sufficient temporary disk. Apply the staged normalization, run full original-column/table and API parity, inspect constraints/RLS, run idempotency/fault checks and performance benchmarks. Confirm projected Supabase end size <=400,000,000 bytes, with an explicit safety margin for managed schemas/WAL outside database-size accounting. Produce a normalized logical dump and validate restore into a second disposable database.
5. Create green only after project/region/version and capacity approval. Provision the normalized schema and load the verified normalized data directly. Restore sequence positions as well as rows. Reconcile Supabase-managed roles/extensions rather than blindly overwriting managed schemas or role passwords. Disable any copied scheduled/external-call integrations until reviewed.
6. Recheck service state. Read-only inspection currently found zero auth users, identities, sessions and refresh tokens; zero storage buckets/objects; zero realtime subscriptions; zero vault secrets; no cron.job table. If any become nonzero, stop for a reviewed service migration: auth data/settings and signing-key/session behavior, storage object bytes plus metadata/policies, realtime configuration and integrations must be handled explicitly. Do not infer that a database dump includes storage object bytes or project configuration.
7. Validate green before cutover: original-column hashes for all public tables, exact editorial hashes and registry state, original sequences, service inventory, complete endpoint parity across reviewed and other House/Senate members and 118/119/all, source provenance=database, fingerprints/interpretations unchanged, all constraints valid, RLS/grants least-privilege, measured size under target and acceptable query plans. Test normalized ingestion only on the disposable copy, not by adding a fake production action.
8. After explicit cutover approval, update Render DATABASE_URL via its protected secret configuration and set NORMALIZED_VOTE_STORAGE=1 for every ETL writer. Deploy the reviewed backend head. Rebind separately reviewed target identity pins and any later production operator authorities; do not copy old-target approval as new authorization. Vercel's API URL need not change when Render's public URL stays the same. Verify whether any direct Supabase client/keys exist in deployed configuration; if so, review those individually before changing them.
9. Run read-only post-cutover smoke/parity and health/provenance checks. Keep writes frozen during acceptance. Confirm all four Foushee registry roots, complete current/historical ledgers, accepted wording, API response shapes and measured storage. Resume permitted routine writes only after acceptance; M15B still requires its own fresh authorization package.
10. Retain blue unchanged for an agreed rollback period. Decommission/delete it only under separate authorization after backup/restore evidence and stable operation. No automatic retirement is included.

### Data that may be reconstructed versus must be copied
Upstream public votes/rolls and deterministic contexts are theoretically reconstructible, but this cutover copies existing records and normalizes them losslessly; it does not fetch evolving upstream sources and assume equality. All evidence/source identity, interpretations, classifications, fingerprint windows, summaries, drift, historical/pending/accepted editorial artifacts, authority/provenance, registry metadata and unique service state must be copied and hash/content verified. Recomputing analytics is a parity test, not permission to replace stored history.

### Rollback
Before writes resume: point Render back to the preserved blue DATABASE_URL, restore NORMALIZED_VOTE_STORAGE=0 and the prior accepted backend deployment, then repeat the read-only public smoke. The API hostname and Vercel configuration remain unchanged. Verify blue's exact captured registry/data hashes and database provenance. Green remains retained for diagnosis; do not perform reverse schema mutation on blue.

After new writes have been accepted on green: connection rollback alone would lose those writes. Freeze writers and obtain a separately reviewed reconciliation/export plan before switching back. There is no automatic reverse migration or blanket batch rollback. This distinction is a hard cutover gate.

## Authorization boundaries and M15B
Creating green, exporting protected service state, loading/migrating a production target, changing Render/Supabase/Vercel configuration, deploying/cutting over, enabling writes, rebinding production authorities and retiring blue each require later explicit authorization. Current production writes: no. No environments or projects were switched. M15B stays paused; after migration its existing preparation must be refreshed against the new target/schema and reviewed before persistence or publication.

## Sources
- PostgreSQL physical reclamation: https://www.postgresql.org/docs/17/sql-altertable.html
- Supabase logical migration: https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore
- Supabase backups do not include Storage object bytes: https://supabase.com/docs/guides/platform/backups
- Supabase size/quota accounting: https://supabase.com/docs/guides/platform/database-size

## Unresolved gates
Hosted proof and final review are pending. A second Free-project slot, target version/region, actual destination managed-schema overhead, protected credentials, operational write freeze, final live capture, green restore validation and cutover authorization remain execution prerequisites. No claim of current production migration readiness is made until implementation proof completes.

## Growth budget
Using the source votes_cast allocation plus measured narrow-member and roll storage gives roughly 265 bytes per additional member-vote/context pair at similar packing/cardinality. The conservative 245.35 MB estimate leaves room for approximately 0.96 million additional such pairs before 500 MB, or approximately 0.58 million before a 400 MB operating threshold, excluding growth elsewhere. This is a planning estimate, not an indefinite free-tier guarantee. Review capacity at 350 MB and prepare the next capacity decision before 400 MB; no history is pruned automatically.

## Expanded proof on 986fe113fb347004c8d0f0ee00d3a3f665130900
All nine jobs passed in run 34920627839. All 28 original table streams and 525 complete API outputs (15 representatives, 118/119/all) match after normalization and after fresh normalized dump/restore. New ingestion through all active adapters, exact re-ingestion, shared-drift rejection, compatibility CRUD and transactional rollback pass. Normalized size 238,346,767 bytes; fresh restore 230,121,999 bytes; conservative production projection 245,337,235 bytes. First and expanded proofs both covered all three scopes. Final head adds captured sequence-state preservation, per-field/index/heap accounting, PostgreSQL 17 validation, and change-gating of this full-population CI step.
