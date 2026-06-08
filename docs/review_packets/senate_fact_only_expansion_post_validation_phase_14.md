# Senate Fact-Only Cache Expansion And Import Post-Validation - Phase 14

Date: 2026-06-08

Scope: 119th Congress / 2025 Senate fact-only expansion package.

Production data changed only for the approved fact/context load. The import did not create, update, or delete `vote_interpretations`. No UI, API shape, support/opposition counting logic, or alignment logic changed.

## Approval Condition Used

`Approve production import of Phase 14 Senate fact-only package, capped at 75 roll calls and 7,500 votes_cast rows, with no vote_interpretations writes, no support/opposition changes, no alignment changes, no PN nominations, and no Senate amendments.`

## Fetch And Cache Results

Source path:

- official Senate roll-call XML through the existing `fetch_sources.py` URL builder
- local cache under `backend/data_sources/senate_xml/`

Ranges attempted:

- 373-479
- 481-617

Results:

| Fetch/cache category | Count |
| --- | ---: |
| Attempted roll numbers | 244 |
| Newly fetched XML files | 244 |
| Already cached in attempted ranges | 0 |
| Missing/unavailable | 0 |
| Failed fetches | 0 |
| Out-of-scope congress/year detected | 0 |

No prior-Congress roll calls were fetched. No roll calls outside calendar year 2025 were selected for the manifest.

## Classification Summary

Classification was limited to the newly fetched 119th Congress / 2025 Senate XML rows in the attempted ranges.

| Category | Count | Phase 14 treatment |
| --- | ---: | --- |
| Bill-centered legislative vote | 70 | Included in fact-only manifest |
| PN nomination | 138 | Excluded |
| Senate amendment with resolvable parent context | 34 | Excluded and deferred |
| Treaty / executive vote | 2 | Excluded |

Excluded rows remain in the manifest backlog section for audit. Senate amendments and PN nominations were not imported.

## Final Manifest

Manifest:

- `docs/review_packets/senate_fact_only_expansion_manifest_phase_14.json`

Included target roll numbers:

`391, 392, 394, 395, 396, 398, 399, 401, 403, 411, 423, 428, 454, 455, 500, 503, 510, 513, 514, 515, 516, 517, 520, 521, 527, 528, 533, 534, 535, 536, 537, 540, 541, 542, 543, 544, 545, 548, 549, 550, 551, 553, 554, 555, 556, 557, 558, 559, 560, 570, 571, 572, 573, 575, 576, 581, 585, 590, 594, 595, 597, 598, 599, 600, 603, 608, 609, 610, 611, 617`

Manifest gate results:

| Gate | Result |
| --- | --- |
| Roll count <= 75 | Passed: 70 |
| Expected `votes_cast` rows <= 7,500 | Passed: 7,000 |
| All included rows are congress 119 | Passed |
| All included rows are calendar year 2025 | Passed |
| All included rows are Senate | Passed |
| All included rows are bill-centered legislative votes | Passed |
| Interpretations included | None |
| PN nominations included | None |
| Senate amendments included | None |
| Treaty/executive votes included | None |

## Final Production-Aware Preflight

Command run from `backend/`:

```powershell
.\.venv_win\Scripts\python.exe -m app.etl.senate_fact_import --manifest ..\docs\review_packets\senate_fact_only_expansion_manifest_phase_14.json --dry-run --production-read-only --skip-existing
```

Result:

| Planned operation | Count |
| --- | ---: |
| Bill inserts | 21 |
| Roll-call inserts | 70 |
| `votes_cast` inserts | 7,000 |
| `vote_contexts` inserts | 7,000 |
| `vote_interpretations` inserts | 0 |
| `vote_interpretations` updates | 0 |
| `vote_interpretations` deletes | 0 |
| Skipped existing target roll calls | 0 |
| Unsupported target roll numbers | 0 |
| Parse failures | 0 |
| Member mapping failures | 0 |
| Bill mapping failures | 0 |

Before-import production snapshot:

| Check | Count |
| --- | ---: |
| Target `roll_calls` | 0 |
| Target `votes_cast` | 0 |
| Target `vote_contexts` | 0 |
| Target `vote_interpretations` | 0 |
| Total `vote_interpretations` | 74 |
| `vote_interpretations` with `support_position` | 48 |
| `vote_interpretations` with `oppose_position` | 48 |
| House `roll_calls` | 339 |
| House `votes_cast` | 146,772 |
| House `vote_contexts` | 146,772 |

## Import Command And Mode

Command run from `backend/`:

```powershell
.\.venv_win\Scripts\python.exe -m app.etl.senate_fact_import --manifest ..\docs\review_packets\senate_fact_only_expansion_manifest_phase_14.json --write-production --skip-existing --approval-phrase 'Approve production import of Phase 14 Senate fact-only package, capped at 75 roll calls and 7,500 votes_cast rows, with no vote_interpretations writes, no support/opposition changes, no alignment changes, no PN nominations, and no Senate amendments.'
```

