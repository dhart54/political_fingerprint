# Procedural-Context Production Import Preflight - Phase 6

Date: 2026-06-07

Scope: preflight only for the six repeated Justice & Public Safety / `house_of_representatives` procedural rows identified in Phase 5.

No production data was written. No import was run. No Supabase rows were modified. No UI, API shape, support/opposition counting, readiness logic, or alignment logic changed.

## Why This Is the Next Scalable Opportunity

Phase 5 scanned 26,763 production evidence rows and found 4,863 enrichment opportunity sections. The highest-value repeated pattern is a six-row House procedural/floor-rule section tied to Justice & Public Safety. It appears across 434 loaded House officials and 434 Justice/Public Safety issue sections.

These rows can reduce scroll/value mismatch because they explain visible floor-process votes that are currently weak. They are not suitable for ordinary support/opposition interpretation because House rules can bundle multiple bills and do not equal final passage of the underlying measures.

## Storage Feasibility

The six procedural-context candidates can be represented with the existing `vote_interpretations` schema without schema changes.

Recommended storage:

- `interpretation_status`: `insufficient_evidence`
- `support_position`: `null`
- `oppose_position`: `null`
- `plain_english_summary`, `what_happened`, `why_it_mattered`, `what_not_to_infer`: store procedural-context explanation
- `source_basis`: store House Clerk and Congress.gov source basis
- `source_url`: store House Clerk roll-call URL
- `issue_facet`: keep `house_of_representatives`
- `confidence`: `medium`

Why this preserves behavior:

- Current manual import validation allows non-interpreted records to keep `support_position` and `oppose_position` null.
- Current manual import validation allows explanatory text and `source_basis` on non-interpreted records.
- Current manual import persistence can upsert these rows by `roll_call_id`.
- Frontend procedural-context display is derived from non-interpreted row context and does not require a new stored enum.
- Backend support/opposition counts require `interpretation_status = 'interpreted'` and matching support/oppose positions, so these rows remain excluded.
- Backend alignment ignores rows whose `interpretation_status` is not `interpreted`, so these rows remain excluded from alignment.

No stop condition was hit: schema changes are not required, support/oppose can remain null, existing code will not count these rows, alignment is not affected, and the import path can be bounded to the six target `roll_call_id` values.

## Exact Target Rows

All six target `vote_interpretations` rows already exist in production as `insufficient_evidence`, so a later approved import would be six updates, not inserts.

| Roll call ID | House roll | Chamber | Current status | Existing row? | Insert/update behavior | Current support | Current oppose | Source URL |
| ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 145 | 160 | House | `insufficient_evidence` | Yes | Update | `null` | `null` | `https://clerk.house.gov/evs/2025/roll160.xml` |
| 146 | 161 | House | `insufficient_evidence` | Yes | Update | `null` | `null` | `https://clerk.house.gov/evs/2025/roll161.xml` |
| 246 | 267 | House | `insufficient_evidence` | Yes | Update | `null` | `null` | `https://clerk.house.gov/evs/2025/roll267.xml` |
| 247 | 268 | House | `insufficient_evidence` | Yes | Update | `null` | `null` | `https://clerk.house.gov/evs/2025/roll268.xml` |
| 269 | 290 | House | `insufficient_evidence` | Yes | Update | `null` | `null` | `https://clerk.house.gov/evs/2025/roll290.xml` |
| 270 | 291 | House | `insufficient_evidence` | Yes | Update | `null` | `null` | `https://clerk.house.gov/evs/2025/roll291.xml` |

## Production Impact Scope

| Impact metric | Count |
| --- | ---: |
| Target roll calls | 6 |
| Existing `vote_interpretations` rows | 6 |
| Inserts expected | 0 |
| Updates expected | 6 |
| Distinct affected officials | 434 |
| Affected vote rows | 2,593 |
| Affected issue sections | 434 |
| Affected chambers | House only |

Chamber consistency is preserved: all six roll calls are House roll calls, and affected officials are House members only.

## Pre-Import Baselines

### Aaron Bean / Justice & Public Safety

| Metric | Current |
| --- | ---: |
| Total rows | 13 |
| Interpreted substantive rows | 6 |
| Weak ambiguous/insufficient rows | 7 |
| Target procedural-context rows | 6 |
| Not-voting rows | 0 |
| Support count | 6 |
| Oppose count | 0 |
| Readiness label | Mixed but interpretable |
| Alignment impact expectation | None; target rows remain non-interpreted |

