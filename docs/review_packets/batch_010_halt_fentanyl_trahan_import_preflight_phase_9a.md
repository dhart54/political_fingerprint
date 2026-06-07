# Batch 010 Import Preflight - Phase 9A

Date: 2026-06-07

Scope: production import preflight for `batch_010_halt_fentanyl_trahan_amendment_candidate`.

This is preflight only. No production data was written. No import was run. No Supabase rows were modified. No UI, API shape, support/opposition counting logic, or alignment logic changed.

## Why Batch 010 Was Selected First

Batch 010 is the strongest substantive candidate from Phase 8 because it has:

- one exact target row;
- a clear amendment vote;
- a matched Congress.gov amendment record;
- official House Clerk roll-call context;
- unambiguous candidate support/oppose positions;
- no schema-change requirement;
- an existing reviewed Phase 3 source packet pattern for the same H.R. 27 amendment.

This is a better first substantive preflight than a multi-row import because count and alignment impact can be inspected around one `roll_call_id`.

## Batch Scope

Batch file:

- `docs/interpretation_batches/batch_010_halt_fentanyl_trahan_amendment_candidate.json`

Candidate count: one

| Field | Value |
| --- | --- |
| `roll_call_id` | 30 |
| House roll number | 32 |
| Chamber | House |
| Bill | H.R. 27, HALT Fentanyl Act |
| Amendment | Trahan of Massachusetts Part B Amendment No. 2 |
| Issue domain | `JUSTICE_PUBLIC_SAFETY` |
| Facet / measure group | `administrative_law_and_regulatory_procedures` |
| Candidate type | `substantive_interpretation` |
| Recommended status | `interpreted` after review approval |
| `support_position` | `yea` |
| `oppose_position` | `nay` |
| Would count if imported? | Yes |
| Procedural context? | No. This is a substantive amendment-adoption vote candidate. |

Source basis:

- House Clerk Roll 32 question and result
- Congress.gov amendment record `119:hamdt:5` description for H.R. 27
- Congress.gov H.R. 27 bill summary, actions, and amendment list

Source URL:

- `https://clerk.house.gov/evs/2025/roll032.xml`

No stop condition was hit. Candidate type is clear, support/oppose positions are unambiguous, source basis is sufficient for preflight, no schema changes are required, and the import path would target only `vote_interpretations.roll_call_id = 30`.

## Current Production State

Current `vote_interpretations` row for roll_call_id 30:

| Field | Current value |
| --- | --- |
| `interpretation_status` | `ambiguous` |
| `support_position` | `null` |
| `oppose_position` | `null` |
| `interpretation_reason` | Manual review found amendment wording without enough official amendment text to assign yea/nay meaning. |
| `source_url` | `https://clerk.house.gov/evs/2025/roll032.xml` |
| `interpretation_version` | `interpretation_v1` |
| `classification_version` | `v1` |
| `plain_english_summary` | `null` |
| `yea_meaning` | `null` |
| `nay_meaning` | `null` |
| `policy_effect` | `null` |
| `issue_facet` | `administrative_law_and_regulatory_procedures` |
| `confidence` | `null` |
| `source_basis` | `["question", "description", "source_url"]` |
| `uncertainty_note` | The packet identifies an amendment vote, but the cached bill summary describes the underlying bill rather than the exact amendment change. |
| `what_happened` | `null` |
| `why_it_mattered` | `null` |
| `member_vote_context` | `null` |
| `what_not_to_infer` | `null` |
| `reviewed_by` | `codex_manual_source_enrichment` |
| `reviewed_at` | `2026-05-16 21:06:27.680161+00` |

Expected insert/update behavior:

- Existing row? Yes.
- Import behavior if approved later: update one existing `vote_interpretations` row.
- Inserts expected: zero.
- Updates expected: one.
- Existing values overwritten? Yes, for roll_call_id 30 only.
- Rollback artifact restores the previous values above.

Affected production scope:

| Metric | Count |
| --- | ---: |
| Target roll calls | 1 |
| Existing interpretation rows | 1 |
| Affected officials | 432 |
| Affected vote rows | 432 |
| Affected issue sections | 432 |
| Yea rows | 182 |
| Nay rows | 226 |
| Not-voting rows | 24 |
| Present rows | 0 |
| Affected domain | `JUSTICE_PUBLIC_SAFETY` |
| Affected facet | `administrative_law_and_regulatory_procedures` |
| Affected chamber | House only |

Chamber consistency is preserved: the target roll call is a House roll call and all affected vote rows are House votes.

## Before Baselines

Readiness label uses the current issue-readiness rule: no interpreted Yes/No rows means not enough to summarize; fewer than three interpreted Yes/No rows means limited; three or more interpreted Yes/No rows with both support and oppose counts means mixed; otherwise strong.

### Aaron Bean / Justice & Public Safety

| Metric | Before import |
| --- | ---: |
| Total rows | 13 |
| Interpreted substantive rows | 6 |
| Procedural-context rows | 6 |
| Ambiguous/insufficient/limited rows | 7 |
| Not-voting rows | 0 |
| Support count | 6 |
| Oppose count | 0 |
| Readiness label | Strong evidence |
| Target row position | Nay |

