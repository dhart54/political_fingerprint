# Senate Evidence Classification And Value Enrichment - Phase 20B

Date: 2026-06-12

Scope: deterministic Senate evidence classification, bounded production `vote_classifications` write, API/evidence validation, and review-only candidate interpretation generation after the Phase 19A Senate amendment fact import.

Production changed only in `vote_classifications`. No `vote_interpretations` rows were inserted, updated, or deleted. No support/opposition counting logic, alignment logic, UI behavior, API shape, fact tables, PN nominations, treaty/executive rows, or prior-Congress rows changed.

## Phase 20 Blocker

Phase 20 found that Senate amendment facts were preserved in production but did not appear as issue evidence because the profile evidence path depends on eligible `vote_classifications`.

Key blocker:

- Phase 19A imported 112 fact-only Senate amendment rows.
- Those rows had `senate_amendment_references` and member vote facts.
- They had zero `vote_interpretations`, as intended.
- They also had zero `vote_classifications`, so they were not issue-evidence rows in the current API surface.
- Importing interpretations before classification would either remain invisible or imply issue evidence before the classification layer had approved the row.

## Classification Diagnosis

The existing generic classification path uses roll-call eligibility plus bill committee/title/summary/subjects. It does not inspect `senate_amendment_references.amendment_purpose`, so amendment votes attached to broad parent bills could be missed or misread through parent-bill context.

Phase 20B adds a Senate-specific classification helper:

- `backend/app/etl/senate_evidence_classification.py`

Deterministic rules:

- Senate amendment facts use amendment purpose and amendment identity first.
- Parent bill context is supporting context only.
- Bill-centered Senate rows use bill title, roll question, roll description, summary, and subjects.
- Generic or missing amendment purpose remains deferred.
- Procedural-only bill-centered questions remain deferred.
- No support/oppose positions are inferred.
- No vote interpretation is included.
- No PN nominations, treaty/executive votes, unsupported rows, malformed rows, or prior-Congress/year rows are included.

## Manifest Summary

Manifest:

- `docs/review_packets/senate_evidence_classification_manifest_phase_20b.json`

Final manifest state after production write and version repair:

| Metric | Count |
| --- | ---: |
| Senate roll calls considered | 285 |
| Existing classifications | 96 |
| Eligible Phase 20B rows | 16 |
| Planned inserts in final manifest | 0 |
| Planned updates in final manifest | 16 |
| Deferred without existing classification | 189 |
| Planned vote_interpretations writes | 0 |

Eligible rows by domain:

| Domain | Rows |
| --- | ---: |
| ECONOMY_TAXES | 6 |
| EDUCATION_WORKFORCE | 1 |
| HEALTH_SOCIAL | 8 |
| JUSTICE_PUBLIC_SAFETY | 1 |

Eligible rows by fact type:

| Fact type | Rows |
| --- | ---: |
| senate_amendment_fact | 14 |
| bill_centered | 2 |

Eligible Phase 20B roll_call_ids:

`516, 517, 524, 525, 526, 528, 529, 535, 545, 561, 563, 426, 578, 581, 468, 618`

## Production Classification Write

Production classification write was explicitly approved by the Phase 20B approval gate and ran as a bounded `vote_classifications` write.

Write sequence:

1. Initial bounded write inserted 16 `vote_classifications` rows with the temporary Phase 20B classification version.
2. API validation showed the current profile evidence path reads active classification version `v1`.
3. A bounded repair updated those same 16 rows to `classification_version = 'v1'`.

Actual production classification effects:

| Step | Inserts | Updates | Skips | vote_interpretations writes |
| --- | ---: | ---: | ---: | ---: |
| Initial write | 16 | 0 | 80 | 0 |
| Version repair | 0 | 16 | 80 | 0 |
| Final state | 16 active Phase 20B target rows | 16 target rows on `v1` | 80 preexisting rows unchanged | 0 |

No fact tables were changed by Phase 20B classification.

Rollback:

- `docs/review_packets/senate_evidence_classification_rollback_phase_20b.sql`

The classification rollback is scoped to the exact 16 Phase 20B target roll calls and deletes their `v1` `vote_classifications` rows. It does not touch fact tables, `senate_amendment_references`, or `vote_interpretations`, and it stops if target roll calls have interpretation rows.

## Post-Write Validation

Post-write production validation:

| Check | Result |
| --- | ---: |
| Target classifications visible with active version | 16 |
| Target amendment classifications visible with active version | 14 |
| Target House classifications | 0 |
| Total vote_interpretations | 74 |
| support_position non-null | 48 |
| oppose_position non-null | 48 |

API/evidence validation:

- `HEALTH_SOCIAL` showed 8 Senate amendment evidence rows.
- `ECONOMY_TAXES` showed 10 evidence rows, including 4 amendment rows.
- `JUSTICE_PUBLIC_SAFETY` showed 2 evidence rows, including 1 amendment row.
- `EDUCATION_WORKFORCE` showed 1 amendment evidence row.
- Evidence rows serialized as `senate_amendment_fact`.
- `amendment_reference.counts_as_interpretation` remained `false`.
- Interpretation fields remained null for classification-only rows.

