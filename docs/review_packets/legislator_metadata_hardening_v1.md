# Legislator Metadata Hardening V1

## Summary

This is repository/local-accessible metadata only. It is not production coverage truth unless a future read-only production report is generated with credentials.

- Read-only: yes
- Requires production credentials: no
- Sources inspected: 16
- Legislator/member rows inspected: 2729
- Warnings emitted: 12

Highest metadata findings:
- Local app-style legislator rows do not persist Senate LIS IDs, slugs, or term boundaries.
- Congress.gov member cache rows are useful identity sources but do not contain app IDs, slugs, LIS IDs, or explicit current flags.
- Senate XML member cache contains LIS and Bioguide IDs, but the normalized app legislator shape drops LIS before persistence.
- ZIP fixture mappings are fixture-only and include a locally detectable split-ZIP conflict for ZIP 27601.
- Lookup/search code assumes one ZIP record maps to one district and empty search can expose all loaded legislators.

## Sources Inspected

| source_kind | path | exists | row_count | notes |
| --- | --- | --- | --- | --- |
| fixture_legislators | backend/fixtures/legislators.json | yes | 3 | App-style fixture rows with persisted ids but no slug, LIS, or term boundaries. |
| congress_sample_members | backend/fixtures/congress_sample/members.json | yes | 3 | Sample Congress.gov-shaped rows normalized by the congress adapter. |
| congress_gov_member_cache | backend/data_sources/congress/members | yes | 554 | Local Congress.gov member cache; not proof of loaded app or production rows. |
| house_clerk_member_xml | backend/fixtures/house_clerk_sample/members.xml | yes | 3 | House member XML includes Bioguide, state, district, party, and names; app ids are generated during normalization. |
| senate_member_xml | backend/fixtures/senate_xml_sample/members.xml | yes | 2 | Senate member XML includes LIS and Bioguide IDs, state, party, and names; no district and no term boundaries. |
| house_clerk_member_xml | backend/data_sources/house_clerk/2023/members.xml | yes | 441 | House member XML includes Bioguide, state, district, party, and names; app ids are generated during normalization. |
| house_clerk_member_xml | backend/data_sources/house_clerk/2024/members.xml | yes | 441 | House member XML includes Bioguide, state, district, party, and names; app ids are generated during normalization. |
| house_clerk_member_xml | backend/data_sources/house_clerk/2026/members.xml | yes | 441 | House member XML includes Bioguide, state, district, party, and names; app ids are generated during normalization. |
| house_clerk_member_xml | backend/data_sources/house_clerk/members.xml | yes | 441 | House member XML includes Bioguide, state, district, party, and names; app ids are generated during normalization. |
| senate_member_xml | backend/data_sources/senate_xml/118_1/members.xml | yes | 100 | Senate member XML includes LIS and Bioguide IDs, state, party, and names; no district and no term boundaries. |
| senate_member_xml | backend/data_sources/senate_xml/118_2/members.xml | yes | 100 | Senate member XML includes LIS and Bioguide IDs, state, party, and names; no district and no term boundaries. |
| senate_member_xml | backend/data_sources/senate_xml/119_2/members.xml | yes | 100 | Senate member XML includes LIS and Bioguide IDs, state, party, and names; no district and no term boundaries. |
| senate_member_xml | backend/data_sources/senate_xml/members.xml | yes | 100 | Senate member XML includes LIS and Bioguide IDs, state, party, and names; no district and no term boundaries. |
| schema | backend/migrations/0001_initial_schema.sql | yes |  | Stored legislators table has id, bioguide_id, name_display, chamber, state, district, party, and in_office; no LIS, slug, or term fields. |
| lookup_routes | backend/app/api/lookup.py; backend/app/api/search.py; backend/app/api/precomputed.py | yes |  | Inspected ZIP lookup, supported ZIPs, legislator search, fallback serialization, and DB lookup helpers. |
| frontend_profile_lookup | frontend/app/page.js; frontend/components/ZipLookupPanel.js; frontend/lib/api.js | yes |  | Inspected default profile, default ZIP lookup, supported ZIP labels, search API use, and visible metadata assumptions. |

## Identity Completeness Table

