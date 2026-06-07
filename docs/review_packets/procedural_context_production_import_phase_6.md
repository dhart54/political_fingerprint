# Procedural-Context Production Import - Phase 6

Date: 2026-06-07

Scope: production import of `batch_004_procedural_context_house_rules_justice` after explicit approval.

Approval phrase received:

`Approve production import of batch_004 procedural-context House rules rows, with support_position and oppose_position null and no support/opposition or alignment counting changes.`

## Imported Batch

Batch file:

- `docs/interpretation_batches/batch_004_procedural_context_house_rules_justice.json`

Import command:

```powershell
cd backend
.\.venv_win\Scripts\python.exe -m app.etl.manual_interpretations import --input ..\docs\interpretation_batches\batch_004_procedural_context_house_rules_justice.json --reviewed-by codex_procedural_context_phase6
```

Import result:

```json
{
  "errors": [],
  "imported_count": 6
}
```

## Rows Updated

All six target rows already existed in production as `insufficient_evidence`, so the import updated existing `vote_interpretations` rows and did not insert new roll-call interpretation rows.

| Roll call ID | House roll | Status after import | Support position | Oppose position | Reviewed by |
| ---: | ---: | --- | --- | --- | --- |
| 145 | 160 | `insufficient_evidence` | `null` | `null` | `codex_procedural_context_phase6` |
| 146 | 161 | `insufficient_evidence` | `null` | `null` | `codex_procedural_context_phase6` |
| 246 | 267 | `insufficient_evidence` | `null` | `null` | `codex_procedural_context_phase6` |
| 247 | 268 | `insufficient_evidence` | `null` | `null` | `codex_procedural_context_phase6` |
| 269 | 290 | `insufficient_evidence` | `null` | `null` | `codex_procedural_context_phase6` |
| 270 | 291 | `insufficient_evidence` | `null` | `null` | `codex_procedural_context_phase6` |

## Validation

Production validation after import confirmed:

- `interpretation_status` remained `insufficient_evidence` for all six target rows.
- `support_position` remained `null` for all six target rows.
- `oppose_position` remained `null` for all six target rows.
- Procedural explanatory fields and source basis were populated.
- No support/opposition counting changes occurred.
- No alignment-counting changes occurred.

Affected target-row aggregate after import:

| Metric | Count |
| --- | ---: |
| Target vote rows | 2,593 |
| Support count | 0 |
| Oppose count | 0 |
| Interpreted rows | 0 |
| Weak rows | 2,593 |

Representative spot checks after import:

| Representative | Issue section | Label | Interpreted rows | Weak/ambiguous rows | Support/aligned count | Oppose/not-aligned count |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Aaron Bean | Justice & Public Safety | `aligned` for support preference | 6 | 7 | 6 | 0 |
| Valerie P. Foushee | Justice & Public Safety | `mixed` for support preference | 6 | 7 | 2 | 4 |

These spot checks match the pre-import baseline. The six imported procedural-context rows remained visible context only and did not become support/opposition or alignment evidence.

## Tests

Pre-import targeted tests:

- `node --test frontend\lib\proceduralContext.test.mjs frontend\lib\issueOverview.test.mjs frontend\lib\issueReadiness.test.mjs frontend\lib\evidenceGrouping.test.mjs` - 23 passed
- `backend\.venv_win\Scripts\python.exe -m pytest backend\tests\test_api_alignment.py backend\tests\test_source_packets.py backend\tests\test_manual_interpretations.py -k "not import_manual_interpretations_validates_before_persisting"` - 18 passed, 1 deselected

Post-import validation:

- Production SQL validation confirmed the six rows remained non-counting procedural-context rows.
- API-layer alignment spot checks confirmed Aaron Bean and Valerie P. Foushee Justice/Public Safety alignment outputs were unchanged in interpreted and weak-row counts.

## Rollback

Rollback artifact:

- `docs/review_packets/procedural_context_import_rollback_phase_6.sql`

Rollback SQL was not run because post-import validation passed.

## Product Boundary

This import changed production `vote_interpretations` explanatory fields for six procedural-context House rules rows only.

It did not:

- Import substantive support/opposition interpretations.
- Set `support_position` or `oppose_position`.
- Change API shape.
- Change UI code.
- Change support/opposition counting logic.
- Change alignment logic.
- Promote procedural rows into ordinary interpreted Yes/No rows.

