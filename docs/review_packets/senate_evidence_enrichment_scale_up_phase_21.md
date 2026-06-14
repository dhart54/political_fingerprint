# Senate Evidence Enrichment Scale-Up - Phase 21

Date: 2026-06-14

Scope: source-grounded scale-up of 119th Congress / 2025 Senate evidence across the strongest remaining loaded families. This milestone reused the established classification, rollback, supervised candidate, import, and validation guardrails from Phases 7-20.

Production writes performed:

- `vote_classifications`: 40 inserts, 0 updates.
- `vote_interpretations`: 39 substantive inserts, 6 procedural-context updates.

No `bills`, `roll_calls`, `votes_cast`, `vote_contexts`, `senate_amendment_references`, House fact rows, UI/API shape, support/opposition counting logic, or alignment logic changed.

## Baseline

Confirmed production baseline before Phase 21 writes:

| Metric | Count |
| --- | ---: |
| Senate roll calls | 285 |
| Senate votes_cast rows | 28,492 |
| Senate vote_contexts rows | 28,492 |
| Senate amendment references | 112 |
| Senate vote_classifications | 96 |
| Senate vote_interpretations | 26 |
| Senate interpreted rows | 20 |
| Senate ambiguous/procedural rows | 6 |
| Senate support_position non-null | 20 |
| Senate oppose_position non-null | 20 |

Priority families processed:

| Family | Loaded roll calls | Classified before | Interpreted before | Amendment refs |
| --- | ---: | ---: | ---: | ---: |
| H.R. 1 | 43 | 23 | 2 | 22 |
| S.Con.Res. 7 | 25 | 8 | 3 | 25 |
| H.Con.Res. 14 | 23 | 4 | 3 | 21 |
| H.R. 5371 | 23 | 2 | 2 | 5 |
| S.J.Res. 55 | 12 | 12 | 7 | 0 |

## Source Results

Source grounding came from stored official Senate XML facts, `senate_amendment_references`, production bill records, and the existing batch 015 procedural-context packet.

For amendment rows:

- amendment number and amendment purpose were required;
- generic purposes such as "In the nature of a substitute" and "To improve the bill" were deferred;
- amendment-related procedural motions were not written as ordinary substantive classifications;
- parent bill context was supporting context only.

For final-passage rows:

- direct final-passage roll question and bill identity were required;
- summaries were limited to final passage and did not imply support for every provision.

For procedural rows:

- S.J.Res. 55 floor-process rows were kept as procedural context with null support and oppose positions.

## Classification Expansion

Manifest:

- `docs/review_packets/senate_enrichment_classification_manifest_phase_21.json`

Rollback generated before write:

- `docs/review_packets/senate_enrichment_classification_rollback_phase_21.sql`

Classification dry-run:

| Metric | Count |
| --- | ---: |
| Considered priority-family roll calls | 126 |
| Planned inserts | 40 |
| Planned updates | 0 |
| Existing/skipped rows | 49 |
| Deferred rows | 37 |
| Planned vote_interpretations writes | 0 |

Classification rows written:

| Domain | New classifications |
| --- | ---: |
| ECONOMY_TAXES | 29 |
| HEALTH_SOCIAL | 10 |
| NATIONAL_SECURITY_FOREIGN | 1 |

Facet split:

| Facet | New classifications |
| --- | ---: |
| budget_and_debt | 26 |
| medicaid_and_medicare | 4 |
| nutrition_and_food_assistance | 3 |
| prescription_drugs_and_medicare_benefits | 1 |
| reproductive_and_family_health | 1 |
| tax_policy | 3 |
| ukraine_and_foreign_security | 1 |
| veterans_health_and_benefits | 1 |

Post-classification validation:

- 40 target classifications existed with active `classification_version = v1`.
- `vote_interpretations` remained 84 after classification write.
- support_position non-null remained 58 after classification write.
- oppose_position non-null remained 58 after classification write.
- House roll calls remained 339.
- Rebuilt classification manifest after write planned 0 additional classification writes.
- After interpretation imports, the classification dry-run correctly fails closed if run against the original pre-write manifest because 39 classification target rows now have approved `vote_interpretations`. If rollback is ever needed, run the interpretation rollback first, then the classification rollback.

## Substantive Package

Batch:

- `docs/interpretation_batches/batch_017_senate_substantive_enrichment_candidates.json`

Final validated package:

| Metric | Count |
| --- | ---: |
| Substantive candidates | 39 |
| Procedural-context candidates | 0 |
| Still-insufficient candidates | 0 |
| Planned inserts before import | 39 |
| Planned updates before import | 0 |
| Not-voting rows excluded | 19 |
| Expected support-row impact | +1,828 |
| Expected oppose-row impact | +2,053 |

