# Senate Amendment Reference Migration And Fact-Only Import - Phase 19

## Approval

Approval phrase received:

> Approve production migration and fact-only import of the Phase 18 Senate amendment package for 112 amendment rolls, with senate_amendment_references enabled, no vote_interpretations writes, no support/opposition changes, no alignment changes, no PN nominations, no treaty/executive votes, and only 119th Congress / 2025 rows.

## Migration Validation

Migration applied:

- `backend/migrations/0010_senate_amendment_references.sql`

Schema validation after migration:

- `senate_amendment_references` exists: yes
- expected columns present: yes
- primary key present: yes
- foreign key to `roll_calls(id)` present: yes
- check constraints present: yes
- parent-bill index present: yes
- fact-status index present: yes
- row count before import: 0

Validated columns:

- `roll_call_id`
- `amendment_number`
- `amendment_type`
- `amendment_to_amendment_number`
- `parent_bill_type`
- `parent_bill_number`
- `parent_bill_display`
- `amendment_purpose`
- `source_url`
- `source_xml_path`
- `fact_status`
- `source_version`
- `created_at`
- `updated_at`

## Pre-Import Baseline Counts

| Metric | Before |
| --- | ---: |
| `bills` | 266 |
| `roll_calls` | 512 |
| `votes_cast` | 164,067 |
| `vote_contexts` | 164,067 |
| `vote_interpretations` | 74 |
| `support_position IS NOT NULL` | 48 |
| `oppose_position IS NOT NULL` | 48 |
| House `roll_calls` | 339 |
| House `votes_cast` | 146,772 |
| House `vote_contexts` | 146,772 |

## Final Pre-Import Dry-Run

Production-aware dry-run after migration:

- errors: none
- manifest candidate rows: 112
- deferred rows: 1
- deferred roll: 344
- unsupported rows: none
- parse failures: none
- member mapping failures: none
- bill mapping failures: none
- amendment reference failures: none
- support/oppose inferred: false
- alignment impact possible: false

Planned writes:

| Table | Planned inserts | Planned skips |
| --- | ---: | ---: |
| `bills` | 1 | 9 |
| `roll_calls` | 112 | 0 |
| `votes_cast` | 11,197 | 0 |
| `vote_contexts` | 11,197 | 0 |
| `senate_amendment_references` | 112 | 0 |
| `vote_interpretations` | 0 | 0 |

Planned `vote_interpretations` updates: 0

Planned `vote_interpretations` deletes: 0

## Import Result

Actual inserted/skipped counts:

| Table | Inserted | Skipped |
| --- | ---: | ---: |
| `bills` | 1 | 9 |
| `roll_calls` | 112 | 0 |
| `votes_cast` | 11,197 | 0 |
| `vote_contexts` | 11,197 | 0 |
| `senate_amendment_references` | 112 | 0 |
| `vote_interpretations` | 0 | 0 |

Actual `vote_interpretations` updates: 0

Actual `vote_interpretations` deletes: 0

## Post-Import Validation

| Metric | Before | After | Changed As Expected |
| --- | ---: | ---: | --- |
| `bills` | 266 | 267 | yes, +1 |
| `roll_calls` | 512 | 624 | yes, +112 |
| `votes_cast` | 164,067 | 175,264 | yes, +11,197 |
| `vote_contexts` | 164,067 | 175,264 | yes, +11,197 |
| `vote_interpretations` | 74 | 74 | yes, unchanged |
| `support_position IS NOT NULL` | 48 | 48 | yes, unchanged |
| `oppose_position IS NOT NULL` | 48 | 48 | yes, unchanged |
| House `roll_calls` | 339 | 339 | yes, unchanged |
| House `votes_cast` | 146,772 | 146,772 | yes, unchanged |
| House `vote_contexts` | 146,772 | 146,772 | yes, unchanged |

Target-row validation:

- target Senate amendment `roll_calls`: 112
- target `votes_cast`: 11,197
- target `vote_contexts`: 11,197
- target `senate_amendment_references`: 112
- target `vote_interpretations`: 0

Post-import skip-existing dry-run:

- planned `bills` inserts: 0
- planned `roll_calls` inserts: 0
- planned `votes_cast` inserts: 0
- planned `vote_contexts` inserts: 0
- planned `senate_amendment_references` inserts: 0
- planned `vote_interpretations` inserts/updates/deletes: 0
- errors: none

## Guardrails Confirmed

- no `vote_interpretations` inserts, updates, or deletes
- no support/opposition input changes
- no alignment input changes
- no House rows changed
- no PN nominations handled
- no treaty/executive votes handled
- roll 344 remains deferred
- amendment rows remain fact-only

## Rollback

Rollback artifact:

- `docs/review_packets/senate_amendment_fact_import_rollback_phase_18.sql`

Rollback scope:

- only the 112 Phase 18 target amendment rolls

Rollback behavior:

- aborts if target roll calls have `vote_interpretations`
- deletes target `senate_amendment_references`
- deletes target `vote_contexts`
- deletes target `votes_cast`
- deletes target `roll_calls`
- deletes target `bills` only if no remaining roll calls reference them
- does not touch `vote_interpretations`
- leaves the `senate_amendment_references` table in place unless a separate schema rollback is explicitly approved

Rollback was not run.

## Risks And Follow-Ups

- These rows are fact-only; they should not be surfaced as substantive support/opposition evidence unless later interpreted through the supervised review process.
- Frontend display should continue to rely on the already-merged `senate_amendment_fact` labeling and `counts_as_interpretation = false`.
- Future amendment enrichment should review whether any of these amendment facts deserve substantive interpretations, but that must be a separate source-grounded process.

## Recommended Next Milestone

Senate Amendment Evidence Display Spot Check And Optional Compression.

That milestone should verify how amendment fact rows appear in evidence payloads and whether visible amendment labeling reduces confusion without creating issue-position claims.
