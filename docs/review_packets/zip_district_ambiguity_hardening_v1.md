# ZIP and District Ambiguity Hardening V1

## Summary

This is repository/local-accessible ZIP and district metadata only. It is not production coverage truth unless a future read-only production report is generated with credentials.

- Read-only: yes
- Requires production credentials: no
- ZIP mapping rows: 9
- Unique ZIPs: 4
- Fixture-only mapping rows: 9
- Non-fixture mapping rows: 0
- Warnings emitted: 8

Highest ZIP/district findings:
- Current lookup code and schema treat a ZIP as one state/district mapping.
- Local ZIP mappings are fixture-only and should not be treated as production or national coverage.
- Local fixtures detect split-ZIP ambiguity for ZIPs that map to more than one district.
- ZIP-only lookup can auto-select a House member today, so national rollout needs ambiguity handling first.

## Sources Inspected

| source_kind | path | exists | row_count | notes |
| --- | --- | --- | --- | --- |
| backend_zip_lookup_routes | backend/app/api/lookup.py | yes |  | ZIP lookup and supported ZIP route definitions. |
| backend_search_routes | backend/app/api/search.py | yes |  | Legislator search route and default empty query. |
| backend_lookup_helpers | backend/app/api/precomputed.py | yes |  | DB and fallback ZIP lookup, House selection, Senate selection, and supported ZIP helpers. |
| schema | backend/migrations/0001_initial_schema.sql | yes |  | zip_district_map primary-key and state/district column constraints. |
| frontend_zip_lookup | frontend/components/ZipLookupPanel.js | yes |  | Default ZIP, result copy, supported ZIP copy, and auto-select behavior. |
| frontend_home | frontend/app/page.js | yes |  | Sample-profile copy around default profile state. |
| etl_seed_import | backend/app/etl/seed.py | yes |  | ZIP mapping insert/copy and bundle dedupe behavior. |
| etl_congress_adapter | backend/app/etl/congress_adapter.py | yes |  | ZIP map loading from source directory. |
| etl_house_clerk_adapter | backend/app/etl/house_clerk_adapter.py | yes |  | House member state/district parsing and ZIP map loading. |
| etl_senate_xml_adapter | backend/app/etl/senate_xml_adapter.py | yes |  | Senate member state handling and ZIP map loading. |
| etl_refresh_merge | backend/app/etl/current_congress_refresh.py; backend/app/etl/historical_congress_refresh.py | yes |  | Refresh bundle ZIP dedupe by ZIP. |
| zip_district_map | backend/fixtures/congress_sample/zip_district_map.json | yes | 2 | Repository/local ZIP mapping file. |
| zip_district_map | backend/fixtures/house_clerk_sample/zip_district_map.json | yes | 3 | Repository/local ZIP mapping file. |
| zip_district_map | backend/fixtures/senate_xml_sample/zip_district_map.json | yes | 2 | Repository/local ZIP mapping file. |
| zip_district_map | backend/fixtures/zip_district_map.json | yes | 2 | Repository/local ZIP mapping file. |
| local_house_metadata | backend/data_sources/congress/members/118_members.json | yes | 444 | Local House metadata source used only for deterministic ZIP-to-House match checks. |
| local_house_metadata | backend/data_sources/house_clerk/2023/members.xml | yes | 441 | Local House metadata source used only for deterministic ZIP-to-House match checks. |
| local_house_metadata | backend/data_sources/house_clerk/2024/members.xml | yes | 441 | Local House metadata source used only for deterministic ZIP-to-House match checks. |
| local_house_metadata | backend/data_sources/house_clerk/2026/members.xml | yes | 441 | Local House metadata source used only for deterministic ZIP-to-House match checks. |
| local_house_metadata | backend/data_sources/house_clerk/members.xml | yes | 441 | Local House metadata source used only for deterministic ZIP-to-House match checks. |
| local_house_metadata | backend/fixtures/congress_sample/members.json | yes | 1 | Local House metadata source used only for deterministic ZIP-to-House match checks. |
| local_house_metadata | backend/fixtures/house_clerk_sample/members.xml | yes | 3 | Local House metadata source used only for deterministic ZIP-to-House match checks. |
| local_house_metadata | backend/fixtures/legislators.json | yes | 1 | Local House metadata source used only for deterministic ZIP-to-House match checks. |