Current API alignment for a `support_more_action` Justice preference:

- label: `aligned`
- aligned count: 6
- not-aligned count: 0
- interpreted count: 6
- ambiguous count: 7

Expected impact if batch_010 is imported later:

- support count unchanged at 6;
- oppose count increases from 0 to 1;
- ambiguous/limited rows decrease from 7 to 6;
- readiness label changes from Strong evidence to Mixed but interpretable;
- support-preference alignment label changes from `aligned` to `mixed`.

### Valerie P. Foushee / Justice & Public Safety

| Metric | Before import |
| --- | ---: |
| Total rows | 13 |
| Interpreted substantive rows | 6 |
| Procedural-context rows | 6 |
| Ambiguous/insufficient/limited rows | 7 |
| Not-voting rows | 0 |
| Support count | 2 |
| Oppose count | 4 |
| Readiness label | Mixed but interpretable |
| Target row position | Yea |

Current API alignment for a `support_more_action` Justice preference:

- label: `mixed`
- aligned count: 2
- not-aligned count: 4
- interpreted count: 6
- ambiguous count: 7

Expected impact if batch_010 is imported later:

- support count increases from 2 to 3;
- oppose count remains 4;
- ambiguous/limited rows decrease from 7 to 6;
- readiness label remains Mixed but interpretable;
- support-preference alignment label remains `mixed`.

### Aggregate Affected Population

Before-import readiness distribution across affected Justice/Public Safety issue sections:

| Readiness label | Sections |
| --- | ---: |
| Strong evidence | 243 |
| Mixed but interpretable | 185 |
| Limited evidence | 3 |
| Not enough to summarize | 1 |

Expected distribution if batch_010 is later approved/imported:

| Readiness label | Sections |
| --- | ---: |
| Strong evidence | 22 |
| Mixed but interpretable | 407 |
| Limited evidence | 2 |
| Not enough to summarize | 1 |

Expected aggregate count impact if imported:

| Impact | Delta |
| --- | ---: |
| Support-position rows | +182 |
| Oppose-position rows | +226 |
| Weak ambiguous/insufficient rows | -408 |
| Not-counted not-voting rows | 24 remain not counted |

Because this is a substantive candidate, support/opposition counts and alignment can change if approved and imported. That is expected, but it requires explicit approval after this preflight.

## Expected Product Value

If approved later, this import would:

- convert a high-traffic ambiguous amendment vote into a source-grounded substantive interpretation;
- explain what the Trahan amendment would have done;
- make 408 Yea/Nay vote rows countable across 432 affected officials;
- reduce one weak Justice/Public Safety row per affected official;
- improve transparency by adding `what_happened`, `why_it_mattered`, and `what_not_to_infer`.

It would not:

- change UI code;
- change API shape;
- change support/opposition counting logic;
- change alignment logic;
- affect procedural-context treatment;
- import any row beyond roll_call_id 30.

## Rollback Artifact

Rollback artifact:

- `docs/review_packets/batch_010_halt_fentanyl_trahan_rollback_phase_9a.sql`

Rollback behavior:

- limited to `roll_call_id = 30`;
- restores the existing `ambiguous` row and previous values found during this preflight;
- does not touch any other roll call;
- was not run during preflight.

## Risks

- This is substantive, so import would change support/opposition counts and alignment outputs for affected officials.
- Aaron Bean's Justice/Public Safety support-preference alignment would change from `aligned` to `mixed` because he voted Nay on the amendment.
- The candidate must stay amendment-specific. It must not be collapsed into final passage of H.R. 27 or a broad fentanyl-policy conclusion.
- Production Supabase is the source of truth, so current production state must be re-queried immediately before any later import.
- The importer updates by `roll_call_id`, so exact target-row confirmation is required before import.

## Approval Gate Before Import

Do not import without this exact approval phrase:

`Approve production import of batch_010_halt_fentanyl_trahan_amendment_candidate substantive interpretation rows, with reviewed support_position and oppose_position values and confirmed support/opposition and alignment impact.`

Before running any approved import:

1. Re-run supervised enrichment validation for batch_010.
2. Re-run manual interpretation validation for batch_010.
3. Re-check production state for `roll_call_id = 30`.
4. Confirm the row is still an update, not a changed insert/update scenario.
5. Confirm expected support/opposition and alignment impact.
6. Keep rollback SQL ready, but do not run it unless validation fails or rollback is explicitly requested.
7. Import only `docs/interpretation_batches/batch_010_halt_fentanyl_trahan_amendment_candidate.json`.
8. Run post-import SQL and API-layer validation.

## Final Recommendation

Batch 010 is safe to prepare for a later supervised import. It should be the first substantive production import candidate from Phase 8 because it is a single-row, source-grounded amendment candidate with clear support/oppose positions.

Do not combine it with other substantive batches for the first import. Import only batch_010 if explicit approval is provided, then validate before considering additional batches.

