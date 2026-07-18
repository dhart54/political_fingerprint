# ZIP Population-Weighted Ambiguity Evaluation V1

> Read-only Census-only analysis. Population-ranked ZCTA mappings are not address-resolved representation.

## Result

Official Census sources support an exact common-2020-block population allocation to the Census Bureau's whole-block CD119 tabulation plan. Population weighting changes presentation ordering in a bounded minority of ZCTAs and sharply distinguishes zero/low-population relationships, but it does not justify representative auto-selection.

## Official sources

The committed manifest pins all 51 PL 94-171 state/DC artifacts individually. Batch: `zip-population-weighting-v1-20260718`; completion: `2026-07-18T20:32:14.086282+00:00`; manifest SHA-256: `df3201bad66134eee6be59f53cd72e19c9d39c286fe5ce1389a1021412c9a851`.
Provenance modes: `{"direct_http":20,"validated_local_resume":36}`. Local resume timestamps describe validation, not retrieval.

- `cd119.zip` — 22,959,130 bytes — SHA-256 `1433feb5178dc7b4188ee30f5f7f715851f4400740b8fe1ce606a876c6294bd6` — https://www2.census.gov/programs-surveys/decennial/rdo/mapping-files/2025/119-congressional-district-befs/cd119.zip
- `tab20_zcta520_tabblock20_natl.txt` — 1,057,697,144 bytes — SHA-256 `7f077624d252fc1cc5a2d1100be07cfe038ffc152bfe193561d068b4def6bbbf` — https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_tabblock20_natl.txt
- `2020Census_PL94_171Redistricting_StatesTechDoc_English.pdf` — 1,829,750 bytes — SHA-256 `5ceb388b1cb99375136773c0e0bf10f885619e1a01828f9251d0d7e041975c51` — https://www2.census.gov/programs-surveys/decennial/2020/technical-documentation/complete-tech-docs/summary-file/2020Census_PL94_171Redistricting_StatesTechDoc_English.pdf
- `CD119_BlockSplits.pdf` — 316,267 bytes — SHA-256 `f0b70f2bde47285f63367ef667a6080ec5c2042842af1e2457c0fb4b739dadcc` — https://www2.census.gov/programs-surveys/decennial/rdo/mapping-files/2025/119-congressional-district-befs/CD119_BlockSplits.pdf
- `explanation_tab20_zcta520_tabblock20_natl.pdf` — 127,042 bytes — SHA-256 `171ea8244b73b01b0801f65cd2bae44064d08a246eb761d0a0480610a1546faa` — https://www2.census.gov/geo/pdfs/maps-data/data/rel2020/zcta520/explanation_tab20_zcta520_tabblock20_natl.pdf

## Compatibility and method

- Method: `method_a_exact_common_block_assignment`; compatible: `True`.
- Population, ZCTA assignment, and congressional assignment share the 15-digit 2020 Census tabulation-block GEOID.
- Population is 2020 Census P1 total resident population from PL 94-171 summary-level 750 records.
- District assignment is the CD119 whole-block tabulation plan for the 2024 election cycle; no spatial apportionment was used.
- Colorado split block `080010096072000` has `90` people and an authoritative whole-block assignment to CD08.

## Coverage and reconciliation

- Blocks: `8,132,968` (`5,769,942` populated; `2,363,026` zero-population).
- 50-state/DC source population: `331,449,281`.
- Population assigned to ZCTAs and reconciled through relationship/ZCTA aggregates: `331,440,751`.
- Official blocks without a ZCTA contain `8,530` people across `144,187` blocks.
- Unassigned-district blocks: `89`; affected population: `0`.
- Unassigned-district blocks affect `31` ZCTAs; affected-ZCTA checksum: `8e0ce11c87f51eefd513473298ba1ebd202384fb6e0d5509e5f54064c9288669`. Their zero population preserves exact population coverage, but block assignment is incomplete.
- Aggregate rows: `39,967`; ZCTAs: `33,642`; district pairs: `436`.
- Relationships with common blocks: `39,967`; with zero common blocks: `0` (checksum `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`).
- Exact-population-coverage relationships: `39,967`; relationships/ZCTAs with incomplete block assignment: `44` / `31`.
- Zero-population ZCTAs: `143`; zero-population relationships: `589`.
- ZCTA totals checksum: `85b4f6bea0a4fcfa950b2d4138d633392a8ea254bfd42a29cf3916209f64982d`; district totals checksum: `59b1f471ab64771ee1697bba201b16f90db580dd87ef6c45a82d5d6b1e851f32`; state parser totals checksum: `624c188080e4a00878785d95a1d9bf2ff53f16bdd0ab06bc3824e8bad5b7ad2f`.

