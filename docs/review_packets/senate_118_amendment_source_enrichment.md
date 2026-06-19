# 118th Senate Amendment Source Enrichment Review Packet

## Summary

This milestone enriched the loaded 118th Senate amendment subset using direct amendment identity and purpose from official Senate XML plus Congress.gov amendment records.

- Audited the full 588-row deferred amendment bucket from the prior 118th evidence pass.
- Reconciled that bucket as 566 House amendment roll calls and 22 Senate amendment roll calls.
- Built source packets for all 22 loaded 118th Senate amendment roll calls.
- Fetched and cached official Congress.gov amendment records for parsed S.Amdt. numbers.
- Promoted 7 Senate amendment rows: 4 substantive interpreted rows and 3 procedural-context rows.
- Kept 15 loaded Senate amendment rows deferred.
- Preserved all 119th source rows, IDs, classifications, interpretations, and public scope isolation.

## Deferred Amendment Audit

Exact prior deferred-amendment distribution:

| Bucket | Rows |
| --- | ---: |
| house:s1:amendment | 406 |
| house:s2:amendment | 160 |
| senate:s1:amendment | 7 |
| senate:s2:amendment | 15 |
| Total | 588 |

The milestone request names "588 deferred 118th Senate amendment rows"; production shape shows the 588 bucket is the full 118th amendment roll-call bucket, while the loaded 118th Senate amendment subset is 22 roll calls.

## Source Packet Results

Source packets:

- `docs/review_packets/senate_118_amendment_source_packets.json`

Summary:

| Result | Rows |
| --- | ---: |
| Direct purpose available | 10 |
| Direct purpose missing or generic | 12 |
| Promoted substantive interpretation | 4 |
| Promoted procedural context | 3 |
| Deferred despite direct purpose, no safe issue domain | 3 |
| Deferred missing/generic purpose | 12 |

Rows promoted:

| Roll call id | Session | Roll | Amendment | Category | Domain |
| ---: | ---: | ---: | --- | --- | --- |
| 2454 | 1 | 71 | S.Amdt. 11 | substantive_interpretation | HEALTH_SOCIAL |
| 2456 | 1 | 73 | S.Amdt. 9 | substantive_interpretation | NATIONAL_SECURITY_FOREIGN |
| 2457 | 1 | 74 | S.Amdt. 33 | substantive_interpretation | NATIONAL_SECURITY_FOREIGN |
| 2459 | 1 | 76 | S.Amdt. 40 | substantive_interpretation | NATIONAL_SECURITY_FOREIGN |
| 3047 | 2 | 81 | S.Amdt. 1626 | procedural_context | INFRASTRUCTURE_TECH_TRANSPORT |
| 3055 | 2 | 107 | S.Amdt. 1804 | procedural_context | NATIONAL_SECURITY_FOREIGN |
| 3056 | 2 | 108 | S.Amdt. 1781 | procedural_context | EDUCATION_WORKFORCE |

## Top Opportunity Families Before Writes

The source-packet report ranked all coherent families available in the 22-row Senate subset. There were 7 families, not 10, because the loaded Senate subset is small.

| Rank | Family | Rows | Decision | Source strength | Trust risk |
| ---: | --- | ---: | --- | --- | --- |
| 1 | substantive_interpretation:NATIONAL_SECURITY_FOREIGN:amendment | 3 | promote counting interpretation | direct amendment purpose | low |
| 2 | substantive_interpretation:HEALTH_SOCIAL:amendment | 1 | promote counting interpretation | direct amendment purpose | low |
| 3 | procedural_context:EDUCATION_WORKFORCE:amendment | 1 | promote visible non-counting context | direct amendment purpose | medium |
| 4 | procedural_context:INFRASTRUCTURE_TECH_TRANSPORT:amendment | 1 | promote visible non-counting context | direct amendment purpose | medium |
| 5 | procedural_context:NATIONAL_SECURITY_FOREIGN:amendment | 1 | promote visible non-counting context | direct amendment purpose | medium |
| 6 | defer_no_safe_issue_domain:amendment | 3 | defer | direct amendment purpose | low |
| 7 | defer_amendment_purpose_missing_or_generic:amendment | 12 | defer | insufficient direct purpose | high |

## Production Writes

Authorization came from the milestone decision envelope after successful preflight gates.

Rollback generated before writes:

- Classifications: `docs/review_packets/senate_118_amendment_classification_rollback.sql`
- Interpretations: `docs/review_packets/senate_118_amendment_interpretation_rollback.sql`
- Derived outputs: `docs/review_packets/senate_118_amendment_derived_outputs_rollback.sql`

Dry-run before writes:

| Metric | Count |
| --- | ---: |
| Target rows | 7 |
| Classification updates | 7 |
| Interpretation updates | 7 |
| Substantive rows | 4 |
| Procedural-context rows | 3 |
| Deferred rows | 15 |
| Errors | 0 |

Actual writes:

| Table | Inserts | Updates | Deletes |
| --- | ---: | ---: | ---: |
| vote_classifications | 0 | 7 | 0 |
| vote_interpretations | 0 | 7 | 0 |
| bills / roll_calls / votes_cast / vote_contexts | 0 | 0 | 0 |
| derived outputs | 0 | 0 | 0 |

## Post-Write Validation

Post-write validation:

| Metric | Actual |
| --- | ---: |
| Target rows | 7 |
| Non-target rows | 0 |
| Eligible rows | 7 |
| Interpreted rows | 4 |
| support_position non-null | 4 |
| oppose_position non-null | 4 |
| Procedural non-counting rows | 3 |
| Not-voting counted as support/opposition | 0 |

Idempotency rerun:

| Metric | Additional writes |
| --- | ---: |
| Classification updates | 0 |
| Interpretation updates | 0 |

## Scope And Profile Validation

Local production-backed API validation across enriched domains:

| Profile | Scope 118 | Scope 119 | Scope all |
| --- | --- | --- | --- |
| Thom Tillis | 10 rows, 4 interpreted, 6 procedural context, congress 118 only | 32 rows, 23 interpreted, congress 119 only | 42 rows, congresses 118/119 |
| Ted Budd | 10 rows, 4 interpreted, 6 procedural context, congress 118 only | 32 rows, 23 interpreted, congress 119 only | 42 rows, congresses 118/119 |
| Markwayne Mullin | 10 rows, 4 interpreted, 6 procedural context, congress 118 only | 31 rows, 23 interpreted, congress 119 only | 41 rows, congresses 118/119 |
| J. D. Vance | 10 rows, 4 interpreted, 6 procedural context, congress 118 only | 0 rows | 10 rows, congress 118 only |
| Blumenauer | 113 rows, 40 interpreted, 73 procedural context, congress 118 only | 0 rows | 113 rows, congress 118 only |
| Adelita S. Grijalva | 0 rows | 34 rows, 17 interpreted, congress 119 only | 34 rows, congress 119 only |

Public backend validation:

- `https://political-fingerprint.onrender.com/health` -> 200, `{"status":"ok"}`
- `https://political-fingerprint.onrender.com/coverage/metadata` -> 200, `data_source = database`
- Thom Tillis National Security evidence:
  - `scope=118`: 6 rows, 3 interpreted, congress 118 only
  - `scope=119`: 6 rows, 5 interpreted, congress 119 only
  - `scope=all`: 12 rows, 8 interpreted, congresses 118/119

Public frontend validation:

- `https://political-fingerprint.vercel.app` -> 200 and rendered the Political Fingerprint app shell.

## Validation Commands

- `python -m pytest --basetemp=..\.local\pytest_senate_118_amendment tests\test_senate_118_amendment_enrichment.py tests\test_evidence_118_expansion.py` -> 13 passed.
- `python -m pytest --basetemp=..\.local\pytest_senate_118_api_scope tests\test_api_positions.py tests\test_api_alignment.py tests\test_api_fingerprint.py` -> 33 passed.
- `node --test frontend/lib/*.test.mjs` -> 40 passed.
- `npm run build` -> passed.

## Derived Outputs

No derived-output table writes were performed. The affected explicit profile scopes read the updated classifications and interpretations directly, and public/local validation confirmed the expected profile changes. Retaining a broad rolling precompute recompute would risk changing current 119th public outputs, matching the earlier 118th expansion lesson.

## Continuity And Change

The resulting Senate 118th evidence is now materially more useful for the named Senate profiles in Prior Congress and Full Record views. It is still not sufficient for broad trustworthy continuity/change statements across Congresses. The promoted package is small, and many amendment rows remain deferred for missing/generic purpose or no safe issue-domain match.
