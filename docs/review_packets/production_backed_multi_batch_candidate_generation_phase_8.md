# Production-Backed Multi-Batch Candidate Generation - Phase 8

Date: 2026-06-07

Scope: production read-only opportunity scan and multi-batch candidate generation using the Phase 7 supervised enrichment operating model.

No production data was written. No import was run. No Supabase rows were modified. No UI, API shape, support/opposition counting, or alignment logic changed.

## Scan Methodology

The scan read production evidence rows with eligible vote classifications and joined:

- loaded officials;
- roll calls;
- member vote positions;
- vote classifications;
- current vote interpretations;
- vote contexts;
- bill metadata.

Weak rows were rows whose current interpretation status was missing, `ambiguous`, or `insufficient_evidence`. Procedural rows were identified from vote type and roll-call language such as previous-question votes, agreeing-to-resolution votes, floor rules, motions, concurrence posture, and related procedural descriptions.

Local Congress.gov cache coverage was checked with `app.etl.source_packets`. Candidate batches were validated with `app.etl.supervised_enrichment`.

Ranking considered:

- affected officials;
- affected vote rows;
- weak/procedural share;
- source availability;
- likely voter value improvement;
- trust risk;
- candidate type;
- likely scroll/value mismatch reduction;
- whether schema changes would be required.

## Top Opportunities Found

| Rank | Opportunity | Domain | Candidate type | Roll calls | Affected officials | Affected vote rows | Current status | Source availability | Value | Risk |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| 1 | H. Res. 953 health floor-rule pair | Health & Social Services | Procedural context | 320, 321 | 433 | 866 | `insufficient_evidence` | Strong House Clerk + Congress.gov rule-resolution cache | High scroll/value reduction | Medium |
| 2 | H. Res. 161 energy/budget floor-rule pair | Environment & Energy | Procedural context | 44, 45 | 433 | 866 | `insufficient_evidence` | Strong House Clerk + Congress.gov rule-resolution cache | High scroll/value reduction | Medium |
| 3 | H. Res. 916 education/small-business floor-rule pair | Education & Workforce | Procedural context | 285, 286 | 432 | 864 | `insufficient_evidence` | Strong House Clerk + Congress.gov rule-resolution cache | High scroll/value reduction | Medium |
| 4 | Trahan amendment to H.R. 27 | Justice & Public Safety | Substantive interpretation | 30 | 432 | 432 | `ambiguous` | Strong House Clerk + matched Congress.gov amendment record | High countable-value improvement | Medium |
| 5 | H.R. 6703 final passage | Health & Social Services | Substantive interpretation | 326 | 433 | 433 | `insufficient_evidence` | Medium House Clerk + Congress.gov bill action/text cache | High countable-value improvement | Medium |

Phase 6 procedural-context rows for roll calls 145, 146, 246, 247, 269, and 270 still appear as `insufficient_evidence` by design, but they already carry procedural-context explanations and were excluded from Phase 8 candidate generation.

## Batches Generated

| Batch | Candidate type split | Roll calls | Affected officials | Affected vote rows | Expected impact if later approved/imported |
| --- | --- | --- | ---: | ---: | --- |
| `batch_010_halt_fentanyl_trahan_amendment_candidate.json` | 1 substantive / 0 procedural / 0 insufficient | 30 | 432 | 432 | Adds one countable amendment interpretation if approved. |
| `batch_011_lower_health_care_premiums_final_passage_candidate.json` | 1 substantive / 0 procedural / 0 insufficient | 326 | 433 | 433 | Adds one countable final-passage interpretation if approved. |
| `batch_012_health_rule_hres953_procedural_context_candidates.json` | 0 substantive / 2 procedural / 0 insufficient | 320, 321 | 433 | 866 | Adds procedural context only; no count/alignment change. |
| `batch_013_education_rule_hres916_procedural_context_candidates.json` | 0 substantive / 2 procedural / 0 insufficient | 285, 286 | 432 | 864 | Adds procedural context only; no count/alignment change. |
| `batch_014_energy_budget_rule_hres161_procedural_context_candidates.json` | 0 substantive / 2 procedural / 0 insufficient | 44, 45 | 433 | 866 | Adds procedural context only; no count/alignment change. |

Total candidates generated:

- substantive interpretation: 2
- procedural context: 6
- still insufficient: 0

Still-insufficient rows were documented as rejected rather than placed into importable candidate batches.

## Candidate Batch Files

- `docs/interpretation_batches/batch_010_halt_fentanyl_trahan_amendment_candidate.json`
- `docs/interpretation_batches/batch_011_lower_health_care_premiums_final_passage_candidate.json`
- `docs/interpretation_batches/batch_012_health_rule_hres953_procedural_context_candidates.json`
- `docs/interpretation_batches/batch_013_education_rule_hres916_procedural_context_candidates.json`
- `docs/interpretation_batches/batch_014_energy_budget_rule_hres161_procedural_context_candidates.json`

## Expected Readiness And Value Impact

Substantive batches:

- may improve support/opposition counts after explicit approval and import;
- may improve issue readiness when they add countable interpreted rows to thin sections;
- require preflight count and alignment impact checks before any production write.

Procedural-context batches:

- reduce scroll/value mismatch by explaining repeated floor-rule rows;
- keep `interpretation_status = insufficient_evidence`;
- keep `support_position = null`;
- keep `oppose_position = null`;
- do not affect support/opposition counts;
- do not affect alignment;
- should not promote readiness on their own.

## Expected Support/Opposition And Alignment Impact

If imported later:

- `batch_010` and `batch_011` would be countable substantive interpretations and could affect support/opposition and alignment for affected officials. They require full count/alignment preflight.
- `batch_012`, `batch_013`, and `batch_014` would be non-counting procedural-context imports. They should not affect support/opposition or alignment if imported with null support/oppose positions and `insufficient_evidence` status.

No batch should be imported directly from this packet.

## Rows Rejected Or Deferred

| Rows | Reason |
| --- | --- |
| 145, 146, 246, 247, 269, 270 | Already imported as procedural-context rows in Phase 6; still non-counting by design. |
| 163 | Appropriations en bloc amendment has cache coverage, but no matched amendment purpose/description was available from the source-packet classifier. Remains still insufficient. |
| 243 | Motion to instruct conferees has source context but needs a more specific conference-instruction review path before any interpretation. |
| 255 | Motion to table a censure/removal resolution is procedurally and institutionally sensitive; not selected as first multi-batch candidate without additional review. |
| 296 | Motion to commit on NDAA-related text needs a separate motion-to-commit treatment before import consideration. |
| 222, 223 | Strong procedural-context opportunity for an NDAA/immigration rule pair, but deferred after three other procedural batches to keep Phase 8 review volume bounded. |
| 381-386 | Senate recess/appeal motions around S.J. Res. 55 explain floor process but offer lower voter value and higher risk of clutter; not import candidates yet. |

## Source Quality Notes

Strong source quality:

- `batch_010`: matched Congress.gov amendment record and House Clerk roll-call source.
- `batch_012`, `batch_013`, `batch_014`: House Clerk roll-call sources plus Congress.gov rule-resolution detail, actions, text versions, committees, and reports where available.

Medium source quality:

- `batch_011`: final-passage roll-call source and Congress.gov bill actions/text metadata are available, but local cache does not include CRS summary text. Candidate language is intentionally limited to passage of the titled measure and Senate receipt.

Not enough source support:

- en bloc appropriations amendments without matched amendment purpose;
- motion-to-commit and conference-instruction rows without a dedicated review model;
- Senate recess motions that do not explain the underlying policy question closely enough.

## Import Priority Ranking

Recommended review order:

1. `batch_010` - highest source quality substantive candidate and already aligned with the Phase 3 H.R. 27 review pattern.
2. `batch_011` - high-value final-passage candidate with medium source depth; review should confirm whether official title/action context is enough.
3. `batch_012` - largest and newest procedural-context health rule pair.
4. `batch_013` - education procedural-context pair.
5. `batch_014` - environment/energy procedural-context pair.

Recommended import order, if approved later:

1. Import one substantive batch first, preferably `batch_010`, after full preflight and rollback artifact.
2. Import one procedural-context batch separately after confirming null support/oppose positions and no alignment/count impact.
3. Do not run multi-batch imports until at least one substantive and one procedural Phase 8 batch have each passed isolated preflight/import/post-validation.

## Approval Gates Before Any Import

Substantive approval phrase:

`Approve production import of [batch_id] substantive interpretation rows, with reviewed support_position and oppose_position values and confirmed support/opposition and alignment impact.`

Procedural-context approval phrase:

`Approve production import of [batch_id] procedural-context rows, with support_position and oppose_position null and no support/opposition or alignment counting changes.`

Before any production write:

1. Re-run supervised enrichment validation for the exact batch file.
2. Re-run manual interpretation validation for the exact batch file.
3. Query current production state for every target `roll_call_id`.
4. Confirm insert/update behavior.
5. Create rollback SQL using current production values.
6. Check support/opposition count impact.
7. Check alignment impact.
8. Confirm no UI/API/counting/alignment code changes are bundled with import.
9. Run the import only after the exact approval phrase is provided.
10. Run post-import SQL and API-layer validation.

## Validation Performed

All generated batches passed:

- Phase 7 supervised enrichment validation;
- existing manual interpretation validation.

The validators confirmed:

- procedural rows are non-counting;
- procedural rows keep null support/oppose positions;
- substantive rows include source basis;
- no still-insufficient row was placed into an import candidate batch;
- no production write path was invoked.

## Risks

- Production Supabase is still the source of truth for discovery, so every import must re-check current state immediately before writing.
- Substantive candidates can affect counts and alignment if imported; they need isolated preflight.
- Procedural rows can be overread as support or opposition on bundled measures; null support/oppose and `what_not_to_infer` are required.
- H.R. 6703 lacks local CRS summary text; candidate language is intentionally narrow.
- Multi-batch import is not advisable yet. Review and import one batch at a time.

## Final Recommendation

Review `batch_010` first. If approved later, it should also be the first import candidate because it has the strongest source basis and the clearest substantive amendment pattern.

Do not import `batch_011` until a reviewer confirms that the final-passage title/action context is sufficient.

Do not import `batch_012`, `batch_013`, or `batch_014` until each has its own procedural-context preflight and rollback artifact.

The next milestone should be import preflight for one selected batch, not a multi-batch production import.