## Current Lookup Assumption Map

| assumption | detected | evidence |
| --- | --- | --- |
| zip_lookup_implemented_in |  | ["backend/app/api/lookup.py", "backend/app/api/precomputed.py", "frontend/lib/api.js", "frontend/components/ZipLookupPanel.js"] |
| search_implemented_in |  | ["backend/app/api/search.py", "backend/app/api/precomputed.py"] |
| zip_treated_as_unique | yes | backend/migrations/0001_initial_schema.sql defines zip_district_map.zip as PRIMARY KEY. |
| lookup_returns_single_district | yes | DB lookup uses one zip_record; fallback uses next(...) for first matching fixture ZIP row. |
| house_member_selection_uses_state_plus_district | yes | backend/app/api/precomputed.py filters House rows by chamber, state, and district. |
| house_member_selection_order_by_id_limit_1 | yes | backend/app/api/precomputed.py selects one House row using ORDER BY id LIMIT 1. |
| senators_selected_by_state_only | yes | Senate rows are selected by state only. |
| supported_zips_fixture_or_sample_driven | yes | /lookup/zips returns fixture fallback mappings when DB rows are unavailable. |
| fallback_sample_zip_risk | yes | Frontend displays loaded ZIP mappings from the returned data_source, including fixtures. |
| frontend_default_zip | yes | ZipLookupPanel auto-runs default ZIP 27701 on mount. |
| frontend_single_mapping_copy | yes | ZipLookupPanel renders `ZIP ... maps to state-district`. |
| frontend_auto_selects_house_profile | yes | Successful ZIP lookup auto-selects the returned House representative when present. |
| frontend_sample_profile_label | yes | Home page labels the initial default profile as sample before user lookup/search. |
| empty_search_exposes_loaded_legislators | yes | Empty q is allowed and DB query returns all legislators when q is empty. |
| etl_zip_bundle_dedupes_by_zip | yes | Seed and refresh bundle merges dedupe zip_district_map rows by ZIP. |
| route_file_contains_lookup_zip |  | yes |

## ZIP Mapping Inventory

- Total mapping rows: 9
- Unique ZIPs: 4
- Fixture-only rows: 9
- Non-fixture rows: 0
- Counts by ZIP: `{"27601": 3, "27701": 4, "77007": 1, "94102": 1}`
- Counts by state: `{"CA": 1, "NC": 7, "TX": 1}`
- Counts by district: `{"CA-12": 1, "NC-02": 1, "NC-04": 6, "TX-07": 1}`
- Counts by source kind: `{"fixture": 9}`
- Duplicate identical mappings: `[{"count": 2, "mapping_key": "27601:NC:04", "source_files": ["backend/fixtures/congress_sample/zip_district_map.json", "backend/fixtures/zip_district_map.json"]}, {"count": 4, "mapping_key": "27701:NC:04", "source_files": ["backend/fixtures/congress_sample/zip_district_map.json", "backend/fixtures/house_clerk_sample/zip_district_map.json", "backend/fixtures/senate_xml_sample/zip_district_map.json", "backend/fixtures/zip_district_map.json"]}]`
- Missing state rows: 0
- Missing district rows: 0
- Invalid district rows: 0

## Ambiguity Findings

- One-ZIP-one-district assumption detected: yes
- ZIPs mapping to multiple districts: `{"27601": ["NC-02", "NC-04"]}`
- ZIPs mapping to multiple states: `{}`
- Address-level resolution implemented: no
- Detection limit: Only multiple mappings present in repository/local-accessible files are detectable here; address-level split-ZIP coverage is not represented.

## House Member Match Findings

- Local House rows inspected: 2213
- Unique current House seats inspected: 864
- ZIP rows without matching local House legislator: 0
- ZIP rows with multiple matching current House legislators: 8
- Matching limit: Local House matches are repository/local-accessible rows only; this does not certify production currentness or loaded production seat coverage.

