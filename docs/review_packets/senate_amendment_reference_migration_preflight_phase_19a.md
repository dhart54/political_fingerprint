# Senate Amendment Reference Production Migration Preflight - Phase 19A

## Scope

Phase 19A preflights the production schema migration for `senate_amendment_references`.

The production migration was not applied because the exact approval phrase was not provided as an approval instruction.

## Main State

- starting main commit: `15c0b1ddea18a2bc5d55a480b3eda61628f501c7`
- branch: `codex/phase-19a-senate-amendment-migration`
- Phase 18 merge present: yes, commit `15c0b1d`
- migration present: `backend/migrations/0010_senate_amendment_references.sql`

## Approval Gate

Required approval phrase before applying the production migration:

> Approve production migration of senate_amendment_references for Phase 19A, with no amendment fact import, no vote_interpretations writes, no support/opposition changes, and no alignment changes.

This exact phrase was not provided as an approval. The phrase appeared in the milestone instructions as the required gate, so this run stopped after preflight.

## Production Read-Only Migration Validation

Validation mode:

- production reads only
- `default_transaction_read_only = on`
- no migration applied
- no data import run

Result:

- target table exists: no
- production migration applied: no
- migration creates target table locally: yes
- referenced tables present: `bills`, `roll_calls`, `vote_contexts`, `vote_interpretations`, `votes_cast`
- missing required referenced columns: none
- migration references `roll_calls(id)`: yes
- migration touches `vote_interpretations`: no
- migration has destructive drop: no
- migration has parent-bill index: yes
- migration has fact-status constraint: yes
- can apply cleanly in principle: yes

## Baseline Counts

Read-only baseline before any migration:

| Metric | Count |
| --- | ---: |
| `bills` | 266 |
| `roll_calls` | 512 |
| `votes_cast` | 164,067 |
| `vote_contexts` | 164,067 |
| `vote_interpretations` | 74 |
| `support_position IS NOT NULL` | 48 |
| `oppose_position IS NOT NULL` | 48 |

## Guardrails Confirmed

- production data changed: no
- production migration applied: no
- amendment fact data imported: no
- `bills` inserted/updated/deleted: no
- `roll_calls` inserted/updated/deleted: no
- `votes_cast` inserted/updated/deleted: no
- `vote_contexts` inserted/updated/deleted: no
- `vote_interpretations` inserted/updated/deleted: no
- support/opposition inputs changed: no
- alignment inputs changed: no
- PN nominations handled: no
- treaty/executive votes handled: no

## Next Step

If the user wants to apply the production schema migration, they should provide the exact approval phrase above.

Recommended next milestone after approval:

- Phase 19A production schema migration application and post-validation.

After the schema migration is applied and validated, Phase 19B should run a fresh production-aware dry-run before any amendment fact-only data import approval.
