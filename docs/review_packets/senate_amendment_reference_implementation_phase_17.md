# Senate Amendment Reference Implementation - Phase 17

## Scope

Phase 17 implements first-class local handling for 119th Congress / 2025 Senate amendment fact rows.

This is not a production import packet. No production data was imported or modified.

## Why This Was Needed

Phase 16 found that Senate amendment votes should not be stored as ordinary parent-bill roll calls alone. If an amendment vote only points at the parent `bill_id`, the API and review surfaces can mistake it for parent-bill final passage or generic parent-bill evidence.

Phase 17 preserves amendment identity while keeping the row fact-only and non-counting.

## Schema Model

Migration:

- `backend/migrations/0010_senate_amendment_references.sql`

New table:

- `senate_amendment_references`

The table is keyed one-to-one to `roll_calls` by `roll_call_id` and stores:

- Senate amendment number
- amendment type
- amendment-to-amendment number, when present
- parent bill type
- parent bill number
- parent bill display label
- amendment purpose
- official source URL
- local XML source path
- `fact_status = fact_only_uninterpreted`

The model allows `roll_calls.bill_id` to point at the parent bill while `senate_amendment_references` preserves that the vote was on a Senate amendment, not final passage of the parent bill.

## Parser And Planner

Updated helper:

- `backend/app/etl/senate_amendment_facts.py`

The helper reads cached official Senate XML and builds a local review manifest for amendment fact rows. It validates that each included row is:

- Senate chamber
- 119th Congress
- calendar year 2025
- a Senate amendment row
- linked to a resolvable parent bill
- backed by an amendment purpose
- backed by member vote rows
- fact-only, with no interpretations included

The local planner reports future inserts for:

- `bills`
- `roll_calls`
- `votes_cast`
- `vote_contexts`
- `senate_amendment_references`

It plans zero inserts, updates, or deletes for `vote_interpretations`.

## API Evidence Labeling

Updated backend serialization:

- `backend/app/api/precomputed.py`

Evidence rows now left join `senate_amendment_references`. Rows with an amendment reference are serialized with:

- `evidence_type = senate_amendment_fact`
- `amendment_reference`
- `amendment_reference.counts_as_interpretation = false`

Rows without amendment references remain:

- `evidence_type = roll_call_vote`
- `amendment_reference = null`

This makes amendment rows distinguishable from parent-bill final passage in API evidence payloads.

## Counting And Alignment Policy

Senate amendment reference rows remain fact-only unless a separate, reviewed `vote_interpretations` row is later approved.

They do not:

- create `vote_interpretations`
- set `support_position`
- set `oppose_position`
- alter support/opposition counts
- alter alignment
- promote readiness
- make substantive issue-position claims
- describe parent-bill final passage

## Phase 16 Candidate Validation Against Phase 17 Model

Manifest:

- `docs/review_packets/senate_amendment_reference_manifest_phase_17.json`

Validation result:

- safe future amendment fact candidates: 112
- deferred amendment rows: 1
- deferred roll: 344
- reason deferred: no usable statement of purpose

Planned future inserts if a later import is separately approved:

- bills: 10
- roll_calls: 112
- votes_cast: 11,197
- vote_contexts: 11,197
- senate_amendment_references: 112
- vote_interpretations: 0

The manifest is a validation artifact, not import approval.

## Production Status

Production data changed:

- no

Production writes performed:

- none

Supabase writes performed:

- none

Imports performed:

- none

## Risks

- The migration is local only until explicitly applied in production.
- Frontend display can consume the API label once amendment facts are imported, but no UI changes are included in this milestone.
- Amendment facts remain useful context only; they are not substantive support/opposition evidence without a separate reviewed interpretation.
- A future import must ensure rollback is scoped to the exact target roll calls and cannot touch existing House data or interpreted rows.

## Future Import Gate

Before any production amendment fact import:

1. Apply and verify the amendment reference migration in production.
2. Generate a bounded import manifest from current cached XML.
3. Run a production-aware dry-run.
4. Confirm planned `vote_interpretations` writes are zero.
5. Confirm all target rows have complete member and bill mapping.
6. Generate rollback SQL scoped only to target roll calls.
7. Receive explicit production import approval.
8. Run post-import validation proving no support/opposition or alignment impact.

## Recommended Next Milestone

Senate Amendment Fact Import Preflight.

That milestone should be preflight only unless explicitly approved, and should prepare production migration validation, bounded import counts, rollback SQL, and post-import checks before any production write.