## Population policy grid

| Policy | Relationships | ZCTAs | Ambiguous | Single | No survivor | Auto-select |
|---|---:|---:|---:|---:|---:|---:|
| p0_all | 39,967 | 33,642 | 5,862 | 27,780 | 0 | 0 |
| p1_positive | 39,378 | 33,499 | 5,505 | 27,994 | 143 | 0 |
| gte_0_01_percent | 39,354 | 33,499 | 5,482 | 28,017 | 143 | 0 |
| gte_0_05_percent | 39,226 | 33,499 | 5,375 | 28,124 | 143 | 0 |
| gte_0_1_percent | 39,090 | 33,499 | 5,260 | 28,239 | 143 | 0 |
| gte_0_5_percent | 38,529 | 33,499 | 4,761 | 28,738 | 143 | 0 |
| gte_1_percent | 38,187 | 33,499 | 4,457 | 29,042 | 143 | 0 |
| gte_2_percent | 37,707 | 33,499 | 4,034 | 29,465 | 143 | 0 |
| gte_5_percent | 36,923 | 33,499 | 3,307 | 30,192 | 143 | 0 |
| gte_10_percent | 36,050 | 33,499 | 2,502 | 30,997 | 143 | 0 |
| gte_25_percent | 34,822 | 33,499 | 1,320 | 32,179 | 143 | 0 |
| gte_50_percent | 33,475 | 33,474 | 1 | 33,473 | 168 | 0 |

## Population versus land

- Accepted ZCTAs: `33,642`; positive-population: `33,499`; zero-population excluded from ranking: `143`.
- Positive-population unique top agrees for `32,872` ZCTAs and differs for `626`; tied population tops: `1`.
- Positive-population ambiguous ZCTAs: `5,861`; unique-top agreement/disagreement within them: `5,234` / `626`.
- Strict population majority exists while strict land majority does not: `32`; strict land majority exists while strict population majority does not: `16`.
- Exact-half population/land cases: `1` / `0`. The separate `>=50%` sensitivity row remains inclusive.
- Positive-land relationships with zero population: `552`; water-only relationships with nonzero population: `0`.
- Tiny positive-land relationships at or below 0.01% include `3` with at least one person and `1` with at least ten people.

## Dominance and margins

| Top population share | Qualifying ambiguous ZCTAs | Nonqualifying | Land top differs |
|---|---:|---:|---:|
| gte_50_percent | 5,836 | 25 | 619 |
| gte_60_percent | 5,326 | 535 | 419 |
| gte_70_percent | 4,815 | 1,046 | 293 |
| gte_75_percent | 4,505 | 1,356 | 218 |
| gte_80_percent | 4,190 | 1,671 | 186 |
| gte_90_percent | 3,338 | 2,523 | 107 |
| gte_95_percent | 2,540 | 3,321 | 57 |

| Top-minus-second margin | Qualifying ambiguous ZCTAs | Nonqualifying | Zero-population undefined |
|---|---:|---:|---:|
| gte_1_points | 5,840 | 21 | 1 |
| gte_5_points | 5,742 | 119 | 1 |
| gte_10_points | 5,612 | 249 | 1 |
| gte_20_points | 5,354 | 507 | 1 |
| gte_25_points | 5,215 | 646 | 1 |
| gte_33_points | 5,013 | 848 | 1 |
| gte_50_points | 4,518 | 1,343 | 1 |

