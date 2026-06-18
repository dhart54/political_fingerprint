# 2026 Evidence Eligibility And Interpretation Expansion

## Scope

This milestone reviewed the loaded 119th Congress, session 2 / 2026 House and Senate vote facts created by the current-Congress freshness refresh. It did not ingest new roll-call facts, alter support/opposition methodology, alter readiness thresholds, or change alignment logic.

The workflow promoted only rows where the loaded official roll-call question and measure context supported deterministic classification. Amendment rows without purpose/context, broad procedural rows, and context mismatches stayed deferred.

## Baseline Audit

Production had 282 session-2 rows with conservative placeholder classifications.

| Reason | Rows |
|---|---:|
| `house:low_classification_confidence` | 138 |
| `house:procedural_vote` | 78 |
| `senate:procedural_vote` | 42 |
| `senate:low_classification_confidence` | 24 |

Vote-type distribution:

| Chamber / vote type | Rows |
|---|---:|
| `house:motion` | 94 |
| `house:final_passage` | 43 |
| `house:amendment` | 33 |
| `senate:motion` | 56 |
| `house:rule` | 20 |
| `house:other` | 13 |
| `house:appropriations` | 9 |
| `senate:other` | 5 |
| `house:concurrence` | 4 |
| `senate:final_passage` | 4 |
| `senate:concurrence` | 1 |

## Top Opportunity Groups

| Rank | Group | Rows | Decision |
|---:|---|---:|---|
| 1 | Broad procedural motions | 120 | Deferred unless focused and domain-grounded |
| 2 | Amendment votes without purpose/context | 33 | Deferred |
| 3 | Final-passage rows without a safe domain signal | 28 | Deferred |
| 4 | Broad House rules | 17 | Deferred |
| 5 | Environment/energy procedural motions | 6 | Procedural context |
| 6 | National-security substantive resolutions | 6 | Substantive interpretation |
| 7 | Education/workforce procedural motions | 5 | Procedural context |
| 8 | Justice/public-safety procedural motions | 5 | Procedural context |
| 9 | Environment/energy final passage | 5 | Substantive interpretation |
| 10 | Economy procedural motions | 4 | Procedural context |

Additional selected source families included 2026 appropriations votes, war-powers resolutions, homeland-security appropriations, immigration/TPS measures, critical-minerals legislation, and direct final-passage votes with clear issue-domain signals.

## Package Generated

Dry-run selected 64 target rows:

| Candidate type | Rows | Counting behavior |
|---|---:|---|
| Substantive interpretation | 32 | Countable after interpretation, `support_position = yea`, `oppose_position = nay` |
| Procedural context | 32 | Non-counting, `support_position = null`, `oppose_position = null` |

Domain distribution:

| Domain | Rows |
|---|---:|
| `ENVIRONMENT_ENERGY` | 15 |
| `JUSTICE_PUBLIC_SAFETY` | 11 |
| `ECONOMY_TAXES` | 10 |
| `NATIONAL_SECURITY_FOREIGN` | 10 |
| `EDUCATION_WORKFORCE` | 8 |
| `HEALTH_SOCIAL` | 4 |
| `IMMIGRATION_BORDER` | 4 |
| `INFRASTRUCTURE_TECH_TRANSPORT` | 2 |

## Deferred Rows

| Deferred reason | Rows | Why deferred |
|---|---:|---|
| `defer_broad_or_low_value_procedural` | 143 | Too broad, too procedural, or not useful enough as issue evidence |
| `defer_amendment_needs_purpose` | 33 | Amendment identity/purpose was not safely available in loaded facts |
| `still_insufficient_no_domain_signal` | 39 | Source text did not support a single issue-domain assignment |
| `defer_context_mismatch` | 3 | Loaded bill/context fields conflicted with the chamber/question context |

The context-mismatch guard was added after review found House rows with Senate cloture/proceeding titles in the loaded bill context. Those rows were explicitly excluded.

## Production Writes