Aaron Bean target-row positions:

| Roll call ID | Roll | Position | Current status | Vote type |
| ---: | ---: | --- | --- | --- |
| 145 | 160 | Yea | `insufficient_evidence` | Motion / previous question |
| 146 | 161 | Yea | `insufficient_evidence` | Rule |
| 246 | 267 | Yea | `insufficient_evidence` | Motion / previous question |
| 247 | 268 | Yea | `insufficient_evidence` | Rule |
| 269 | 290 | Yea | `insufficient_evidence` | Concurrence/procedural context |
| 270 | 291 | Yea | `insufficient_evidence` | Concurrence/procedural context |

### Valerie P. Foushee / Justice & Public Safety

| Metric | Current |
| --- | ---: |
| Total rows | 13 |
| Interpreted substantive rows | 6 |
| Weak ambiguous/insufficient rows | 7 |
| Target procedural-context rows | 6 |
| Not-voting rows | 0 |
| Support count | 2 |
| Oppose count | 4 |
| Readiness label | Mixed but interpretable |
| Alignment impact expectation | None; target rows remain non-interpreted |

Valerie Foushee target-row positions:

| Roll call ID | Roll | Position | Current status | Vote type |
| ---: | ---: | --- | --- | --- |
| 145 | 160 | Nay | `insufficient_evidence` | Motion / previous question |
| 146 | 161 | Nay | `insufficient_evidence` | Rule |
| 246 | 267 | Nay | `insufficient_evidence` | Motion / previous question |
| 247 | 268 | Nay | `insufficient_evidence` | Rule |
| 269 | 290 | Nay | `insufficient_evidence` | Concurrence/procedural context |
| 270 | 291 | Nay | `insufficient_evidence` | Concurrence/procedural context |

## Expected Before / After Display Behavior

Before approved import:

- Rows are visible as weak `insufficient_evidence` rows.
- Some UI procedural-context detection can label them from row context, but stored explanatory fields are empty.
- Support/opposition counts and alignment exclude them.

After approved procedural-context import:

- Rows remain `insufficient_evidence`.
- Rows gain procedural-context explanatory text and source basis.
- Rows remain visible as procedural context.
- Rows remain excluded from support/opposition counts.
- Rows remain excluded from alignment.
- Readiness should not promote based on these rows alone.

## Artifacts

Review-only candidate batch:

- `docs/interpretation_batches/batch_004_procedural_context_house_rules_justice.json`

Rollback artifact:

- `docs/review_packets/procedural_context_import_rollback_phase_6.sql`

Rollback scope:

- limited to roll_call_id values `145`, `146`, `246`, `247`, `269`, and `270`
- restores existing values for all six rows
- no rollback SQL was run during preflight

## Risks

- Procedural rows can be overread as direct support/opposition on underlying bills.
- Some House rules bundle multiple issue domains.
- The import path uses `ON CONFLICT (roll_call_id) DO UPDATE`, so review must confirm the six target IDs before import.
- The current storage approach keeps `interpretation_status = insufficient_evidence`; this is intentional for counting safety but means the row is contextual, not a substantive interpreted vote.
- A mistaken future change that counts non-interpreted rows would break the safety boundary, so alignment/counting tests must stay in place.

## Approval Gate

Do not import without this exact approval phrase from the user:

`Approve production import of batch_004 procedural-context House rules rows, with support_position and oppose_position null and no support/opposition or alignment counting changes.`

Before running any approved import, perform:

1. Re-run targeted tests.
2. Re-check current production status for the six `roll_call_id` values.
3. Confirm all six are still `insufficient_evidence` with null support/oppose.
4. Run import only against `docs/interpretation_batches/batch_004_procedural_context_house_rules_justice.json`.
5. Validate after import that support/opposition counts and alignment payloads are unchanged.
6. Keep rollback SQL ready but do not run it unless validation fails.

## Final Recommendation

These six procedural-context rows are safe candidates for a later supervised production import under the approval gate above. They should be the first procedural-context production import because they are bounded, already covered by source context, already represented by existing rows, and affect a repeated 434-official pattern without requiring schema changes.

This branch is ready for PR review as a preflight milestone. It should not proceed into production import unless the exact approval phrase is provided.
