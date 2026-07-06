# Data Inventory / Source Manifest V1

## Summary

Repository/local-accessible data only. Counts are not production coverage unless a future read-only production manifest is generated with credentials.

- Read-only: yes
- Requires production credentials: no
- Fixture roll calls: 14
- Fixture member vote rows: 21
- Local source URL rows inspected: 1291
- Interpretation-like rows inspected: 922
- Warnings emitted: 11

## Source Cache Inventory

### House Clerk XML

| year | path | exists | roll_xml_count |
| --- | --- | --- | --- |
| 2023 | backend/data_sources/house_clerk/2023 | yes | 724 |
| 2024 | backend/data_sources/house_clerk/2024 | yes | 517 |
| 2025 | backend/data_sources/house_clerk/2025 | no | 0 |
| 2026 | backend/data_sources/house_clerk/2026 | yes | 222 |

### Senate XML

| congress_session | path | exists | vote_xml_count | members_xml_exists |
| --- | --- | --- | --- | --- |
| 118_1 | backend/data_sources/senate_xml/118_1 | yes | 352 | yes |
| 118_2 | backend/data_sources/senate_xml/118_2 | yes | 339 | yes |
| 119_1 | backend/data_sources/senate_xml/119_1 | no | 0 | no |
| 119_2 | backend/data_sources/senate_xml/119_2 | yes | 178 | yes |

Loose Senate XML files at `backend/data_sources/senate_xml`: 618

### Congress.gov Local Metadata

| source_type | path | exists | json_count |
| --- | --- | --- | --- |
| amendments | backend/data_sources/congress/amendments | yes | 12 |
| bills | backend/data_sources/congress/bills | yes | 304 |
| bill_actions | backend/data_sources/congress/bill_actions | yes | 96 |
| bill_amendments | backend/data_sources/congress/bill_amendments | yes | 97 |
| bill_committees | backend/data_sources/congress/bill_committees | yes | 25 |
| bill_subjects | backend/data_sources/congress/bill_subjects | yes | 35 |
| bill_summaries | backend/data_sources/congress/bill_summaries | yes | 35 |
| bill_texts | backend/data_sources/congress/bill_texts | yes | 25 |
| members | backend/data_sources/congress/members | yes | 1 |

## Fixture Inventory

| path | extension | record_count |
| --- | --- | --- |
| backend/fixtures/bills.json | .json | 12 |
| backend/fixtures/congress_sample/bills.json | .json | 12 |
| backend/fixtures/congress_sample/members.json | .json | 3 |
| backend/fixtures/congress_sample/roll_calls.json | .json | 12 |
| backend/fixtures/congress_sample/votes.json | .json | 19 |
| backend/fixtures/congress_sample/zip_district_map.json | .json | 2 |
| backend/fixtures/house_clerk_sample/bills.json | .json | 4 |
| backend/fixtures/house_clerk_sample/members.xml | .xml |  |
| backend/fixtures/house_clerk_sample/roll001.xml | .xml |  |
| backend/fixtures/house_clerk_sample/roll002.xml | .xml |  |
| backend/fixtures/house_clerk_sample/roll003.xml | .xml |  |
| backend/fixtures/house_clerk_sample/roll004.xml | .xml |  |
| backend/fixtures/house_clerk_sample/zip_district_map.json | .json | 3 |
| backend/fixtures/legislators.json | .json | 3 |
| backend/fixtures/roll_calls.json | .json | 14 |
| backend/fixtures/senate_xml_sample/bills.json | .json | 4 |
| backend/fixtures/senate_xml_sample/members.xml | .xml |  |
| backend/fixtures/senate_xml_sample/vote_001.xml | .xml |  |
| backend/fixtures/senate_xml_sample/vote_002.xml | .xml |  |
| backend/fixtures/senate_xml_sample/vote_003.xml | .xml |  |
| backend/fixtures/senate_xml_sample/vote_004.xml | .xml |  |
| backend/fixtures/senate_xml_sample/zip_district_map.json | .json | 2 |
| backend/fixtures/vote_subject_tags.json | .json | 12 |
| backend/fixtures/votes_cast.json | .json | 21 |
| backend/fixtures/zip_district_map.json | .json | 2 |

## Legislator Metadata Inventory

### Fixture Legislators

- Total: 3
- By chamber: `{"house": 1, "senate": 2}`
- By party: `{"D": 2, "R": 1}`
- By state: `{"NC": 3}`
- Current/in-office: `{"True": 3}`
- Missing identity fields: `{"bioguide_id": 0, "lis_id": 3, "name_display": 0, "slug": 3}`

### Congress.gov Member Cache

| path | congress | member_count |
| --- | --- | --- |
| backend/data_sources/congress/members/118_members.json | 118 | 554 |

- Total cached member rows: 554
- By chamber: `{"House of Representatives": 444, "Senate": 110}`
- By party: `{"Democratic": 270, "Independent": 5, "Republican": 279}`
- By state count: 56
- Currentness inferred from term end-year: `{"ended_before_2026": 91, "ends_2026_or_later": 7, "no_end_year_present": 456}`
- Missing identity fields: `{"bioguideId": 0, "lisId": 554, "name": 0, "slug": 554}`

## ZIP/District Inventory

| path | mapping_count | fixture_only |
| --- | --- | --- |
| backend/fixtures/congress_sample/zip_district_map.json | 2 | yes |
| backend/fixtures/house_clerk_sample/zip_district_map.json | 3 | yes |
| backend/fixtures/senate_xml_sample/zip_district_map.json | 2 | yes |
| backend/fixtures/zip_district_map.json | 2 | yes |

