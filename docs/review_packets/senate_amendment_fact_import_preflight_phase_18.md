# Senate Amendment Fact Import Preflight And Production Migration Validation - Phase 18

## Scope

Phase 18 prepares a production import preflight for the 112 safe 119th Congress / 2025 Senate amendment fact rows validated in Phase 17.

This milestone did not apply the production migration and did not import data.

## Production Migration Compatibility

Migration inspected:

- `backend/migrations/0010_senate_amendment_references.sql`

Production validation was read-only with `default_transaction_read_only = on`.

Result:

- target table exists in production: no
- production migration applied: no
- referenced tables present: `bills`, `roll_calls`, `votes_cast`, `vote_contexts`, `vote_interpretations`
- missing required referenced columns: none
- local migration creates `senate_amendment_references`: yes
- local migration references `roll_calls(id)`: yes
- local migration touches `vote_interpretations`: no
- local migration has destructive drop: no
- local migration has parent-bill index: yes
- local migration has fact-only status constraint: yes
- can apply cleanly in principle: yes

The migration was not applied.

## Manifest

Manifest:

- `docs/review_packets/senate_amendment_fact_import_manifest_phase_18.json`

Manifest summary:

- target amendment rolls: 112
- deferred rows: 1
- deferred roll: 344
- reason deferred: no usable statement of purpose
- scope: Senate, 119th Congress, 2025
- PN nominations: excluded
- treaty/executive votes: excluded
- unsupported rows: excluded
- interpretations included: no
- support/oppose inferred: no
- `counts_as_interpretation`: false

The manifest includes only rows with:

- amendment number
- amendment type
- amendment-to-amendment relationship when available
- parent bill type and number
- parent bill display/title when available
- amendment purpose
- expected member vote rows
- source XML path
- official Senate source URL
- proposed `senate_amendment_references` row

## Production-Aware Dry-Run

Command mode:

- `python -m app.etl.senate_amendment_facts --dry-run ../docs/review_packets/senate_amendment_fact_import_manifest_phase_18.json --production-read-only --skip-existing`

Production-aware dry-run result:

| Table | Planned inserts | Planned skips |
| --- | ---: | ---: |
| `bills` | 1 | 9 |
| `roll_calls` | 112 | 0 |
| `votes_cast` | 11,197 | 0 |
| `vote_contexts` | 11,197 | 0 |
| `senate_amendment_references` | 112 | 0 |
| `vote_interpretations` | 0 | 0 |

Additional validation:

- target rolls already existing in production: none
- target rolls with existing `vote_interpretations`: none
- unsupported target rows: none
- parse failures: none
- member mapping failures: none
- bill mapping failures: none
- amendment reference failures: none
- planned `vote_interpretations` inserts: 0
- planned `vote_interpretations` updates: 0
- planned `vote_interpretations` deletes: 0
- planned support/opposition impact: 0
- planned alignment impact: 0

## Amendment Identity Boundary

The future import would store parent-bill linkage and amendment identity separately:

- `roll_calls.bill_id` can point to the parent bill.
- `senate_amendment_references.roll_call_id` identifies the row as amendment evidence.
- `senate_amendment_references.amendment_number` preserves the specific Senate amendment.
- API serialization from Phase 17 labels these rows as `senate_amendment_fact`.
- `amendment_reference.counts_as_interpretation = false`.

This prevents amendment votes from being mistaken for parent-bill final passage or ordinary substantive issue-position evidence.

## Rollback Artifact

Rollback plan:

- `docs/review_packets/senate_amendment_fact_import_rollback_phase_18.sql`

Rollback scope:

- only the 112 Phase 18 target Senate roll numbers

Rollback behavior:

- aborts if target roll calls have `vote_interpretations`
- deletes target `senate_amendment_references`
- deletes target `vote_contexts`
- deletes target `votes_cast`
- deletes target `roll_calls`
- deletes target `bills` only if no remaining `roll_calls` reference them
- does not insert, update, or delete `vote_interpretations`
- leaves the `senate_amendment_references` table in place unless a separate schema rollback is explicitly approved

Rollback was not run.

## Risks

- The production migration is not applied yet; the future import must apply or verify the table before data import.
- The 112 target rows are fact-only. They improve source-grounded amendment visibility but do not create support/opposition or alignment evidence.
- Amendment rows may still need UI review after import to ensure amendment labels are displayed clearly wherever evidence is shown.
- Bill title enrichment remains limited to currently available parent-bill metadata; amendment identity is preserved separately.
- A combined schema-and-data import is efficient but riskier than a schema-only step followed by data import.

## Approval Gate

No production write is approved by this packet.

Recommended future approval phrase if schema and data are combined:

> Approve production migration and import of Phase 18 Senate amendment fact-only package for 112 amendment rolls, with senate_amendment_references enabled, no vote_interpretations writes, no support/opposition changes, no alignment changes, no PN nominations, no treaty/executive votes, and only 119th Congress / 2025 rows.

Safer split approval path:

1. First approve only the production migration:
   > Approve production migration for senate_amendment_references only, with no data import and no vote_interpretations writes.
2. Then approve the data import after another production-aware dry-run:
   > Approve production import of Phase 18 Senate amendment fact-only package for 112 amendment rolls, with no vote_interpretations writes, no support/opposition changes, no alignment changes, no PN nominations, no treaty/executive votes, and only 119th Congress / 2025 rows.

## Recommendation

Proceed next to Senate Amendment Fact Import Approval only if the user explicitly approves either the split migration-first path or the combined migration-and-data approval phrase.

Do not import amendment facts without a fresh production-aware dry-run immediately before the write.
