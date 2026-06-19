# 118th Congress Historical Expansion Review Packet

## Summary

The 118th Congress historical load was implemented and written to production with session-aware House and Senate roll-call identity. The production data layer now contains supported 118th Congress facts, vote contexts, deterministic classifications, source-grounded interpretation rows, and recomputed derived outputs alongside the existing 119th Congress data.

The public profile now exposes a voter-friendly scope control with `Full record`, `Recent Congress`, and `Prior Congress` views. The default `Full record` view includes eligible 118th and 119th evidence while preserving Congress attribution in API metadata, evidence rows, and comparison breakdowns.

## Official Source Coverage

Official coverage targets were audited against House Clerk and Senate LIS roll-call indexes, then cached under ignored `backend/data_sources` paths.

| Chamber | Session | Year | Official latest roll | Cached files | Coverage |
| --- | ---: | ---: | ---: | ---: | --- |
| House | 1 | 2023 | 724 | 724 | Complete |
| House | 2 | 2024 | 517 | 517 | Complete |
| Senate | 1 | 2023 | 352 | 352 | Complete |
| Senate | 2 | 2024 | 339 | 339 | Complete |

## Deferred Categories

Unsupported or unsafe vote families were explicitly deferred rather than guessed.

| Chamber | Session | Deferred category | Count |
| --- | ---: | --- | ---: |
| House | 1 | Missing bill reference | 19 |
| Senate | 1 | PN nomination | 231 |
| Senate | 1 | Treaty or executive vote | 2 |
| Senate | 2 | PN nomination | 229 |
| Senate | 2 | Unsupported bill reference | 12 |

Two House 118 session 2 roll calls, rolls 410 and 411, were deferred during import as unsupported/deferred vote types.

## Production Writes

Fact/classification/interpretation write effects matched preflight:

| Table family | Rows added |
| --- | ---: |
| Bills | 531 |
| Legislators | 85 |
| Roll calls | 1,353 |
| Votes cast | 539,935 |
| Vote contexts | 539,935 |
| Vote classifications | 1,353 |
| Vote interpretations | 1,353 |

Derived-output write effects matched preflight for `window_end=2026-06-19`, `classification_version=v1`:

| Table family | Rows inserted or updated |
| --- | ---: |
| Fingerprints | 5,096 |
| Chamber medians | 48 |
| Drift scores | 637 |
| Summaries | 637 |

A bounded follow-up correction updated 430 House 118 session 2 roll 110 vote-context rows from `nomination` to `motion` after the title phrase "Confirmation Act" exposed a false nomination inference. The parser now treats `nomination`, `confirmation:`, and `on the nomination` as nomination signals, while ordinary bill titles containing "Confirmation Act" are not nomination votes.

## Facts Loaded

| Congress | Chamber | Session | Roll calls | Votes cast |
| ---: | --- | ---: | ---: | ---: |
| 118 | House | 1 | 694 | 303,034 |
| 118 | House | 2 | 514 | 222,403 |
| 118 | Senate | 1 | 61 | 6,098 |
| 118 | Senate | 2 | 84 | 8,400 |
| 119 | House | 1 | 339 | 146,772 |
| 119 | House | 2 | 216 | 93,125 |
| 119 | Senate | 1 | 285 | 28,492 |
| 119 | Senate | 2 | 66 | 6,600 |

## Vote Types Preserved

Imported 118th vote-context rows preserve chamber, session, vote type, final result, member position, party context, and not-voting distinctions. Not-voting rows remain excluded from support/opposition semantics.

| Chamber | Session | Vote type | Context rows |
| --- | ---: | --- | ---: |
| House | 1 | amendment | 178,151 |
| House | 1 | appropriations | 3,898 |
| House | 1 | concurrence | 1,302 |
| House | 1 | final_passage | 19,524 |
| House | 1 | motion | 71,531 |
| House | 1 | other | 8,242 |
| House | 1 | rule | 20,386 |
| House | 2 | amendment | 69,823 |
| House | 2 | appropriations | 4,316 |
| House | 2 | concurrence | 864 |
| House | 2 | final_passage | 29,309 |
| House | 2 | motion | 95,658 |
| House | 2 | other | 6,039 |
| House | 2 | rule | 16,394 |
| Senate | 1 | amendment | 700 |
| Senate | 1 | concurrence | 500 |
| Senate | 1 | final_passage | 799 |
| Senate | 1 | motion | 1,799 |
| Senate | 1 | other | 2,300 |
| Senate | 2 | amendment | 1,500 |
| Senate | 2 | concurrence | 400 |
| Senate | 2 | final_passage | 1,000 |
| Senate | 2 | motion | 4,600 |
| Senate | 2 | other | 900 |

## Classification And Interpretation Effects

The 118th deterministic classification write added 1,353 rows. Existing rules safely marked only three 118th roll calls eligible, all in House session 1 during 2023:

| Date | Roll | Domain | Interpretation status |
| --- | ---: | --- | --- |
| 2023-01-09 | 25 | ECONOMY_TAXES | interpreted |
| 2023-11-14 | 646 | EDUCATION_WORKFORCE | insufficient_evidence |
| 2023-11-14 | 647 | EDUCATION_WORKFORCE | interpreted |

All other imported 118th classifications were preserved as low-confidence or procedural/non-counting under existing methodology. No support/opposition, readiness, alignment, or interpretation semantics were changed.

## Idempotency

Post-write fact dry-run returned zero planned inserts for bills, legislators, roll calls, votes cast, vote contexts, vote classifications, and vote interpretations.

Post-write precompute rerun returned zero inserts or updates for fingerprints, chamber medians, drift scores, and summaries for `window_end=2026-06-19`, `classification_version=v1`.