Mode:

- production write mode;
- manifest-bounded;
- exact Phase 14 approval phrase required;
- production-aware dry-run re-run inside import before writing;
- explicit `--skip-existing` behavior enabled;
- no `vote_interpretations` write path invoked.

## Actual Import Counts

| Table/action | Count |
| --- | ---: |
| Inserted `bills` | 21 |
| Inserted `roll_calls` | 70 |
| Inserted `votes_cast` | 7,000 |
| Inserted `vote_contexts` | 7,000 |
| Inserted `vote_interpretations` | 0 |
| Updated `vote_interpretations` | 0 |
| Deleted `vote_interpretations` | 0 |
| Skipped existing target roll calls | 0 |

## Post-Import Production Validation

Read-only validation after import:

| Check | Result |
| --- | ---: |
| Target `roll_calls` present | 70 |
| Target `votes_cast` rows present | 7,000 |
| Target `vote_contexts` rows present | 7,000 |
| Target `vote_interpretations` rows present | 0 |
| Total `bills` | 266 |
| Total `roll_calls` | 512 |
| Total `votes_cast` | 164,067 |
| Total `vote_contexts` | 164,067 |
| Total `vote_interpretations` | 74 |
| `vote_interpretations` with `support_position` | 48 |
| `vote_interpretations` with `oppose_position` | 48 |
| House `roll_calls` | 339 |
| House `votes_cast` | 146,772 |
| House `vote_contexts` | 146,772 |

`vote_interpretations` status distribution was unchanged:

| Status | Count |
| --- | ---: |
| `interpreted` | 48 |
| `ambiguous` | 12 |
| `insufficient_evidence` | 14 |

Post-import production-aware dry-run with `--skip-existing` reported all 70 target roll calls as skipped existing rows and planned zero inserts into all tables, including zero `vote_interpretations` inserts, updates, or deletes.

## Counting And Alignment Impact

Support/opposition count inputs did not change:

- total `vote_interpretations` remained 74;
- `support_position` non-null count remained 48;
- `oppose_position` non-null count remained 48;
- target roll calls have zero `vote_interpretations` rows.

Alignment inputs did not change because alignment is computed from stored `vote_interpretations` and explicit user preferences. Since this import wrote no `vote_interpretations`, it did not change alignment.

House rows were unchanged:

- House `roll_calls` remained 339;
- House `votes_cast` remained 146,772;
- House `vote_contexts` remained 146,772.

## Rollback Artifact

Rollback artifact:

- `docs/review_packets/senate_fact_only_expansion_rollback_phase_14.sql`

Rollback scope:

- Phase 14 target Senate roll numbers only;
- deletes target `vote_contexts`, `votes_cast`, and `roll_calls`;
- deletes target `bills` only if no remaining `roll_calls` reference them;
- does not delete or modify `vote_interpretations`;
- includes a guard query that requires manual stop/review if target `vote_interpretations` rows exist.

Rollback was not run.

## Tests And Validation

Commands run:

```powershell
.\.venv_win\Scripts\python.exe -m pytest tests\test_senate_xml_adapter.py::test_load_senate_xml_sample_bundle_normalizes_senate_xml tests\test_senate_xml_adapter.py::test_run_etl_supports_senate_xml_sample_source tests\test_senate_xml_adapter.py::test_build_seed_bundle_supports_senate_xml_sample_source tests\test_senate_xml_adapter.py::test_parse_senate_bill_reference_supports_house_joint_resolution tests\test_senate_xml_adapter.py::test_parse_senate_bill_reference_supports_house_concurrent_resolution tests\test_senate_xml_adapter.py::test_parse_senate_bill_reference_still_rejects_nomination tests\test_senate_fact_import.py
```

Result:

- 12 passed.

Additional validation:

- manifest validation passed;
- CLI help loaded successfully;
- final pre-import production-aware dry-run passed;
- post-import production read-only validation passed;
- post-import production-aware dry-run with `--skip-existing` passed and planned zero additional writes.

## Risks And Follow-Ups

- Production Supabase remains the working production database, so future fact imports should stay manifest-bounded with explicit approval.
- These are vote facts and deterministic vote contexts only; they do not provide substantive issue interpretations.
- Senate PN nominations remain excluded.
- Senate amendment handling remains deferred.
- Treaty/executive rows remain excluded.
- Future interpretation work should remain supervised and source-packet based.
- The remaining current-Congress Senate backlog should be classified with the same hard gates before any further import.

## Stop State

Phase 14 completed the approved 70-roll Senate fact-only import and post-validation. The branch is ready for PR review after `git diff --check` and final git status confirmation.