Rollback was created before writes:

- `docs/review_packets/session2_evidence_expansion_rollback.sql`
- `docs/review_packets/session2_evidence_expansion_precompute_rollback.sql`

Production writes performed:

| Step | Table(s) | Result |
|---|---|---|
| Classification update | `vote_classifications` | 64 updated |
| Interpretation update | `vote_interpretations` | 64 updated |
| Derived refresh | `fingerprints`, `chamber_medians`, `drift_scores`, `summaries` | 2026-06-17 v1 window refreshed |

No fact tables were changed. No new roll calls, votes, vote contexts, bills, legislators, or source facts were inserted.

## Validation

Target post-validation:

- 64 eligible classifications.
- 32 interpreted substantive rows.
- 32 procedural/non-counting rows.
- 32 target rows with non-null support and oppose positions.
- 32 procedural rows retained null support and oppose positions.

Aggregate interpretation counts:

- `vote_interpretations`: 405 total.
- `support_position IS NOT NULL`: 97 before, 129 after.
- `oppose_position IS NOT NULL`: 97 before, 129 after.
- Net support/oppose interpretation rows: +32 / +32.

Vote-row impact across the 32 substantive target rolls:

- Support vote rows: 7,769.
- Oppose vote rows: 5,734.
- Not-voting rows: 745, excluded from support/opposition meaning.

Derived refresh result:

- `fingerprints`: 4,280 updated/inserted.
- `chamber_medians`: 42 updated/inserted.
- `drift_scores`: 535 updated/inserted.
- `summaries`: 535 updated/inserted.

Idempotency:

- Classification rerun: 0 updates.
- Interpretation rerun: 0 updates.
- Precompute rerun: 0 updates/inserts.

## Representative Profile Checks

Local production-backed API using the current code returns the refreshed `2026-06-17` window.

Valerie Foushee:

- Economy & Taxes: 19 total, 12 interpreted; support 0, oppose 11, other 1.
- National Security & Foreign Policy: 31 total, 26 interpreted; support 8, oppose 18.
- Justice & Public Safety: 24 total, 11 interpreted; support 2, oppose 9.

Thom Tillis:

- Economy & Taxes: 39 total, 34 interpreted.
- Health & Social Policy: 18 total, 16 interpreted.
- National Security & Foreign Policy: 6 total, 5 interpreted.

Ted Budd:

- Economy & Taxes: 39 total, 34 interpreted.
- Health & Social Policy: 18 total, 16 interpreted.
- National Security & Foreign Policy: 6 total, 5 interpreted.

Adam Schiff:

- Economy & Taxes: 39 total, 34 interpreted.
- National Security & Foreign Policy: 6 total, 5 interpreted.
- Infrastructure/Tech/Transport: 7 total, 1 interpreted.

Sparse profile `leg_grijalva`:

- 5 total eligible rows.
- 2 interpreted rows.
- Remains limited/sparse and inspectable without overstating the evidence.

## Public Deployment Status

After production writes, the public Render API still returned the older `2026-03-12` window during pre-PR verification. Production data and local production-backed API returned `2026-06-17`.

This indicates the public deployment needs normal post-merge backend deployment verification. The branch includes backend code changes, so Render should be verified after merge before marking the public refresh complete.

## Guardrails

- No support/opposition methodology change.
- No readiness-threshold change.
- No alignment-logic change.
- No amendment interpretation without amendment purpose.
- Procedural context remains non-counting.
- Not-voting remains excluded.
- Cross-chamber context mismatches are deferred.
- No fact ingestion was performed in this milestone.

## Tests

- `backend/tests/test_session2_evidence_expansion.py`: 7 passed.

Additional final targeted tests, build checks, and deployment checks are required before PR merge.

## Next Recommendation

After this PR is merged and deployed, verify that the public Render API and Vercel frontend serve the refreshed `2026-06-17` window. The next product milestone should address the deferred amendment-purpose backlog or improve official source enrichment for rows with no safe domain signal.