| source_kind | rows | missing_app_internal_id | missing_bioguide_id | missing_lis_id_for_senators | missing_display_name | missing_persisted_slug | missing_chamber | missing_state | missing_house_district | missing_party | missing_current_flag | missing_term_start | missing_term_end | duplicate_bioguide_ids | duplicate_app_internal_ids | duplicate_slugs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| congress_gov_member_cache | 554 | 554 | 0 | 110 | 0 | 554 | 0 | 0 | 0 | 0 | 554 | 0 | 456 | 0 | 0 | 1 |
| congress_sample_members | 3 | 0 | 0 | 2 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 0 | 0 | 0 |
| fixture_legislators | 3 | 0 | 0 | 2 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 0 | 0 | 0 |
| house_clerk_member_xml | 1767 | 1767 | 15 | 0 | 15 | 1767 | 0 | 0 | 0 | 15 | 0 | 1767 | 1767 | 437 | 0 | 437 |
| senate_member_xml | 402 | 402 | 0 | 0 | 0 | 402 | 0 | 0 | 0 | 0 | 400 | 402 | 402 | 100 | 0 | 100 |

- Persisted slugs are not present in inspected local metadata; app routing derives `leg_...` ids from display names.
- The stored app schema has no LIS or term-boundary columns.
- Missing Senate LIS counts are source-specific: Senate XML has LIS, while app fixture and Congress.gov cache rows do not.

## Chamber/State/District Quality Table

| source_kind | rows | unknown_chamber | mixed_chamber_format_rows | house_rows_missing_district | senate_rows_with_house_style_district | invalid_state_values | invalid_house_district_values | at_large_house_districts | senate_lis_gaps | senate_bioguide_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| congress_gov_member_cache | 554 | 0 | 554 | 0 | 5 | 5 | 0 | 11 | 110 | 0 |
| congress_sample_members | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| fixture_legislators | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| house_clerk_member_xml | 1767 | 0 | 0 | 0 | 0 | 0 | 0 | 48 | 0 | 0 |
| senate_member_xml | 402 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- Congress.gov chamber values use labels such as `House of Representatives`; the report normalizes those while counting format inconsistency.
- Senate districts should be absent or explicitly statewide in UI copy; numeric districts on Senate rows are flagged as House-style confusion.
- At-large House districts are recognized as `00`, `0`, or at-large labels.

## Currentness/Term-Boundary Table

| source_kind | rows | inferred_current_or_recent | clearly_stale | ambiguous_currentness | no_end_year_or_no_term_boundary | term_dates_before_supported_window | in_office_term_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| congress_gov_member_cache | 554 | 7 | 18 | 456 | 456 | 18 | 0 |
| congress_sample_members | 3 | 0 | 0 | 3 | 3 | 0 | 0 |
| fixture_legislators | 3 | 0 | 0 | 3 | 3 | 0 | 0 |
| house_clerk_member_xml | 1767 | 0 | 0 | 1767 | 1767 | 0 | 0 |
| senate_member_xml | 402 | 0 | 0 | 402 | 402 | 0 | 0 |

- Currentness is inferred from local fields only. No external network or production query is used.
- `ambiguous_no_end_year` is not treated as production current truth; it means the local row lacks an end year.
- Fixture and XML current flags without term boundaries are useful but insufficient for cross-Congress expansion gates.

## Duplicate/Conflict Findings

- Same Bioguide mapped to multiple app IDs: 2
- Same slug mapped to multiple people: 2
- Same state/district/current House seat mapped to multiple current members: 67
- Same Senate state/seat/class ambiguity groups: 51
- ZIP mappings resolving to multiple districts: `{"27601": ["NC-02", "NC-04"]}`
- Fixture/Congress.gov disagreements: 0

## ZIP/District Lookup Implications

- ZIP mapping rows: 9
- Fixture-only ZIP mapping rows: 9
- Unique ZIPs: 4
- Multi-district ZIPs detected: `{"27601": ["NC-02", "NC-04"]}`
- ZIP rows without any local House match: 0
- ZIP rows without app/fixture House match: 0
- Limitation: Only multiple mappings present in local fixture files are detectable; address-level split ZIP coverage is not represented.