## Deterministic case studies

- `top_population_differs_from_top_land`: `{"land_top":"MA-02","population_top":"MA-01","zcta":"01027"}`
- `population_weighting_resolves_land_ambiguity`: `{"land_top":"MA-02","land_top_share":{"denominator":52558568,"numerator":35307583},"population_share":{"denominator":17896,"numerator":16211},"population_top":"MA-01","zcta":"01027"}`
- `zero_population_relationship_removed_by_p1`: `{"land_part":16510,"mapping":"MA-03","water_only":false,"zcta":"01436"}`
- `population_ambiguity_remains_severe`: `{"margin":{"denominator":8888,"numerator":345},"top_mapping":"MA-02","top_share":{"denominator":17776,"numerator":9233},"zcta":"01570"}`
- `multi_state_zcta`: `{"mappings":["RI-01","MA-04"],"zcta":"02861"}`
- `large_land_share_zero_or_negligible_population`: `{"land_share":{"denominator":4938547,"numerator":1850944},"mapping":"NJ-07","population":0,"zcta":"07851","zcta_population":245}`
- `no_population_majority`: `{"top_mapping":"NY-08","top_share":{"denominator":83519,"numerator":36494},"zcta":"11223"}`
- `nearly_tied_population_shares`: `{"margin":{"denominator":692,"numerator":5},"second_mapping":"NY-19","top_mapping":"NY-23","zcta":"13835"}`
- `dc_98_candidate_normalization`: `{"runtime_approved":false,"source_mapping":"DC-98","zcta":"20001"}`
- `tiny_land_sliver_meaningful_population`: `{"land_share":{"denominator":28563881,"numerator":2359},"mapping":"VA-03","population":24,"zcta":"23462","zcta_population":68045}`
- `currently_vacant_district`: `{"classifications":["officially_vacant","filled_current_voting_seat","filled_current_voting_seat"],"mappings":["GA-13","GA-04","GA-10"],"zcta":"30012"}`
- `populated_block_unsafe_under_spatial_apportionment`: `{"assignment_quality":"exact_official_assignment","block_geoid":"080010096072000","cd_record":847713,"district":"08","pl_record":84436,"population":90,"zcta":"80003","zcta_record":6759636}`

## Current-seat reconciliation

- Unique pair classes: `{"candidate_dc_normalization":1,"filled_current_voting_seat":431,"officially_vacant":4}`.
- Relationship row classes: `{"candidate_dc_normalization":57,"filled_current_voting_seat":39659,"officially_vacant":251}`.
- Vacancies: `CA-14, FL-20, GA-13, TX-23`.
- DC-98 remains candidate normalization to seeded DC-00 only; runtime approval is false.

## Product boundary

Population share may preserve and order possible districts and support versioned low/zero-population labels. The measurement is from 2020, current residents may differ, and minority-district addresses remain valid. Population concentration cannot identify a user's district or authorize representative auto-selection. A validated full-address resolver remains necessary.

## Staging decision

No `0016` migration is proposed. The aggregate-evidence model is preferred over a production block ledger, but production storage should wait for independent review and a separate implementation milestone. Migration `0015` remains unchanged, SHA-pinned, and unapplied.

## Production safety

- House snapshot: `house-119-20260713T011722Z`; legislators fingerprint: `87c12b1054b5390af3a4bc16a1234ecb71ef10edd52b6ad700441e122f1ae7b7` across `637` rows.
- House domain counts: `{"delegates":5,"filled_seats":437,"resident_commissioner":1,"source_conflicts":0,"unknown_seats":0,"vacant_seats":4,"voting_representatives":431}`.
- `zip_district_mappings` rows: `0` before and `0` after.
- Routes use `zip_district_map` and do not read `zip_district_mappings`: `True`; feature flag: `absent_not_configured`.
- Session and transaction read-only modes were confirmed with a bounded 30-second statement timeout. Canonical House checksums and the legislators fingerprint matched before/after. No production/runtime mutation occurred. Production auto-select eligibility remains zero.