## 119th Congress Invariance

The captured prewrite baseline matched post-write 119th counts:

| Data family | 119th count |
| --- | ---: |
| Votes cast | 274,989 |
| Vote contexts | 274,989 |
| Vote classifications | 757 |
| Interpreted vote interpretations | 129 |
| Ambiguous vote interpretations | 12 |
| Insufficient-evidence vote interpretations | 264 |

Named 119th legislator IDs remained unchanged: Valerie P. Foushee `F000477`, Thom Tillis `T000476`, and Ted Budd `B001305`.

## Scoped Public Profile Validation

FastAPI public profile routes returned 200 for `scope=all`, `scope=119`, and `scope=118`. Selected-scope metadata is included in fingerprint, positions, evidence, and alignment responses.

| Profile | Scope | Eligible evidence | Reviewed Yes/No | Evidence attribution |
| --- | --- | ---: | ---: | --- |
| Valerie P. Foushee | Full record | 124 | 69 | 118th: 3, 119th: 121 |
| Valerie P. Foushee | Recent Congress | 121 | 67 | 119th only |
| Valerie P. Foushee | Prior Congress | 3 | 2 | 118th only |
| Thom Tillis | Full record | 73 | 59 | 119th only |
| Thom Tillis | Recent Congress | 73 | 59 | 119th only |
| Thom Tillis | Prior Congress | 0 | 0 | Empty prior-period treatment |
| Ted Budd | Full record | 73 | 58 | 119th only |
| Ted Budd | Recent Congress | 73 | 58 | 119th only |
| Ted Budd | Prior Congress | 0 | 0 | Empty prior-period treatment |

Representative one-Congress and sparse candidates were identified in production:

| Case | Example | Congresses present | Notes |
| --- | --- | --- | --- |
| 118th only | Blumenauer | 118 | House profile with 3 eligible 118th rows and an empty 119th scope |
| 119th only sparse | Vance (R-OH) | 119 | Existing sparse Senate profile with 1 raw roll call and 0 eligible roll calls |

No tested profile has enough reviewed 118th evidence to support a confident continuity/change statement under the sufficiency rule. The 118th load has only two interpreted eligible votes overall, so the UI correctly says there is not enough reviewed evidence to compare the two Congresses confidently or that evidence is available in only one Congress.

## Scoped API Behavior

- Default profile scope is `all`, labeled `Full record`.
- Supported scope values are `all`, `119`, and `118`.
- `scope=all` includes only the intended available Congresses, 118 and 119.
- `scope=119` preserves the current 119th-only profile view.
- `scope=118` removes accidental rolling-window filtering and returns 118th evidence by Congress.
- Evidence rows retain their original `congress`, `session`, `chamber`, vote type, interpretation, and vote-context fields.
- Position rows include a `congress_breakdown` and cautious `comparison` object for full-record views.
- Comparison status is only confident when both 118th and 119th have at least three reviewed Yes/No vote meanings for the issue.
- No numeric change score was introduced.

## Product Presentation

The frontend profile header now shows a compact secondary scope control:

- `Full record` with `118th + 119th` supporting detail.
- `Recent Congress` with `119th` supporting detail.
- `Prior Congress` with `118th` supporting detail.

Issue summaries distinguish the full-record pattern, recent/prior selected scope, and comparison availability. Conflicting or insufficient periods are surfaced rather than averaged into one conclusion.

## Responsive Validation

Rendered local validation passed against the production-backed API:

- Desktop: scope control, default full-record copy, and profile summary rendered with no horizontal overflow.
- Desktop interactions: switching to `Prior Congress` updated Valerie P. Foushee to 3 eligible 118th rows; switching to `Recent Congress` returned 119th-only evidence.
- Mobile 390px: scope buttons fit as compact controls, profile summary rendered, and horizontal overflow was eliminated.

## Rollback Artifacts

- `docs/review_packets/118th_congress_historical_expansion_rollback.sql`
- `docs/review_packets/118th_congress_historical_expansion_precompute_rollback.sql`
- `docs/review_packets/118th_congress_historical_expansion_prewrite_baseline.json`

## Tests

Targeted backend tests passed:

```text
pytest --basetemp=..\.local\pytest_basetemp tests\test_congress_adapter.py tests\test_current_congress_refresh.py tests\test_historical_congress_refresh.py tests\test_vote_context.py
19 passed
```

Scoped profile tests passed:

```text
pytest --basetemp=..\.local\pytest_basetemp tests\test_api_positions.py tests\test_api_fingerprint.py tests\test_api_alignment.py tests\test_db_read_layer.py
39 passed
```

Frontend unit tests and build passed:

```text
node --test frontend\lib\profileNarrative.test.mjs frontend\lib\issueReadiness.test.mjs frontend\lib\positionEvidenceCounts.test.mjs
12 passed

npm run build
Compiled successfully
```

## Historical Window Recommendation

For the later time-comparison milestone, keep the new full-record profile as the default, with Recent and Prior Congress scopes available as compact controls. Do not silently blend Congresses into one score or evidence list without labels. A good next product shape is:

- Default: full available record, preserving Congress labels and selected-scope metadata.
- Selector: 118th, 119th, and full-record options with chamber/session/source labels on evidence rows.
- Comparison: side-by-side Congress windows once enough interpreted 118th evidence exists.

## Remaining Limitations

- No public profile currently has enough interpreted evidence in both 118th and 119th Congresses to produce a confident continuity/change statement.
- 118th Senate profiles have no eligible interpreted 118th evidence under current deterministic rules.
- PR, merge, and deployment verification remain to be completed after review.
