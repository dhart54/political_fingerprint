# 118th Evidence Eligibility And Interpretation Expansion Review Packet

## Summary

This milestone promoted a bounded 118th Congress package into eligible evidence:

- 198 reviewed 118th roll calls were updated.
- 77 rows became substantive interpreted issue evidence.
- 121 rows became visible procedural context with null support/opposition.
- 588 amendment rows remain deferred because loaded facts do not provide direct amendment purpose safely enough.
- Not-voting remains excluded from support/opposition.
- 119th source rows, classifications, interpretations, and counts were not modified.

The work also fixed an API read-path bug: explicit `scope=119` now uses 119-only congress-scoped reads instead of the latest rolling precompute window.

## Baseline Before Writes

Loaded 118th roll calls: 1,353.

Reason distribution before changes:

| Reason | Rows |
| --- | ---: |
| house:s1:low_classification_confidence | 545 |
| house:s1:policy_vote | 3 |
| house:s1:procedural_vote | 146 |
| house:s2:low_classification_confidence | 301 |
| house:s2:procedural_vote | 213 |
| senate:s1:low_classification_confidence | 42 |
| senate:s1:procedural_vote | 19 |
| senate:s2:low_classification_confidence | 55 |
| senate:s2:procedural_vote | 29 |

Interpretation status before changes:

| Status | Rows |
| --- | ---: |
| house:s1:insufficient_evidence | 692 |
| house:s1:interpreted | 2 |
| house:s2:insufficient_evidence | 514 |
| senate:s1:insufficient_evidence | 61 |
| senate:s2:insufficient_evidence | 84 |

## Eligibility And Deferral Rules

Rows were eligible only when the direct vote question, measure title, and source fields safely identified the issue domain and vote meaning. Final passage, appropriations, concurrence, and direct CRA passage/override questions were eligible for substantive interpretation when the domain was clear.

Procedural rows were eligible only as non-counting procedural context when they were focused and issue-relevant. They keep `interpretation_status = insufficient_evidence` and null support/opposition.

Rows stayed ineligible or deferred when they lacked a safe issue domain, used broad floor-process questions, had ambiguous civic meaning, had a context mismatch, or were amendments without direct amendment purpose. Parent-measure context was not used to replace narrower amendment meaning.

## Ranked Opportunity Families

| Rank | Group | Rows | Source strength | Trust risk | Decision |
| ---: | --- | ---: | --- | --- | --- |
| 1 | substantive_interpretation:NATIONAL_SECURITY_FOREIGN:final_passage | 10 | Direct passage plus measure title | Low | Counting interpretation |
| 2 | substantive_interpretation:EDUCATION_WORKFORCE:rule | 8 | Direct CRA passage/override question | Low | Counting interpretation |
| 3 | substantive_interpretation:HEALTH_SOCIAL:final_passage | 7 | Direct passage plus measure title | Low | Counting interpretation |
| 4 | substantive_interpretation:ENVIRONMENT_ENERGY:final_passage | 6 | Direct passage plus measure title | Low | Counting interpretation |
| 5 | substantive_interpretation:ECONOMY_TAXES:appropriations | 5 | Direct passage plus appropriations title | Low | Counting interpretation |
| 6 | substantive_interpretation:NATIONAL_SECURITY_FOREIGN:appropriations | 4 | Direct passage plus appropriations title | Low | Counting interpretation |
| 7 | substantive_interpretation:INFRASTRUCTURE_TECH_TRANSPORT:final_passage | 4 | Direct passage plus measure title | Low | Counting interpretation |
| 8 | substantive_interpretation:ECONOMY_TAXES:final_passage | 3 | Direct passage plus measure title | Low | Counting interpretation |
| 9 | substantive_interpretation:ENVIRONMENT_ENERGY:rule | 2 | Direct CRA passage/override question | Low | Counting interpretation |
| 10 | substantive_interpretation:JUSTICE_PUBLIC_SAFETY:appropriations | 2 | Direct passage plus appropriations title | Low | Counting interpretation |

Additional coherent procedural-context families were retained as non-counting context, including national security and foreign affairs motions, economy and tax motions, and education/workforce floor-process rows. They help users understand floor process without changing support/opposition summaries.

## Final Distribution

Final reason distribution:

| Reason | Rows |
| --- | ---: |
| house:s1:low_classification_confidence | 508 |
| house:s1:policy_vote | 36 |
| house:s1:procedural_context | 53 |
| house:s1:procedural_vote | 97 |
| house:s2:low_classification_confidence | 260 |
| house:s2:policy_vote | 41 |
| house:s2:procedural_context | 56 |
| house:s2:procedural_vote | 157 |
| senate:s1:low_classification_confidence | 41 |
| senate:s1:procedural_context | 1 |
| senate:s1:procedural_vote | 19 |
| senate:s2:low_classification_confidence | 44 |
| senate:s2:procedural_context | 11 |
| senate:s2:procedural_vote | 29 |

Opportunity distribution after writes:

| Category | Rows |
| --- | ---: |
| defer_amendment_needs_direct_purpose | 588 |
| defer_broad_or_low_value_procedural | 404 |
| still_insufficient_no_domain_signal | 146 |
| procedural_context | 121 |
| substantive_interpretation | 77 |
| defer_no_safe_issue_domain | 13 |
| defer_context_mismatch | 2 |
| still_insufficient_ambiguous_question | 2 |

Domain distribution for the 198 target rows:

| Domain | Rows |
| --- | ---: |
| NATIONAL_SECURITY_FOREIGN | 67 |
| ECONOMY_TAXES | 36 |
| EDUCATION_WORKFORCE | 21 |
| ENVIRONMENT_ENERGY | 19 |
| HEALTH_SOCIAL | 16 |
| JUSTICE_PUBLIC_SAFETY | 15 |
| IMMIGRATION_BORDER | 12 |
| INFRASTRUCTURE_TECH_TRANSPORT | 12 |

## Production Writes

Rollbacks were generated before writes:

- Classifications: `docs/review_packets/118th_evidence_expansion_classification_rollback.sql`
- Interpretations: `docs/review_packets/118th_evidence_expansion_interpretation_rollback.sql`
- Derived precomputes: `docs/review_packets/118th_evidence_expansion_precompute_rollback.sql`

Write results:

- Classification write updated 198 rows.
- Interpretation write updated 198 rows.
- Post-write validation found 198 target rows, 77 interpreted substantive rows, 121 procedural-context rows, 77 non-null support positions, 77 non-null oppose positions, and 0 non-118 targets.
- Not-voting counted as support/opposition: 0.

The derived precompute write was exercised and proved idempotent. It was then restored from the generated rollback because retaining the recomputed latest rolling rows would have changed 119 public rolling-window outputs. Final retained production changes are limited to 118th classifications and interpretations.

## Idempotency

Reruns after the classification and interpretation writes produced zero additional writes:

- Classification rerun: 0 updates.
- Interpretation rerun: 0 updates.
- Derived precompute rerun before rollback: 0 fingerprint, chamber median, drift score, and summary writes.

## Scope And Profile Validation

Local database-backed API validation on patched code:

| Profile | Scope 118 | Scope 119 | Scope all |
| --- | --- | --- | --- |
| Valerie Foushee | 186 rows, 77 interpreted, sample congress 118 | 121 rows, 70 interpreted, sample congress 119 | 307 rows, 147 interpreted, sample congresses 118/119 |
| Thom Tillis | 12 rows, 0 interpreted, sample congress 118 | 73 rows, 59 interpreted, sample congress 119 | 85 rows, 59 interpreted, sample congresses 118/119 |
| Ted Budd | 12 rows, 0 interpreted, sample congress 118 | 73 rows, 59 interpreted, sample congress 119 | 85 rows, 59 interpreted, sample congresses 118/119 |
| Markwayne Mullin | 12 rows, 0 interpreted, sample congress 118 | 72 rows, 59 interpreted, sample congress 119 | 84 rows, 59 interpreted, sample congresses 118/119 |
| Blumenauer | 186 rows, 77 interpreted, sample congress 118 | 0 rows | 186 rows, 77 interpreted, sample congress 118 |
| J. D. Vance | 12 rows, 0 interpreted, sample congress 118 | 0 rows | 12 rows, 0 interpreted, sample congress 118 |

This confirms `scope=118`, `scope=119`, and `scope=all` are isolated in the patched API.

## Validation Commands

- `pytest --basetemp=..\.local\pytest_118_expansion tests\test_evidence_118_expansion.py tests\test_session2_evidence_expansion.py` -> 15 passed.
- `pytest --basetemp=..\.local\pytest_118_api_scope tests\test_db_read_layer.py tests\test_api_fingerprint.py tests\test_api_positions.py tests\test_api_alignment.py` -> 39 passed.
- `node --test frontend/lib/*.test.mjs` -> 40 passed.
- `npm run build` -> passed.
- Local API `/health` -> `{"status":"ok"}`.
- Local API `/coverage/metadata` -> database source, 392 eligible roll calls.

The broad backend suite was attempted in database and fixture modes. It hit pre-existing live-adapter failures and then a Windows pytest basetemp cleanup `PermissionError`; targeted milestone gates passed.

Public frontend validation: `https://political-fingerprint.vercel.app` returned 200 and rendered the Political Fingerprint page. The local Next.js dev server could not be relaunched after clearing the stale `.next` cache because process launch failed with `spawn EPERM` or did not bind port 3000; this is treated as an environment limitation, not a product blocker, because tests and build passed.

Public backend validation: `https://political-fingerprint.onrender.com/health` returned `{"status":"ok"}`. `https://political-fingerprint.onrender.com/coverage/metadata` reported `data_source = database` and 392 eligible roll calls.

## Continuity And Change

The resulting evidence is materially more useful for Prior Congress and Full Record views, especially for House members with broad 118th voting records. It is not sufficient for broad trustworthy continuity/change statements across Congresses. Senate 118th interpreted evidence remains sparse, many amendments remain deferred, and retained procedural context is intentionally non-counting.