- Total mapping rows: 9
- Unique ZIPs: 4
- By state: `{"CA": 1, "NC": 7, "TX": 1}`
- By district: `{"CA-12": 1, "NC-02": 1, "NC-04": 6, "TX-07": 1}`
- Multi-district ZIPs detected: `{"27601": ["NC-02", "NC-04"]}`
- Limitation: Only multiple mappings present in local fixture files are detectable; address-level split ZIP coverage is not represented.

## Vote Row Inventory

- Fixture roll-call rows: 14
- Fixture member vote rows: 21
- Roll calls by chamber/Congress/session: `{"house:118:session_2": 3, "house:118:session_unknown": 4, "senate:118:session_2": 3, "senate:118:session_unknown": 4}`
- Member vote rows by chamber/Congress: `{"house:118": 7, "senate:118": 14}`
- Member vote position counts: `{"nay": 4, "not_voting": 2, "present": 2, "yea": 13}`
- Fixture subject tag counts: `{"Border Security": 1, "Ceremonies": 1, "Climate": 1, "Commemorations": 1, "Commerce": 1, "Congress": 2, "Criminal Justice": 1, "Defense": 1, "Education": 2, "Energy": 1, "Foreign Policy": 1, "Health": 1, "Immigration": 1, "Infrastructure": 2, "Public Health": 1, "Public Safety": 1, "Taxation": 1, "Technology": 2, "Workforce": 2}`
- Interpretation note: Fixture vote rows have positions but do not encode reviewed support/opposition semantics.

## Source URL Coverage

- Total rows with `source_url` field inspected: 1291
- Rows with source URL: 1291
- Rows missing source URL: 0
- Rows with official source URL: 1277
- Rows with non-official source URL: 14
- Rows with malformed source URL: 0
- Non-official examples: `["https://example.com/rollcalls/house/1", "https://example.com/rollcalls/house/2", "https://example.com/rollcalls/house/3", "https://example.com/rollcalls/house/4", "https://example.com/rollcalls/house/5"]`

## Interpretation Coverage

- Interpretation-like rows: 922
- Status counts: `{"ambiguous": 42, "insufficient_evidence": 92, "interpreted": 416, "interpreted | ambiguous | insufficient_evidence": 220, "missing": 152}`
- Rows with interpreted support/opposition: 375
- Ambiguous or limited-context rows: 437
- Not-voting rows detected: 0
- Rows missing interpretation reason: 373
- Rows missing what happened: 595
- Rows missing why it mattered: 595
- Rows missing caveat or uncertainty field: 485
- Rows excluded from top-level summary candidate: 547

## Derived Artifacts

| path | exists | kind | record_count | notes |
| --- | --- | --- | --- | --- |
| docs/derived/house_comparable_policy_question_families_v1.json | yes | json | 15 | families=15 |
| docs/analysis/house_comparable_policy_question_families.json | yes | json | 15 | family_summaries=15, threshold_simulations=10 |
| docs/analysis/house_comparable_policy_question_profiles.csv | yes | csv | 9 |  |
| docs/analysis/house_comparable_policy_question_thresholds.csv | yes | csv | 10 |  |
| docs/analysis/house_continuity_readiness_analysis.json | yes | json | 12 | threshold_simulations=6 |
| docs/analysis/house_continuity_thresholds.csv | yes | csv | 6 |  |
| frontend/lib/goldenRenderFixture.mjs | yes | mjs | 28 | golden fixture vote rows counted by constructor calls |

- Reviewed interpretation batch JSON files: 35
- Rollback SQL artifacts: 27
- Manifest JSON artifacts: 8
- Deferred artifact count: 0
- Record Across House-only: yes

## Warnings

- This manifest describes repository/local-accessible files only; it is not production coverage truth.
- The script does not use production credentials and cannot distinguish loaded production rows from local caches.
- House Clerk cache gap: 2025 has 0 roll XML files at backend/data_sources/house_clerk/2025.
- Senate XML cache gap: 119_1 has 0 vote XML files at backend/data_sources/senate_xml/119_1.
- Fixture data is present and intentionally small; fallback coverage must not be presented as production coverage.
- Fixture legislator metadata missing lis_id for 3 rows.
- Fixture legislator metadata missing slug for 3 rows.
- Source URL trust gap: 14 inspected rows have non-official source URLs.
- Interpretation coverage gap: 547 interpretation-like rows are not interpreted support/opposition candidates.
- Record Across artifacts are House-only and must not be used as Senate comparison support.
- Senate-specific vote types, nominations, treaties, cloture, and amendment references still need separate public-read gates.

## Expansion Readiness Implications

- Local caches show useful House, Senate, Congress.gov, fixture, interpretation, and derived-artifact coverage, but they do not prove production load state.
- The current manifest can identify gaps before expansion, but a production read-only companion should be added before broad rollout decisions.
- House current-Congress expansion remains the nearest pilot path only after source URL, member metadata, ZIP ambiguity, and sparse-profile gates are explicit.
- Senate public reads still need chamber-aware vote-type and interpretation rules before support/opposition claims scale.

## No-Go Gates

- Do not treat this local manifest as production truth.
- Do not publish Senate reads using House assumptions.
- Do not add broad member coverage without per-member source and interpretation coverage reporting.
- Do not generate top-level reads for thin, unreviewed, ambiguous, procedural, or not-voting-heavy evidence.
- Do not expand national ZIP lookup without split-ZIP/address ambiguity handling.
- Do not use Record Across artifacts to claim change, consistency, trend, or movement.

## Recommended Next Milestone

Legislator metadata hardening, with currentness, term-boundary, identity, state/district, Senate LIS/Bioguide, and stale-member checks.
