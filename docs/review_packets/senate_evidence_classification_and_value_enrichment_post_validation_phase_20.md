# Senate Evidence Classification And Value Enrichment Post-Validation - Phase 20

Date: 2026-06-14

Scope: completed Phase 20B deterministic Senate evidence classification and the approved import of `batch_016_senate_amendment_value_substantive_candidates`.

Production changes in this phase:

- `vote_classifications`: 16 bounded Phase 20B classification rows were created or repaired before the interpretation import.
- `vote_interpretations`: 10 approved batch 016 substantive interpretation rows were inserted.

No `bills`, `roll_calls`, `votes_cast`, `vote_contexts`, or `senate_amendment_references` rows changed during the batch 016 interpretation import. No UI, API shape, support/opposition counting logic, or alignment logic changed.

## Phase 20B Classification Result

Phase 20 originally found that Senate amendment facts were stored but not reachable as issue evidence because they had no active `vote_classifications`. Phase 20B added deterministic Senate evidence classification with these boundaries:

- Senate amendment facts are classified from amendment purpose and amendment identity first.
- Parent bill context is supporting context only.
- Bill-centered rows are classified from bill title, roll question, roll description, summary, and subjects.
- Missing or generic amendment purpose remains deferred.
- Classification does not infer `support_position` or `oppose_position`.
- Classification does not create `vote_interpretations`.

Manifest:

- `docs/review_packets/senate_evidence_classification_manifest_phase_20b.json`

Classification rows considered: 285 Senate roll calls.

Eligible Phase 20B classifications:

| Type | Count |
| --- | ---: |
| Senate amendment facts | 14 |
| Bill-centered facts | 2 |
| Total | 16 |

Domains:

| Domain | Count |
| --- | ---: |
| ECONOMY_TAXES | 6 |
| EDUCATION_WORKFORCE | 1 |
| HEALTH_SOCIAL | 8 |
| JUSTICE_PUBLIC_SAFETY | 1 |

Production write sequence:

1. Initial bounded classification write inserted 16 `vote_classifications` rows under the temporary Phase 20B classification version.
2. API validation showed the profile evidence path uses active classification version `v1`.
3. A bounded active-version repair updated those same 16 target rows to `classification_version = 'v1'`.

Final classification validation:

| Check | Result |
| --- | ---: |
| Target classifications visible on active `v1` | 16 |
| Target amendment classifications visible on active `v1` | 14 |
| Target House classifications | 0 |
| Total `vote_interpretations` after classification write | 74 |
| `support_position IS NOT NULL` after classification write | 48 |
| `oppose_position IS NOT NULL` after classification write | 48 |

Classification rollback:

- `docs/review_packets/senate_evidence_classification_rollback_phase_20b.sql`

The rollback deletes the exact Phase 20B target `vote_classifications` rows and stops if those target roll calls have `vote_interpretations`. It does not touch fact tables or `vote_interpretations`.

## Batch 016 Approval

Batch 016 is a mixed substantive interpretation package:

- 9 Senate amendment substantive interpretation rows.
- 1 Senate bill-centered final-passage substantive interpretation row: `roll_call_id = 468`.
- 0 procedural-context rows.
- 10 total substantive rows.

Approval phrase received:

> Approve production import of batch_016 as a mixed Senate substantive interpretation package for roll_call_ids 524, 526, 535, 545, 561, 563, 578, 581, 468, and 618, containing 9 amendment rows and 1 bill-centered final-passage row, with support_position yea, oppose_position nay, expected support rows +447, expected oppose rows +540, no classification writes, no fact-table writes, and rollback scoped to the batch_016 roll_call_ids.

Target roll_call_ids:

`524, 526, 535, 545, 561, 563, 578, 581, 468, 618`

## Final Preflight

Preflight gates passed before import:

