# 118th House Amendment Evidence Pre-Write Review

## Status

Pre-write gate passed for the 228-row candidate package. No production write has been performed by this artifact.

## Scope

- Full audit rows: 566
- Exact target rows: 228
- Filtered procedural-signal rows kept limited: 11
- Remaining limited/deferred rows: 338
- Affected officials: 448

## Target Domain Distribution

| Domain | Rows |
| --- | ---: |
| `NATIONAL_SECURITY_FOREIGN` | 105 |
| `ECONOMY_TAXES` | 42 |
| `JUSTICE_PUBLIC_SAFETY` | 37 |
| `ENVIRONMENT_ENERGY` | 15 |
| `INFRASTRUCTURE_TECH_TRANSPORT` | 13 |
| `HEALTH_SOCIAL` | 7 |
| `EDUCATION_WORKFORCE` | 6 |
| `IMMIGRATION_BORDER` | 3 |

## Proposed Effects

- Classification updates: 228 rows to `is_eligible = true`, `eligibility_reason = policy_vote`.
- Interpretation updates: 228 rows to `interpreted`, `support_position = yea`, `oppose_position = nay`.
- Expected support vote instances: 42481.
- Expected opposition vote instances: 53861.
- Not-voting instances excluded: 3510.
- Procedural and limited rows remain non-counting.
- 119th evidence and non-targeted 118th evidence are not in the write set.

## Rollback Paths

- Classifications: `docs/review_packets/118th_house_amendment_classification_rollback.sql`
- Interpretations: `docs/review_packets/118th_house_amendment_interpretation_rollback.sql`
- Derived outputs: `docs/review_packets/118th_house_amendment_precompute_rollback.sql`
