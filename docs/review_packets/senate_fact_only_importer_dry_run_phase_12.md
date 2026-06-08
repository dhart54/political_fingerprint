# Senate Fact-Only Importer Dry-Run - Phase 12

Date: 2026-06-08

Scope: minimum implementation and dry-run validation for the Phase 11 Senate fact-only expansion manifest.

No production data was written. No import was run. No Supabase rows were modified. No `vote_interpretations` rows were created, updated, or deleted. No UI, API shape, support/opposition counting, or alignment logic changed.

## Implementation Summary

Phase 12 adds a bounded facts-only dry-run path for Senate vote facts.

Added:

- H.J.Res. and H.Con.Res. parsing support in the Senate XML adapter.
- `backend/app/etl/senate_fact_import.py`, a manifest-bounded dry-run helper/CLI.
- targeted tests for parser support and dry-run safety behavior.
- Phase 12 rollback planning SQL.

The dry-run path is deliberately separate from the existing persistent ETL seed path because the normal seed bundle builds `vote_interpretations`. This milestone does not enable a production import.

## Parser Changes

`backend/app/etl/senate_xml_adapter.py` now maps:

- `H.J.Res.` / `H J RES` to `hjres`;
- `H.Con.Res.` / `H CON RES` to `hconres`.

Guardrails retained:

- PN nominations remain unsupported.
- Senate amendments remain unsupported.
- Unsupported references continue to fail/skip explicitly rather than being guessed.

## Dry-Run Command

Dry-run command used from `backend/`:

```powershell
.\.venv_win\Scripts\python.exe -m app.etl.senate_fact_import --manifest ..\docs\review_packets\senate_vote_facts_expansion_manifest_phase_11.json --dry-run --production-read-only --skip-existing
```

The command:

- requires an explicit manifest path;
- supports production read-only validation;
- sets `default_transaction_read_only = on` for production validation queries;
- supports explicit `--skip-existing`;
- reports planned inserts by table;
- reports zero planned `vote_interpretations` writes;
- exits non-zero if unsupported rows, parse failures, member mapping failures, bill mapping failures, existing rows without explicit skip behavior, or target interpretation rows are detected.

## Manifest Used

Manifest:

- `docs/review_packets/senate_vote_facts_expansion_manifest_phase_11.json`

Target roll numbers:

`97, 150, 151, 161, 162, 169, 191, 206, 207, 222, 223, 224, 228, 231, 232, 236, 239, 276, 277, 278, 279, 280, 281`

All target rows are cached Senate XML files, absent from production, and categorized as bill-centered legislative vote facts.

## Dry-Run Results

Production-aware dry-run result:

| Planned operation | Count |
| --- | ---: |
| Bill inserts | 11 |
| Roll-call inserts | 23 |
| `votes_cast` inserts | 2,300 |
| `vote_contexts` inserts | 2,300 |
| `vote_interpretations` inserts | 0 |
| `vote_interpretations` updates | 0 |
| `vote_interpretations` deletes | 0 |
| Skipped existing target roll calls | 0 |
| Unsupported target roll numbers | 0 |
| Parse failures | 0 |
| Member mapping failures | 0 |
| Bill mapping failures | 0 |

Local-only dry-run, without production bill presence lookup, planned 12 bill inserts. Production read-only validation found one target bill key already present, reducing the production-aware planned bill inserts to 11.

## Zero Interpretation Writes

The facts-only dry-run reports:

- `planned_vote_interpretation_inserts = 0`
- `planned_vote_interpretation_updates = 0`
- `planned_vote_interpretation_deletes = 0`

The dry-run module does not call `run_etl_and_persist`, `build_seed_bundle`, or any production write path. It parses XML, compares against optional production read-only state, builds planned fact/context counts, and exits.

## Idempotency Behavior

Expected future import behavior:

- existing production roll calls are skipped only when explicit skip-existing behavior is enabled;
- existing production roll calls without explicit skip-existing behavior cause a fail-closed error;
- target roll calls with any existing `vote_interpretations` rows cause a fail-closed error;
- unsupported manifest categories do not enter the plan;
- missing XML files or parse failures cause a fail-closed error;
- member mapping failures cause a fail-closed error;
- bill mapping failures cause a fail-closed error.

## Rollback Artifact

Rollback planning artifact:

- `docs/review_packets/senate_vote_facts_expansion_rollback_plan_phase_12.sql`

The rollback plan is scoped to the exact 23 manifest roll numbers. It deletes target `vote_contexts`, `votes_cast`, and `roll_calls` rows only when no target `vote_interpretations` rows exist. It deletes target bill rows only when no remaining `roll_calls` rows reference them.

The rollback artifact was not run.

## Risks

- This is a dry-run implementation, not an approved production importer.
- A future production import still needs an explicit write command/mode and approval gate.
- Fact-only rows may increase raw evidence volume if surfaced before source context catches up.
- Motion-to-proceed rows in the target set are vote facts, not substantive support/opposition evidence.
- Senate amendment fact loading remains deferred until amendment identifiers, parent bills, and purposes can be preserved and reviewed.
- PN nominations remain excluded pending separate product/methodology semantics.

## Approval Gate Before Future Production Import

No production import is approved by this packet.

If this batch is approved later, use an explicit bounded approval phrase:

`Approve production import of Phase 12 Senate fact-only batch for roll numbers 97, 150, 151, 161, 162, 169, 191, 206, 207, 222, 223, 224, 228, 231, 232, 236, 239, 276, 277, 278, 279, 280, 281, with no vote_interpretations writes.`

## Final Recommendation

The dry-run path is safe for later import approval review because it is manifest-bounded, production-read-only during validation, and plans zero interpretation writes.

Recommended next step:

1. Review this implementation and dry-run packet.
2. If accepted, create a separate production import milestone that adds or exposes the write path, runs one final preflight, and stops for the exact approval phrase above.
3. Keep PN nominations excluded.
4. Keep Senate amendment fact loading deferred.
5. Fetch the 244 uncached Senate XML roll numbers after this first fact-only path is proven, unless the product priority is broader source inventory before any import.