The package contains amendment and final-passage interpretations only. Procedural motions, concurrence rows, administrative-rule process rows, generic substitute amendments, and insufficient source rows were excluded.

One initially generated H.R. 1 final-passage row, `roll_call_id = 417`, was removed after post-import validation found that its existing `vote_classifications` row was ineligible (`low_classification_confidence`). The newly inserted interpretation for 417 was deleted, the generator was tightened to exclude existing ineligible classifications, and the final batch was regenerated at 39 valid rows.

## Procedural Package

Batch:

- `docs/interpretation_batches/batch_018_senate_procedural_context_candidates.json`

The package carries forward the six S.J.Res. 55 floor-process rows. The current procedural-context wording is from the Phase 21 batch 018 review packet; the rollback uses the recoverable pre-Phase-21 product state from `docs/interpretation_batches/batch_007_thom_infra_interpretations.json`.

| Metric | Count |
| --- | ---: |
| Procedural-context candidates | 6 |
| Substantive candidates | 0 |
| Still-insufficient candidates | 0 |
| Inserts | 0 |
| Updates | 6 |
| support_position | null for all rows |
| oppose_position | null for all rows |

Procedural-context rows explain the floor procedure and remain non-counting.

Rollback source and metadata limitation:

- Prior product content source: `docs/interpretation_batches/batch_007_thom_infra_interpretations.json`.
- Prior reviewer convention: `reviewed_by = codex_manual_review`, supported by untouched sibling row `390` from the same prior batch.
- Phase 21 overwrote the exact prior `reviewed_at` / `updated_at` values for roll_call_ids `381-386`.
- Those exact timestamps are no longer recoverable from current production.
- The rollback restores known prior product content and the strongly supported prior reviewer identity, but it does not fabricate exact historical timestamps.
- This is an audit-metadata limitation only. It does not affect substantive interpretation content, support/opposition counting, alignment, readiness, or procedural non-counting behavior.

## Interpretation Preflight And Rollback

Rollback generated before interpretation imports:

- `docs/review_packets/senate_enrichment_interpretation_rollback_phase_21.sql`

Final rollback scope:

- Deletes the 39 newly inserted batch 017 substantive interpretation rows.
- Restores known prior product-facing values for the 6 batch 018 procedural-context updates using batch 007 as the source.
- Restores procedural `reviewed_by` to `codex_manual_review`.
- Does not claim byte-for-byte restoration of exact prior `reviewed_at` / `updated_at` values for roll_call_ids `381-386`; those timestamps were overwritten and are not recoverable.
- Does not touch `vote_classifications` or fact tables.

Final post-correction preflight/idempotency:

| Package | Target rows | Existing rows | Additional inserts needed after import | Content matches |
| --- | ---: | ---: | ---: | --- |
| batch 017 substantive | 39 | 39 | 0 | yes |
| batch 018 procedural | 6 | 6 | 0 | yes |

## Import Results

Substantive import:

- imported_count: 39 final rows
- inserts: 39
- updates: 0
- errors: []

Procedural-context import:

- imported_count: 6
- inserts: 0
- updates: 6
- errors: []
- support_position and oppose_position remained null for all six rows.
- No support/opposition or alignment impact was introduced by these procedural-context updates.

Corrective action:

- Removed one initially inserted interpretation for `roll_call_id = 417` after validation found the row was not eligible issue evidence.
- Final production state and final artifacts exclude 417.
- The final substantive rollback is scoped only to the 39 preserved inserted interpretations.
- The procedural rollback is scoped only to roll_call_ids `381-386` and restores batch-007 product fields plus `reviewed_by = codex_manual_review`; exact prior timestamps are not fabricated.

## Expected Versus Actual Effects

Final substantive package:

| Impact | Expected | Actual |
| --- | ---: | ---: |
| Support rows | +1,828 | +1,828 |
| Oppose rows | +2,053 | +2,053 |
| Not-voting rows excluded | 19 | 19 |

Procedural package:

| Impact | Expected | Actual |
| --- | ---: | ---: |
| Support rows | 0 | 0 |
| Oppose rows | 0 | 0 |
| support_position non-null changes | 0 | 0 |
| oppose_position non-null changes | 0 | 0 |

Post-import production totals:

| Metric | Count |
| --- | ---: |
| Total vote_interpretations | 123 |
| Senate vote_interpretations | 65 |
| support_position non-null | 97 |
| oppose_position non-null | 97 |
| Total vote_classifications | 475 |
| Senate vote_classifications | 136 |
| bills | 267 |
| roll_calls | 624 |
| votes_cast | 175,264 |
| vote_contexts | 175,264 |
| senate_amendment_references | 112 |
| House roll_calls | 339 |
| House votes_cast | 146,772 |
| House vote_contexts | 146,772 |