Rows with multiple local current House matches:
| zip | state | district | source_file | matching_current_house_people |
| --- | --- | --- | --- | --- |
| 27701 | NC | 04 | backend/fixtures/congress_sample/zip_district_map.json | 3 |
| 27601 | NC | 04 | backend/fixtures/congress_sample/zip_district_map.json | 3 |
| 27701 | NC | 04 | backend/fixtures/house_clerk_sample/zip_district_map.json | 3 |
| 77007 | TX | 07 | backend/fixtures/house_clerk_sample/zip_district_map.json | 2 |
| 94102 | CA | 12 | backend/fixtures/house_clerk_sample/zip_district_map.json | 2 |
| 27701 | NC | 04 | backend/fixtures/senate_xml_sample/zip_district_map.json | 3 |
| 27701 | NC | 04 | backend/fixtures/zip_district_map.json | 3 |
| 27601 | NC | 04 | backend/fixtures/zip_district_map.json | 3 |

## Public Lookup Risk Analysis

- ZIP-only lookup can be wrong for split ZIPs because a ZIP can contain addresses from multiple House districts.
- A one-ZIP-one-district table cannot safely scale nationally without ambiguity detection and user-facing handling.
- Address-level lookup or an ambiguity UI is needed before national ZIP rollout.
- Fallback/sample ZIP mappings must be clearly labeled so fixture coverage is not mistaken for production coverage.
- Current NC fixture behavior should not be generalized to national coverage or address-accurate representation.
- Auto-selecting a House profile from an ambiguous ZIP would overstate what the ZIP evidence can prove.

## Expansion Gates

- No auto-select House member when a ZIP maps to multiple districts.
- No national ZIP dataset without source, retrieval date, coverage date, and version metadata.
- No unsupported ZIP fallback that appears as production coverage.
- No ambiguous ZIP result without user-facing ambiguity messaging.
- No district match unless current House member metadata passes identity/currentness gates.
- No Senate state selection without currentness, seat, or class metadata caveats.

## No-Go Items

- Do not treat this local ZIP report as production coverage truth.
- Do not download or ingest national ZIP data in this milestone.
- Do not mutate local or production databases.
- Do not change public lookup or frontend product behavior in this milestone.
- Do not implement address-level district resolution here.
- Do not auto-select a House member from split or ambiguous ZIP evidence.

## Warnings

- One-ZIP-one-district assumption is present in schema and lookup behavior.
- Split ZIPs detected in local mappings: {"27601": ["NC-02", "NC-04"]}.
- Duplicate identical ZIP/state/district mappings are present across local source files.
- ZIP rows with multiple matching current House legislators are present in local metadata.
- All repository/local ZIP mappings are fixture-only and must not be treated as production coverage.
- Fallback/sample ZIP behavior can be mistaken for production coverage without explicit labeling.
- Production-vs-local ambiguity remains: this report does not query production credentials or production tables.
- Address-level district resolution is not implemented in this milestone.

Warning catalog:
| warning_key | active | message |
| --- | --- | --- |
| one_zip_one_district_assumption | yes | One-ZIP-one-district assumption is present in schema and lookup behavior. |
| split_zips_detected | yes | Split ZIPs detected in local mappings: {"27601": ["NC-02", "NC-04"]}. |
| multi_state_zips_detected | no | Multi-state ZIPs detected in local mappings: {}. |
| duplicate_mappings | yes | Duplicate identical ZIP/state/district mappings are present across local source files. |
| missing_state_or_district | no | ZIP rows missing state or district are present. |
| invalid_district_values | no | ZIP rows with invalid district values are present. |
| no_matching_house_legislator | no | ZIP rows without a matching local current House legislator are present. |
| multiple_matching_current_house_legislators | yes | ZIP rows with multiple matching current House legislators are present in local metadata. |
| fixture_only_zip_mappings | yes | All repository/local ZIP mappings are fixture-only and must not be treated as production coverage. |
| fallback_sample_zip_risk | yes | Fallback/sample ZIP behavior can be mistaken for production coverage without explicit labeling. |
| production_vs_local_ambiguity | yes | Production-vs-local ambiguity remains: this report does not query production credentials or production tables. |
| address_level_resolution_not_implemented | yes | Address-level district resolution is not implemented in this milestone. |

## Recommended Next Milestone

Address-level lookup or ambiguity UI design spike, followed by a read-only production ZIP coverage companion report before national ZIP rollout.