| Gate | Result |
| --- | --- |
| Target roll_call_id list matched approval | Passed |
| Composition: 9 amendment / 1 final passage / 0 procedural | Passed |
| Every row was `candidate_type = substantive_interpretation` | Passed |
| Every row was `interpretation_status = interpreted` | Passed |
| Every row used `support_position = yea` and `oppose_position = nay` | Passed |
| Direct official Senate source basis existed for every row | Passed |
| Amendment rows described amendment identity and purpose, not parent-bill final passage | Passed |
| Roll 468 was verified as H.R. 5371 final passage, not an amendment | Passed |
| No motive, ideology, character, corruption, or voting recommendation claims | Passed |
| No existing target `vote_interpretations` rows | Passed |
| Delete-only rollback restores true pre-import state | Passed |
| Expected support rows reproduced | +447 |
| Expected oppose rows reproduced | +540 |
| Expected not-voting rows excluded | 13 |
| Planned classification writes | 0 |
| Planned fact-table writes | 0 |

Pre-import baseline:

| Table/check | Count |
| --- | ---: |
| `vote_interpretations` | 74 |
| `support_position IS NOT NULL` | 48 |
| `oppose_position IS NOT NULL` | 48 |
| `vote_classifications` | 435 |
| `bills` | 267 |
| `roll_calls` | 624 |
| `votes_cast` | 175,264 |
| `vote_contexts` | 175,264 |
| `senate_amendment_references` | 112 |
| House `roll_calls` | 339 |
| House `votes_cast` | 146,772 |
| House `vote_contexts` | 146,772 |

## Import Result

Command mode used:

- `python -m app.etl.manual_interpretations import --input ../docs/interpretation_batches/batch_016_senate_amendment_value_substantive_candidates.json --reviewed-by phase_20_batch_016_approved`

Result:

| Metric | Count |
| --- | ---: |
| Imported rows | 10 |
| Errors | 0 |
| Inserts | 10 |
| Updates | 0 |

The inserts/updates split is inferred from preflight: no target `vote_interpretations` rows existed before import, and all 10 existed after import.

## Post-Import Validation

Post-import counts:

| Table/check | Before | After | Delta |
| --- | ---: | ---: | ---: |
| `vote_interpretations` | 74 | 84 | +10 |
| `support_position IS NOT NULL` | 48 | 58 | +10 |
| `oppose_position IS NOT NULL` | 48 | 58 | +10 |
| `vote_classifications` | 435 | 435 | 0 |
| `bills` | 267 | 267 | 0 |
| `roll_calls` | 624 | 624 | 0 |
| `votes_cast` | 175,264 | 175,264 | 0 |
| `vote_contexts` | 175,264 | 175,264 | 0 |
| `senate_amendment_references` | 112 | 112 | 0 |
| House `roll_calls` | 339 | 339 | 0 |
| House `votes_cast` | 146,772 | 146,772 | 0 |
| House `vote_contexts` | 146,772 | 146,772 | 0 |

Stored target content matched the batch JSON for all checked interpretation fields. No target row was a procedural vote type.

Idempotency validation:

| Check | Result |
| --- | ---: |
| Existing target interpretation rows after import | 10 |
| Additional inserts needed on rerun | 0 |
| Procedural targets imported as substantive | 0 |

## Expected Versus Actual Count Impact

| Impact | Expected | Actual |
| --- | ---: | ---: |
| Support rows from target votes | +447 | +447 |
| Oppose rows from target votes | +540 | +540 |
| Not-voting rows excluded | 13 | 13 |
| Present rows | 0 | 0 |

Impact by affected domain:

| Domain | Support rows | Oppose rows | Not voting excluded |
| --- | ---: | ---: | ---: |
| ECONOMY_TAXES | 54 | 136 | 10 |
| EDUCATION_WORKFORCE | 50 | 50 | 0 |
| HEALTH_SOCIAL | 295 | 302 | 3 |
| JUSTICE_PUBLIC_SAFETY | 48 | 52 | 0 |

## Amendment And Final-Passage Behavior

Amendment rows:

- 9 target rows joined to `senate_amendment_references`.
- Every amendment target kept `fact_status = fact_only_uninterpreted` at the fact layer.
- API evidence serialization returned `evidence_type = senate_amendment_fact`.
- API evidence serialization returned `amendment_reference.counts_as_interpretation = false`.
- Countable meaning came from the approved `vote_interpretations` rows, not from the amendment fact layer.

Bill-centered final-passage row:

- `roll_call_id = 468`
- Senate Roll 528
- `vote_type = final_passage`
- Bill identity: H.R. 5371, "Continuing Appropriations, Agriculture, Legislative Branch, Military Construction and Veterans Affairs, and Extensions Act, 2026"
- API evidence serialization returned `evidence_type = roll_call_vote`.
- `amendment_reference = null`.
- Interpretation summary describes passage of H.R. 5371 and does not describe the row as an amendment.
- `what_not_to_infer` states not to infer support for every specific funding line from the title-level source alone.

## Readiness And Alignment Changes

Affected interpreted roll additions:

| Domain | New interpreted rolls | Amendment rows | Bill-centered rows |
| --- | ---: | ---: | ---: |
| ECONOMY_TAXES | 2 | 1 | 1 |
| EDUCATION_WORKFORCE | 1 | 1 | 0 |
| HEALTH_SOCIAL | 6 | 6 | 0 |
| JUSTICE_PUBLIC_SAFETY | 1 | 1 | 0 |

Aggregate alignment label counts for Senate officials using `support_more_action` preferences:

| Domain | Before | After |
| --- | --- | --- |
| HEALTH_SOCIAL | insufficient_evidence: 102 | mixed: 98; not_aligned: 2; insufficient_evidence: 2 |
| ECONOMY_TAXES | mixed: 97; aligned: 3; insufficient_evidence: 2 | mixed: 100; insufficient_evidence: 2 |
| EDUCATION_WORKFORCE | insufficient_evidence: 102 | aligned: 50; not_aligned: 50; insufficient_evidence: 2 |
| JUSTICE_PUBLIC_SAFETY | aligned: 84; not_aligned: 16; insufficient_evidence: 2 | mixed: 68; aligned: 32; insufficient_evidence: 2 |

Sample Senate API validation for `leg_ted_budd` and `leg_thom_tillis` showed the expected domain effects:

- HEALTH_SOCIAL moved from insufficient evidence to mixed with 6 interpreted target rows.
- EDUCATION_WORKFORCE moved from insufficient evidence to not aligned for both sample senators because both voted Nay on the target amendment while `support_position = yea`.
- JUSTICE_PUBLIC_SAFETY moved from aligned to mixed for both sample senators because the new target row added a Nay where `support_position = yea`.
- ECONOMY_TAXES remained mixed for both sample senators, with target roll_call_ids 468 and 618 visible.

No unexplained House changes were observed.

## Rollback

Interpretation rollback:

- `docs/review_packets/senate_value_enrichment_rollback_phase_20b.sql`

The rollback is scoped only to the 10 batch 016 `roll_call_id` values and deletes target `vote_interpretations`. Because preflight confirmed there were no existing target interpretation rows, this restores the true pre-import interpretation state. It does not touch classifications or fact tables.

## Remaining Risks

- Batch 016 creates substantive interpretation evidence and therefore intentionally changes support/opposition and alignment outputs in the affected Senate domains.
- Amendment rows remain source-grounded to Senate XML purpose text; they should not be summarized as broad ideology or motive.
- Roll 468 is a title-level final-passage interpretation. It should not be used to claim support for every provision in H.R. 5371.
- Future Senate substantive batches should stay bounded and supervised.

## Recommendation

Batch 015 should remain a separate procedural-context import decision. It should not be imported as substantive evidence.

The next larger Senate enrichment package should be another supervised substantive candidate package drawn from the now-classified Senate fact universe, with separate preflight for support/oppose impact, alignment changes, rollback, and API evidence validation.