## Readiness And Alignment

Senate interpreted evidence after Phase 21:

| Domain | Substantive interpreted rolls | Procedural-context rolls | Total |
| --- | ---: | ---: | ---: |
| ECONOMY_TAXES | 34 | 0 | 34 |
| EDUCATION_WORKFORCE | 1 | 0 | 1 |
| HEALTH_SOCIAL | 16 | 0 | 16 |
| INFRASTRUCTURE_TECH_TRANSPORT | 1 | 6 | 7 |
| JUSTICE_PUBLIC_SAFETY | 2 | 0 | 2 |
| NATIONAL_SECURITY_FOREIGN | 5 | 0 | 5 |

Alignment label distribution for Senate officials using `support_more_action` preferences:

| Domain | Label distribution |
| --- | --- |
| ECONOMY_TAXES | mixed: 100; insufficient_evidence: 2 |
| HEALTH_SOCIAL | mixed: 100; insufficient_evidence: 2 |
| EDUCATION_WORKFORCE | aligned: 50; not_aligned: 50; insufficient_evidence: 2 |
| ENVIRONMENT_ENERGY | insufficient_evidence: 102 |
| NATIONAL_SECURITY_FOREIGN | mixed: 31; not_aligned: 53; aligned: 16; insufficient_evidence: 2 |
| INFRASTRUCTURE_TECH_TRANSPORT | not_aligned: 46; aligned: 51; insufficient_evidence: 5 |

Observed alignment changes were limited to affected Senate domains. No House fact or interpretation counts changed.

## Serialization And Not-Voting

Validation confirmed:

- Senate amendment rows retain amendment identity and source purpose.
- Amendment rows serialize as amendment evidence through the existing API path.
- Final-passage rows describe final passage and do not claim support for every provision.
- Procedural rows remain non-counting with null support and oppose positions.
- Not-voting rows are excluded from support/oppose impact.
- No procedural row was imported as substantive.

## Final Validation

Final validation commands/results:

| Check | Result |
| --- | --- |
| Phase 21 batch 017 validator | 39 candidates, valid |
| Phase 21 batch 018 validator | 6 candidates, valid |
| Supervised validator, batch 017 | 39 substantive, 0 errors, 0 warnings |
| Supervised validator, batch 018 | 6 procedural-context, 0 errors, 0 warnings |
| Approval checklist, batch 017 | passed |
| Approval checklist, batch 018 | passed |
| Manual interpretation validator | batch 017: 39 valid; batch 018: 6 valid |
| Manifest validation | 126 considered, valid |
| Production content match | 45/45 target rows matched batch artifacts exactly |
| Support/oppose/not-voting reconciliation | +1,828 support; +2,053 oppose; 19 not-voting excluded |
| Procedural-context production state | 6/6 ambiguous with null support and oppose positions |
| Classification state | 40/40 target rows active `v1`, eligible, and domain-assigned |
| Rollback artifact scope | 39 substantive deletes; 6 procedural product-field restores; 40 classification deletes |
| Post-import idempotency | 0 additional interpretation inserts needed; content matches |
| Fact-table validation | no `bills`, `roll_calls`, `votes_cast`, `vote_contexts`, or `senate_amendment_references` changes during interpretation import |
| House validation | House roll calls, votes_cast, and vote_contexts unchanged |
| Targeted no-temp pytest subset | 20 passed, 1 deselected |
| Full targeted pytest attempt | test bodies reached 20 passed and 1 temp-fixture setup error, then hit known Windows pytest temp cleanup `PermissionError` |
| `git diff --check` | passed with normal Windows CRLF notice |

The deselected/blocked test was the temp-fixture-backed manual import persistence test. The observed failure mode was the known local Windows pytest temp PermissionError and does not indicate a Phase 21 product correctness failure.

## Rejected And Deferred Rows

Rows were deferred or rejected for:

- generic amendment purpose (`In the nature of a substitute`, `To improve the bill`);
- amendment-related procedural motions;
- administrative-rule/floor-process language unsuitable for substantive interpretation;
- existing ineligible classification (`roll_call_id = 417`);
- already interpreted rows from prior phases;
- rows outside the priority families.

## Risks

- Production Supabase remains the working database.
- The substantive package intentionally changes support/opposition and alignment outcomes in affected Senate domains.
- Budget-resolution amendments are source-grounded but can be narrow; summaries must remain amendment-specific.
- Future batches should continue excluding procedural motions from substantive evidence.

## Next Recommendation

Run a focused Senate enrichment cleanup/review milestone for the remaining deferred rows, separating:

- procedural-context rows that can reduce scroll/value mismatch;
- source-grounded final-passage rows with eligible classifications;
- still-insufficient generic amendment rows;
- future source expansion for families outside the Phase 21 priority set.