Lookup safety implications:
- A ZIP resolves to a single `zip_district_map` row with one state and district.
- The House representative is selected by state and district with `ORDER BY id LIMIT 1`.
- Senators are selected by state; no seat/class or currentness caveat is exposed in the route payload.
- Fallback ZIP lookup uses the first matching fixture ZIP row and fixture legislators.
- One-ZIP-one-district assumed: zip_district_map has ZIP as primary key and code uses a single zip_record.
- Empty search exposes all loaded legislators: yes

Warnings needed before national expansion:
- Loaded coverage is not national coverage.
- ZIP-only lookup may be ambiguous; address-level resolution may be needed.
- Fixture/sample rows must be visibly labeled when they appear.
- Currentness and term-boundary status should be shown or used as a gate before auto-loading a profile.
- Senate identity should disclose LIS/Bioguide handling and missing seat/class metadata.

## Senate Metadata Readiness

| source_kind | rows | missing_lis_id | missing_bioguide_id | missing_state | missing_seat_rank_or_class | xml_source_identity_rows | senate_rows_with_house_style_district |
| --- | --- | --- | --- | --- | --- | --- | --- |
| congress_gov_member_cache | 110 | 110 | 0 | 0 | 110 | 0 | 5 |
| congress_sample_members | 2 | 2 | 0 | 0 | 2 | 0 | 0 |
| fixture_legislators | 2 | 2 | 0 | 0 | 2 | 0 | 0 |
| senate_member_xml | 402 | 0 | 0 | 0 | 2 | 402 | 0 |

- Senate LIS ID exists in inspected local sources: yes
- Bioguide ID exists in inspected local sources: yes
- State exists in inspected local sources: yes
- Seat rank or class exists in inspected local sources: yes
- Senate class exists in inspected local sources: no
- Member XML source identity exists: yes

- Normalized app legislators do not preserve LIS IDs even though Senate vote matching uses LIS internally.
- The app schema has no Senate seat/class field; Senate XML stateRank is not a full Senate class model.
- Nominations, treaties, and cloture are not vote-semantics decisions here, but they require chamber-specific metadata and source caveats before public Senate rollout.
- Senate XML member files provide useful local identity, but local files alone do not prove production mapping completeness.

## Expansion Gates

- No broad House rollout unless each current House member has stable Bioguide, state, district, currentness, and source coverage status.
- No Senate rollout unless Senate identity includes reliable Bioguide/LIS handling and chamber-specific caveats.
- No national ZIP rollout until split-ZIP/address ambiguity is handled.
- No profile auto-load from fallback/sample data without a clear user-facing sample or coverage label.
- No cross-Congress comparison unless member identity and term boundaries are reliable.

## No-Go Items

- Do not treat this local report as production coverage truth.
- Do not fix metadata by editing fixture or production-like data in this milestone.
- Do not use fallback/sample rows as unlabeled public coverage.
- Do not auto-select a House member from split or ambiguous ZIP evidence.
- Do not publish Senate reads until LIS/Bioguide handling and Senate metadata caveats are reliable.
- Do not infer cross-time movement from rows whose term boundaries are ambiguous.

## Warnings

- This is repository/local-accessible metadata only. It is not production coverage truth unless a future read-only production report is generated with credentials.
- Missing Bioguide IDs are present in local metadata sources.
- Missing Senate LIS IDs are present for senator rows in one or more local sources.
- Persisted slugs are missing even though app routing derives slug-like legislator IDs from display names.
- Ambiguous currentness is present because rows lack term boundaries or explicit current flags.
- Stale member rows are present relative to the supported 119th Congress window.
- Duplicate Bioguide conflicts are present across local sources.
- Duplicate current House state/district seat conflicts are present across local sources.
- Fixture-only ZIP mappings are present and must not be treated as production coverage.
- Split-ZIP ambiguity is detectable in local fixture mappings.
- Senate metadata is not sufficient for public Senate rollout without LIS/seat/class caveats and mapping gates.
- Production-vs-local ambiguity remains: this report does not query production credentials or production tables.

## Recommended Next Milestone

ZIP and district ambiguity hardening, followed by a production read-only metadata companion report before any broad House, Senate, or national ZIP rollout.