## Rerun Opportunity Map

After Phase 20B classification, the strongest bounded opportunities were:

| Rank | Opportunity | Candidate type | Rows | Why it matters | Risk |
| ---: | --- | --- | ---: | --- | --- |
| 1 | Senate S.Con.Res. 7 health/Medicaid amendment votes | substantive_interpretation | 5 selected from classified health rows | High voter value and clear amendment purposes | Must avoid broad health ideology claims |
| 2 | Senate tax/funding amendment rows | substantive_interpretation | 3 selected from classified economy rows | Makes major budget/amendment activity inspectable | Parent-bill context must not substitute for amendment meaning |
| 3 | Senate education amendment row | substantive_interpretation | 1 selected | Adds issue evidence where Senate coverage is thin | Single-row issue section needs cautious readiness |
| 4 | Senate criminal detention amendment row | substantive_interpretation | 1 selected | Clear practical public-safety amendment purpose | Avoid motive or ideology inference |
| 5 | S.J.Res. 55 CRA procedural floor sequence | procedural_context | 6 | Reduces scroll/value mismatch for procedural rows | Must remain non-counting |

## Candidate Batches

Review-only candidate batches:

| Batch | Substantive | Procedural context | Still insufficient | Import status |
| --- | ---: | ---: | ---: | --- |
| `batch_015_senate_sjres55_procedural_context_candidates` | 0 | 6 | 0 | Review-only procedural context |
| `batch_016_senate_amendment_value_substantive_candidates` | 10 | 0 | 0 | Review-only substantive candidates |

Batch 015:

- File: `docs/interpretation_batches/batch_015_senate_sjres55_procedural_context_candidates.json`
- Covers Senate Rolls 266-271 on S.J.Res. 55.
- Keeps `support_position = null` and `oppose_position = null`.
- Expected support/opposition impact: 0.
- Expected alignment impact: 0.

Batch 016:

- File: `docs/interpretation_batches/batch_016_senate_amendment_value_substantive_candidates.json`
- Covers 10 source-grounded Senate amendment/fact rows.
- roll_call_ids: `524, 526, 535, 545, 561, 563, 578, 581, 468, 618`
- Senate roll numbers: `70, 72, 81, 170, 186, 188, 358, 362, 528, 568`
- Candidate split: 10 substantive, 0 procedural, 0 still insufficient.
- Future support_position recommendation: `yea`
- Future oppose_position recommendation: `nay`
- Future interpretation import did not run.

## Substantive Package Preflight

Batch 016 expected impact if separately approved and imported later:

| Metric | Count |
| --- | ---: |
| Roll calls | 10 |
| Affected senator vote rows | 1,000 |
| Not voting rows | 13 |
| Aggregate support rows if imported | +447 |
| Aggregate oppose rows if imported | +540 |
| Present rows | 0 |
| Existing target vote_interpretations | 0 |

Expected readiness/value impact:

- Adds source-grounded Senate amendment meaning across health, economy, education, and justice issue evidence.
- Turns selected classified amendment facts from visible-but-uninterpreted evidence into reviewable substantive interpretations if later approved.
- Can materially improve Senate profile value because each selected roll affects all senators.
- Readiness impact should be calculated only after import approval, because substantive counting would change.

Expected support/opposition/alignment impact if later approved:

- Support/opposition rows would change because batch 016 is substantive.
- Alignment may change for users with preferences in affected domains.
- This is why batch 016 requires a separate explicit substantive import approval and rollback, not an automatic import.

Future interpretation rollback:

- `docs/review_packets/senate_value_enrichment_rollback_phase_20b.sql`

The interpretation rollback is scoped only to batch 016 target `vote_interpretations` rows and does not touch classifications or fact tables.

## Risks

- Classification makes rows visible as issue evidence, but does not by itself establish support/opposition meaning.
- Senate amendment purpose text can be narrow; summaries must not infer broad ideology or motive.
- The active `v1` classification version is required for current API visibility.
- Batch 016 would change support/opposition and alignment if imported, so it should remain a supervised one-batch approval.
- Procedural batch 015 should remain non-counting if imported later.

## Future Approval Phrase

Required exact approval phrase before importing batch 016:

> Approve production import of batch_016 Senate amendment value substantive interpretations for roll_call_ids 524, 526, 535, 545, 561, 563, 578, 581, 468, and 618, with support_position yea, oppose_position nay, expected support rows +447, expected oppose rows +540, no classification writes, no fact-table writes, and rollback scoped to the batch_016 roll_call_ids.

## Recommendation

Batch 016 is valuable enough for human review and a future import preflight. It should not be imported automatically. The next safe action is a focused batch 016 substantive import approval/preflight, or a broader review pass if the team wants to combine Senate amendment interpretations into a larger supervised package.
