"""Generate a read-only local ZIP and district ambiguity report.

This script only inspects repository files. It does not import app DB helpers,
open network connections, or require production credentials.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


REPORT_MD = Path("docs/review_packets/zip_district_ambiguity_hardening_v1.md")
REPORT_JSON = Path("docs/review_packets/zip_district_ambiguity_hardening_v1.json")
COVERAGE_STATEMENT = (
    "This is repository/local-accessible ZIP and district metadata only. It is "
    "not production coverage truth unless a future read-only production report "
    "is generated with credentials."
)
STATE_NAME_TO_CODE = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}
VALID_STATE_CODES = set(STATE_NAME_TO_CODE.values()) | {"AS", "GU", "MP", "PR", "VI"}
AT_LARGE_DISTRICTS = {"0", "00", "at large", "at-large", "delegate", "resident commissioner"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD)
    parser.add_argument("--json-out", type=Path, default=REPORT_JSON)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)
    write_outputs(report, repo_root=repo_root, markdown_out=args.markdown_out, json_out=args.json_out)
    print(f"Wrote {args.markdown_out}")
    print(f"Wrote {args.json_out}")
    return 0


def build_report(repo_root: Path) -> dict[str, Any]:
    zip_rows = collect_zip_rows(repo_root)
    house_rows = collect_house_rows(repo_root)
    lookup_assumptions = inspect_lookup_assumptions(repo_root)
    inventory = build_zip_inventory(zip_rows=zip_rows)
    ambiguity = build_ambiguity_findings(zip_rows=zip_rows)
    house_matches = build_house_match_findings(zip_rows=zip_rows, house_rows=house_rows)
    warning_catalog, active_warnings = build_warning_catalog(
        lookup_assumptions=lookup_assumptions,
        inventory=inventory,
        ambiguity=ambiguity,
        house_matches=house_matches,
    )
    gates = expansion_gates()
    no_go = no_go_items()
    risk = public_lookup_risk_analysis()

    report = {
        "schema_version": "zip_district_ambiguity_hardening_v1",
        "scope": {
            "coverage_statement": COVERAGE_STATEMENT,
            "read_only": True,
            "requires_production_credentials": False,
            "production_credentials_used": False,
            "production_tables_queried": False,
        },
        "summary": {
            "zip_mapping_rows": len(zip_rows),
            "unique_zips": inventory["unique_zips"],
            "fixture_only_mapping_rows": inventory["fixture_only_mapping_rows"],
            "non_fixture_mapping_rows": inventory["non_fixture_mapping_rows"],
            "warnings_emitted": len(active_warnings),
            "highest_findings": [
                "Current lookup code and schema treat a ZIP as one state/district mapping.",
                "Local ZIP mappings are fixture-only and should not be treated as production or national coverage.",
                "Local fixtures detect split-ZIP ambiguity for ZIPs that map to more than one district.",
                "ZIP-only lookup can auto-select a House member today, so national rollout needs ambiguity handling first.",
            ],
        },
        "sources_inspected": sources_inspected(repo_root, zip_rows=zip_rows, house_rows=house_rows),
        "current_lookup_assumption_map": lookup_assumptions,
        "zip_mapping_inventory": inventory,
        "ambiguity_findings": ambiguity,
        "house_member_match_findings": house_matches,
        "public_lookup_risk_analysis": risk,
        "expansion_gates": gates,
        "no_go_items": no_go,
        "warnings": active_warnings,
        "warning_catalog": warning_catalog,
        "recommended_next_milestone": (
            "Address-level lookup or ambiguity UI design spike, followed by a read-only production ZIP "
            "coverage companion report before national ZIP rollout."
        ),
    }
    return report


def collect_zip_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    backend_root = repo_root / "backend"
    if not backend_root.exists():
        return rows

    for path in sorted(backend_root.glob("**/zip_district_map.json")):
        data = _as_list(_load_json(path))
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            raw_zip = _clean(item.get("zip"))
            raw_state = _clean(item.get("state"))
            raw_district = _clean(item.get("district"))
            state = normalize_state(raw_state)
            district = normalize_district(raw_district)
            rows.append(
                {
                    "row_id": f"{_rel(repo_root, path)}#{index}",
                    "path": _rel(repo_root, path),
                    "source_file": _rel(repo_root, path),
                    "source_kind": classify_zip_source(repo_root, path),
                    "fixture_only": is_fixture_path(repo_root, path),
                    "zip": raw_zip,
                    "state": state,
                    "district": district,
                    "raw_state": raw_state,
                    "raw_district": raw_district,
                    "valid_zip": bool(re.fullmatch(r"\d{5}", raw_zip)),
                    "valid_state": bool(state and state in VALID_STATE_CODES),
                    "valid_district": is_valid_house_district(district),
                    "missing_state": not bool(raw_state),
                    "missing_district": not bool(raw_district),
                    "mapping_key": mapping_key(raw_zip, state, district),
                }
            )
    return rows


def collect_house_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((repo_root / "backend/fixtures").glob("**/legislators.json")):
        rows.extend(load_json_house_rows(repo_root, path, source_kind="fixture_legislators"))
    for path in sorted((repo_root / "backend/fixtures").glob("**/members.json")):
        rows.extend(load_json_house_rows(repo_root, path, source_kind="fixture_members"))
    for path in sorted((repo_root / "backend/data_sources/congress/members").glob("*.json")):
        rows.extend(load_json_house_rows(repo_root, path, source_kind="congress_gov_member_cache"))
    for path in sorted((repo_root / "backend/fixtures").glob("**/members.xml")):
        rows.extend(load_house_xml_rows(repo_root, path, source_kind="fixture_house_member_xml"))
    for path in sorted((repo_root / "backend/data_sources/house_clerk").glob("**/members.xml")):
        rows.extend(load_house_xml_rows(repo_root, path, source_kind="house_clerk_member_xml"))
    return sorted(rows, key=lambda row: (row["state"] or "", row["district"] or "", row["source_file"], row["person_key"]))


def load_json_house_rows(repo_root: Path, path: Path, *, source_kind: str) -> list[dict[str, Any]]:
    data = _load_json(path)
    members = _as_list(data.get("members") if isinstance(data, dict) else data)
    rows = []
    for index, item in enumerate(members):
        if not isinstance(item, dict):
            continue
        chamber = normalize_chamber(item.get("chamber") or item.get("currentMemberChamber") or item.get("terms", {}).get("item", [{}])[-1].get("chamber") if isinstance(item.get("terms"), dict) else item.get("chamber"))
        state, district = extract_json_state_district(item)
        if chamber != "house" and not district:
            continue
        if chamber and chamber != "house":
            continue
        name = _clean(item.get("name_display") or item.get("directOrderName") or item.get("name") or item.get("officialName"))
        bioguide = _clean(item.get("bioguide_id") or item.get("bioguideId") or item.get("bioguideID"))
        current = item.get("in_office", item.get("currentMember", True))
        rows.append(
            house_row(
                repo_root=repo_root,
                path=path,
                row_index=index,
                source_kind=source_kind,
                name=name,
                bioguide=bioguide,
                state=state,
                district=district,
                current=current is not False,
            )
        )
    return rows


def load_house_xml_rows(repo_root: Path, path: Path, *, source_kind: str) -> list[dict[str, Any]]:
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return []

    rows = []
    for index, member in enumerate(root.findall("./members/member")):
        member_info = member.find("member-info")
        if member_info is None:
            continue
        state_element = member_info.find("state")
        state = state_element.attrib.get("postal-code") if state_element is not None else None
        district = extract_house_xml_district(member, member_info)
        if not state or not district:
            continue
        rows.append(
            house_row(
                repo_root=repo_root,
                path=path,
                row_index=index,
                source_kind=source_kind,
                name=_text(member_info.find("official-name")) or _text(member_info.find("namelist")),
                bioguide=_text(member_info.find("bioguideID")),
                state=state,
                district=district,
                current=True,
            )
        )
    return rows


def house_row(
    *,
    repo_root: Path,
    path: Path,
    row_index: int,
    source_kind: str,
    name: str,
    bioguide: str,
    state: Any,
    district: Any,
    current: bool,
) -> dict[str, Any]:
    normalized_state = normalize_state(state)
    normalized_district = normalize_district(district)
    person_key = bioguide or f"{_slug(name)}:{normalized_state}:{normalized_district}"
    return {
        "row_id": f"{_rel(repo_root, path)}#{row_index}",
        "source_file": _rel(repo_root, path),
        "source_kind": source_kind,
        "name_display": name,
        "bioguide_id": bioguide,
        "chamber": "house",
        "state": normalized_state,
        "district": normalized_district,
        "current": current,
        "seat_key": seat_key(normalized_state, normalized_district),
        "person_key": person_key,
    }


def inspect_lookup_assumptions(repo_root: Path) -> dict[str, Any]:
    lookup_route = _safe_read_text(repo_root / "backend/app/api/lookup.py")
    search_route = _safe_read_text(repo_root / "backend/app/api/search.py")
    precomputed = _safe_read_text(repo_root / "backend/app/api/precomputed.py")
    schema = _safe_read_text(repo_root / "backend/migrations/0001_initial_schema.sql")
    zip_panel = _safe_read_text(repo_root / "frontend/components/ZipLookupPanel.js")
    page = _safe_read_text(repo_root / "frontend/app/page.js")
    seed = _safe_read_text(repo_root / "backend/app/etl/seed.py")
    current_refresh = _safe_read_text(repo_root / "backend/app/etl/current_congress_refresh.py")
    historical_refresh = _safe_read_text(repo_root / "backend/app/etl/historical_congress_refresh.py")

    return {
        "zip_lookup_implemented_in": [
            "backend/app/api/lookup.py",
            "backend/app/api/precomputed.py",
            "frontend/lib/api.js",
            "frontend/components/ZipLookupPanel.js",
        ],
        "search_implemented_in": ["backend/app/api/search.py", "backend/app/api/precomputed.py"],
        "zip_treated_as_unique": {
            "detected": "zip TEXT PRIMARY KEY" in schema,
            "evidence": "backend/migrations/0001_initial_schema.sql defines zip_district_map.zip as PRIMARY KEY.",
        },
        "lookup_returns_single_district": {
            "detected": "_get_db_zip_record" in precomputed and "next((row for row in FALLBACK_FIXTURE_DATA.zip_district_map" in precomputed,
            "evidence": "DB lookup uses one zip_record; fallback uses next(...) for first matching fixture ZIP row.",
        },
        "house_member_selection_uses_state_plus_district": {
            "detected": "state = %s AND district = %s" in precomputed,
            "evidence": "backend/app/api/precomputed.py filters House rows by chamber, state, and district.",
        },
        "house_member_selection_order_by_id_limit_1": {
            "detected": "ORDER BY id\n        LIMIT 1" in precomputed or "ORDER BY id LIMIT 1" in precomputed,
            "evidence": "backend/app/api/precomputed.py selects one House row using ORDER BY id LIMIT 1.",
        },
        "senators_selected_by_state_only": {
            "detected": "WHERE chamber = 'senate' AND state = %s" in precomputed,
            "evidence": "Senate rows are selected by state only.",
        },
        "supported_zips_fixture_or_sample_driven": {
            "detected": '"data_source": "fixtures"' in precomputed and "FALLBACK_FIXTURE_DATA.zip_district_map" in precomputed,
            "evidence": "/lookup/zips returns fixture fallback mappings when DB rows are unavailable.",
        },
        "fallback_sample_zip_risk": {
            "detected": "FALLBACK_FIXTURE_DATA.zip_district_map" in precomputed and "data_source" in zip_panel,
            "evidence": "Frontend displays loaded ZIP mappings from the returned data_source, including fixtures.",
        },
        "frontend_default_zip": {
            "detected": 'const DEFAULT_ZIP = "27701"' in zip_panel,
            "evidence": "ZipLookupPanel auto-runs default ZIP 27701 on mount.",
        },
        "frontend_single_mapping_copy": {
            "detected": "maps to" in zip_panel,
            "evidence": "ZipLookupPanel renders `ZIP ... maps to state-district`.",
        },
        "frontend_auto_selects_house_profile": {
            "detected": "onSelectLegislator?.(payload.house_rep)" in zip_panel,
            "evidence": "Successful ZIP lookup auto-selects the returned House representative when present.",
        },
        "frontend_sample_profile_label": {
            "detected": "Sample profile shown until you search your ZIP" in page,
            "evidence": "Home page labels the initial default profile as sample before user lookup/search.",
        },
        "empty_search_exposes_loaded_legislators": {
            "detected": 'q: str = ""' in search_route and "WHERE (%s = '' OR lower(name_display) LIKE %s)" in precomputed,
            "evidence": "Empty q is allowed and DB query returns all legislators when q is empty.",
        },
        "etl_zip_bundle_dedupes_by_zip": {
            "detected": 'key="zip"' in seed and 'key="zip"' in current_refresh and 'key="zip"' in historical_refresh,
            "evidence": "Seed and refresh bundle merges dedupe zip_district_map rows by ZIP.",
        },
        "route_file_contains_lookup_zip": "/lookup/zip/{zip_code}" in lookup_route,
    }


def build_zip_inventory(*, zip_rows: list[dict[str, Any]]) -> dict[str, Any]:
    duplicate_groups = {
        key: grouped
        for key, grouped in group_rows(zip_rows, lambda row: row["mapping_key"]).items()
        if key and len(grouped) > 1
    }
    return {
        "total_mapping_rows": len(zip_rows),
        "unique_zips": len({row["zip"] for row in zip_rows if row["zip"]}),
        "fixture_only_mapping_rows": sum(1 for row in zip_rows if row["fixture_only"]),
        "non_fixture_mapping_rows": sum(1 for row in zip_rows if not row["fixture_only"]),
        "counts_by_zip": dict(sorted(Counter(row["zip"] for row in zip_rows if row["zip"]).items())),
        "counts_by_state": dict(sorted(Counter(row["state"] for row in zip_rows if row["state"]).items())),
        "counts_by_district": dict(sorted(Counter(seat_key(row["state"], row["district"]) for row in zip_rows if row["state"] and row["district"]).items())),
        "counts_by_source_file": dict(sorted(Counter(row["source_file"] for row in zip_rows).items())),
        "counts_by_source_kind": dict(sorted(Counter(row["source_kind"] for row in zip_rows).items())),
        "duplicate_identical_mappings": [
            {
                "mapping_key": key,
                "count": len(grouped),
                "source_files": sorted({row["source_file"] for row in grouped}),
            }
            for key, grouped in sorted(duplicate_groups.items())
        ],
        "missing_state_rows": [compact_zip_row(row) for row in zip_rows if row["missing_state"]],
        "missing_district_rows": [compact_zip_row(row) for row in zip_rows if row["missing_district"]],
        "invalid_district_rows": [compact_zip_row(row) for row in zip_rows if row["district"] and not row["valid_district"]],
        "invalid_state_rows": [compact_zip_row(row) for row in zip_rows if row["state"] and not row["valid_state"]],
        "invalid_zip_rows": [compact_zip_row(row) for row in zip_rows if row["zip"] and not row["valid_zip"]],
        "fixture_vs_non_fixture_sources": {
            "fixture_sources": sorted({row["source_file"] for row in zip_rows if row["fixture_only"]}),
            "non_fixture_sources": sorted({row["source_file"] for row in zip_rows if not row["fixture_only"]}),
        },
    }


def build_ambiguity_findings(*, zip_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_zip = group_rows(zip_rows, lambda row: row["zip"])
    multi_district = {}
    multi_state = {}
    for zip_code, rows in sorted(rows_by_zip.items()):
        if not zip_code:
            continue
        districts = sorted({seat_key(row["state"], row["district"]) for row in rows if row["state"] and row["district"]})
        states = sorted({row["state"] for row in rows if row["state"]})
        if len(districts) > 1:
            multi_district[zip_code] = districts
        if len(states) > 1:
            multi_state[zip_code] = states
    return {
        "one_zip_one_district_assumption_detected": True,
        "multi_district_zips": multi_district,
        "multi_state_zips": multi_state,
        "split_zip_rows": [
            compact_zip_row(row)
            for row in zip_rows
            if row["zip"] in multi_district or row["zip"] in multi_state
        ],
        "address_level_resolution_implemented": False,
        "detection_limit": (
            "Only multiple mappings present in repository/local-accessible files are detectable here; "
            "address-level split-ZIP coverage is not represented."
        ),
    }


def build_house_match_findings(*, zip_rows: list[dict[str, Any]], house_rows: list[dict[str, Any]]) -> dict[str, Any]:
    current_house_by_seat = group_rows(
        [row for row in house_rows if row["current"] and row["state"] and row["district"]],
        lambda row: row["seat_key"],
    )
    no_match = []
    multiple = []
    per_mapping = []
    for row in zip_rows:
        if not row["state"] or not row["district"] or not row["valid_state"] or not row["valid_district"]:
            match_rows: list[dict[str, Any]] = []
        else:
            match_rows = current_house_by_seat.get(seat_key(row["state"], row["district"]), [])
        unique_people = sorted({match["person_key"] for match in match_rows})
        record = {
            **compact_zip_row(row),
            "matching_current_house_source_rows": len(match_rows),
            "matching_current_house_people": len(unique_people),
            "matching_house_examples": [
                {
                    "name_display": match["name_display"],
                    "bioguide_id": match["bioguide_id"],
                    "source_file": match["source_file"],
                }
                for match in sorted(match_rows, key=lambda item: (item["person_key"], item["source_file"]))[:5]
            ],
        }
        per_mapping.append(record)
        if not match_rows:
            no_match.append(record)
        if len(unique_people) > 1:
            multiple.append(record)
    return {
        "local_house_rows_inspected": len(house_rows),
        "unique_current_house_seats_inspected": len(current_house_by_seat),
        "zip_rows_without_matching_local_house_legislator": no_match,
        "zip_rows_with_multiple_matching_current_house_legislators": multiple,
        "per_mapping_house_match_summary": per_mapping,
        "matching_limit": (
            "Local House matches are repository/local-accessible rows only; this does not certify production "
            "currentness or loaded production seat coverage."
        ),
    }


def build_warning_catalog(
    *,
    lookup_assumptions: dict[str, Any],
    inventory: dict[str, Any],
    ambiguity: dict[str, Any],
    house_matches: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    catalog = [
        warning_item(
            "one_zip_one_district_assumption",
            lookup_assumptions["zip_treated_as_unique"]["detected"] or ambiguity["one_zip_one_district_assumption_detected"],
            "One-ZIP-one-district assumption is present in schema and lookup behavior.",
        ),
        warning_item(
            "split_zips_detected",
            bool(ambiguity["multi_district_zips"]),
            f"Split ZIPs detected in local mappings: {json.dumps(ambiguity['multi_district_zips'], sort_keys=True)}.",
        ),
        warning_item(
            "multi_state_zips_detected",
            bool(ambiguity["multi_state_zips"]),
            f"Multi-state ZIPs detected in local mappings: {json.dumps(ambiguity['multi_state_zips'], sort_keys=True)}.",
        ),
        warning_item(
            "duplicate_mappings",
            bool(inventory["duplicate_identical_mappings"]),
            "Duplicate identical ZIP/state/district mappings are present across local source files.",
        ),
        warning_item(
            "missing_state_or_district",
            bool(inventory["missing_state_rows"] or inventory["missing_district_rows"]),
            "ZIP rows missing state or district are present.",
        ),
        warning_item(
            "invalid_district_values",
            bool(inventory["invalid_district_rows"]),
            "ZIP rows with invalid district values are present.",
        ),
        warning_item(
            "no_matching_house_legislator",
            bool(house_matches["zip_rows_without_matching_local_house_legislator"]),
            "ZIP rows without a matching local current House legislator are present.",
        ),
        warning_item(
            "multiple_matching_current_house_legislators",
            bool(house_matches["zip_rows_with_multiple_matching_current_house_legislators"]),
            "ZIP rows with multiple matching current House legislators are present in local metadata.",
        ),
        warning_item(
            "fixture_only_zip_mappings",
            inventory["fixture_only_mapping_rows"] > 0 and inventory["non_fixture_mapping_rows"] == 0,
            "All repository/local ZIP mappings are fixture-only and must not be treated as production coverage.",
        ),
        warning_item(
            "fallback_sample_zip_risk",
            lookup_assumptions["fallback_sample_zip_risk"]["detected"],
            "Fallback/sample ZIP behavior can be mistaken for production coverage without explicit labeling.",
        ),
        warning_item(
            "production_vs_local_ambiguity",
            True,
            "Production-vs-local ambiguity remains: this report does not query production credentials or production tables.",
        ),
        warning_item(
            "address_level_resolution_not_implemented",
            not ambiguity["address_level_resolution_implemented"],
            "Address-level district resolution is not implemented in this milestone.",
        ),
    ]
    return catalog, [item["message"] for item in catalog if item["active"]]


def public_lookup_risk_analysis() -> list[str]:
    return [
        "ZIP-only lookup can be wrong for split ZIPs because a ZIP can contain addresses from multiple House districts.",
        "A one-ZIP-one-district table cannot safely scale nationally without ambiguity detection and user-facing handling.",
        "Address-level lookup or an ambiguity UI is needed before national ZIP rollout.",
        "Fallback/sample ZIP mappings must be clearly labeled so fixture coverage is not mistaken for production coverage.",
        "Current NC fixture behavior should not be generalized to national coverage or address-accurate representation.",
        "Auto-selecting a House profile from an ambiguous ZIP would overstate what the ZIP evidence can prove.",
    ]


def expansion_gates() -> list[str]:
    return [
        "No auto-select House member when a ZIP maps to multiple districts.",
        "No national ZIP dataset without source, retrieval date, coverage date, and version metadata.",
        "No unsupported ZIP fallback that appears as production coverage.",
        "No ambiguous ZIP result without user-facing ambiguity messaging.",
        "No district match unless current House member metadata passes identity/currentness gates.",
        "No Senate state selection without currentness, seat, or class metadata caveats.",
    ]


def no_go_items() -> list[str]:
    return [
        "Do not treat this local ZIP report as production coverage truth.",
        "Do not download or ingest national ZIP data in this milestone.",
        "Do not mutate local or production databases.",
        "Do not change public lookup or frontend product behavior in this milestone.",
        "Do not implement address-level district resolution here.",
        "Do not auto-select a House member from split or ambiguous ZIP evidence.",
    ]


def sources_inspected(repo_root: Path, *, zip_rows: list[dict[str, Any]], house_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    static_sources = [
        ("backend_zip_lookup_routes", "backend/app/api/lookup.py", "ZIP lookup and supported ZIP route definitions."),
        ("backend_search_routes", "backend/app/api/search.py", "Legislator search route and default empty query."),
        ("backend_lookup_helpers", "backend/app/api/precomputed.py", "DB and fallback ZIP lookup, House selection, Senate selection, and supported ZIP helpers."),
        ("schema", "backend/migrations/0001_initial_schema.sql", "zip_district_map primary-key and state/district column constraints."),
        ("frontend_zip_lookup", "frontend/components/ZipLookupPanel.js", "Default ZIP, result copy, supported ZIP copy, and auto-select behavior."),
        ("frontend_home", "frontend/app/page.js", "Sample-profile copy around default profile state."),
        ("etl_seed_import", "backend/app/etl/seed.py", "ZIP mapping insert/copy and bundle dedupe behavior."),
        ("etl_congress_adapter", "backend/app/etl/congress_adapter.py", "ZIP map loading from source directory."),
        ("etl_house_clerk_adapter", "backend/app/etl/house_clerk_adapter.py", "House member state/district parsing and ZIP map loading."),
        ("etl_senate_xml_adapter", "backend/app/etl/senate_xml_adapter.py", "Senate member state handling and ZIP map loading."),
        ("etl_refresh_merge", "backend/app/etl/current_congress_refresh.py; backend/app/etl/historical_congress_refresh.py", "Refresh bundle ZIP dedupe by ZIP."),
    ]
    sources = [
        {"source_kind": kind, "path": path, "exists": all((repo_root / part.strip()).exists() for part in path.split(";")), "notes": notes}
        for kind, path, notes in static_sources
    ]
    sources.extend(
        {
            "source_kind": "zip_district_map",
            "path": path,
            "exists": True,
            "row_count": count,
            "notes": "Repository/local ZIP mapping file.",
        }
        for path, count in sorted(Counter(row["source_file"] for row in zip_rows).items())
    )
    sources.extend(
        {
            "source_kind": "local_house_metadata",
            "path": path,
            "exists": True,
            "row_count": count,
            "notes": "Local House metadata source used only for deterministic ZIP-to-House match checks.",
        }
        for path, count in sorted(Counter(row["source_file"] for row in house_rows).items())
    )
    return sources


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ZIP and District Ambiguity Hardening V1",
        "",
        "## Summary",
        "",
        report["scope"]["coverage_statement"],
        "",
        f"- Read-only: {_yes_no(report['scope']['read_only'])}",
        f"- Requires production credentials: {_yes_no(report['scope']['requires_production_credentials'])}",
        f"- ZIP mapping rows: {report['summary']['zip_mapping_rows']}",
        f"- Unique ZIPs: {report['summary']['unique_zips']}",
        f"- Fixture-only mapping rows: {report['summary']['fixture_only_mapping_rows']}",
        f"- Non-fixture mapping rows: {report['summary']['non_fixture_mapping_rows']}",
        f"- Warnings emitted: {report['summary']['warnings_emitted']}",
        "",
        "Highest ZIP/district findings:",
    ]
    lines.extend(f"- {item}" for item in report["summary"]["highest_findings"])
    lines.extend(["", "## Sources Inspected", ""])
    lines.extend(
        markdown_table(
            ["source_kind", "path", "exists", "row_count", "notes"],
            report["sources_inspected"],
        )
    )
    lines.extend(["", "## Current Lookup Assumption Map", ""])
    assumptions = report["current_lookup_assumption_map"]
    assumption_rows = []
    for key, value in assumptions.items():
        if isinstance(value, dict):
            assumption_rows.append({"assumption": key, "detected": _yes_no(value.get("detected")), "evidence": value.get("evidence", "")})
        else:
            assumption_rows.append({"assumption": key, "detected": "", "evidence": value})
    lines.extend(markdown_table(["assumption", "detected", "evidence"], assumption_rows))

    inventory = report["zip_mapping_inventory"]
    lines.extend(["", "## ZIP Mapping Inventory", ""])
    lines.extend(
        [
            f"- Total mapping rows: {inventory['total_mapping_rows']}",
            f"- Unique ZIPs: {inventory['unique_zips']}",
            f"- Fixture-only rows: {inventory['fixture_only_mapping_rows']}",
            f"- Non-fixture rows: {inventory['non_fixture_mapping_rows']}",
            f"- Counts by ZIP: `{json.dumps(inventory['counts_by_zip'], sort_keys=True)}`",
            f"- Counts by state: `{json.dumps(inventory['counts_by_state'], sort_keys=True)}`",
            f"- Counts by district: `{json.dumps(inventory['counts_by_district'], sort_keys=True)}`",
            f"- Counts by source kind: `{json.dumps(inventory['counts_by_source_kind'], sort_keys=True)}`",
            f"- Duplicate identical mappings: `{json.dumps(inventory['duplicate_identical_mappings'], sort_keys=True)}`",
            f"- Missing state rows: {len(inventory['missing_state_rows'])}",
            f"- Missing district rows: {len(inventory['missing_district_rows'])}",
            f"- Invalid district rows: {len(inventory['invalid_district_rows'])}",
        ]
    )

    lines.extend(["", "## Ambiguity Findings", ""])
    ambiguity = report["ambiguity_findings"]
    lines.extend(
        [
            f"- One-ZIP-one-district assumption detected: {_yes_no(ambiguity['one_zip_one_district_assumption_detected'])}",
            f"- ZIPs mapping to multiple districts: `{json.dumps(ambiguity['multi_district_zips'], sort_keys=True)}`",
            f"- ZIPs mapping to multiple states: `{json.dumps(ambiguity['multi_state_zips'], sort_keys=True)}`",
            f"- Address-level resolution implemented: {_yes_no(ambiguity['address_level_resolution_implemented'])}",
            f"- Detection limit: {ambiguity['detection_limit']}",
        ]
    )
    lines.extend(["", "## House Member Match Findings", ""])
    house = report["house_member_match_findings"]
    lines.extend(
        [
            f"- Local House rows inspected: {house['local_house_rows_inspected']}",
            f"- Unique current House seats inspected: {house['unique_current_house_seats_inspected']}",
            f"- ZIP rows without matching local House legislator: {len(house['zip_rows_without_matching_local_house_legislator'])}",
            f"- ZIP rows with multiple matching current House legislators: {len(house['zip_rows_with_multiple_matching_current_house_legislators'])}",
            f"- Matching limit: {house['matching_limit']}",
        ]
    )
    if house["zip_rows_without_matching_local_house_legislator"]:
        lines.extend(["", "Rows without local House match:"])
        lines.extend(markdown_table(["zip", "state", "district", "source_file"], house["zip_rows_without_matching_local_house_legislator"]))
    if house["zip_rows_with_multiple_matching_current_house_legislators"]:
        lines.extend(["", "Rows with multiple local current House matches:"])
        lines.extend(markdown_table(["zip", "state", "district", "source_file", "matching_current_house_people"], house["zip_rows_with_multiple_matching_current_house_legislators"]))

    lines.extend(["", "## Public Lookup Risk Analysis", ""])
    lines.extend(f"- {item}" for item in report["public_lookup_risk_analysis"])
    lines.extend(["", "## Expansion Gates", ""])
    lines.extend(f"- {item}" for item in report["expansion_gates"])
    lines.extend(["", "## No-Go Items", ""])
    lines.extend(f"- {item}" for item in report["no_go_items"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in report["warnings"])
    lines.extend(["", "Warning catalog:"])
    lines.extend(markdown_table(["warning_key", "active", "message"], report["warning_catalog"]))
    lines.extend(["", "## Recommended Next Milestone", "", report["recommended_next_milestone"], ""])
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], *, repo_root: Path, markdown_out: Path, json_out: Path) -> None:
    markdown_path = _resolve_output(repo_root, markdown_out)
    json_path = _resolve_output(repo_root, json_out)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def extract_json_state_district(item: dict[str, Any]) -> tuple[str, str]:
    state = item.get("state")
    district = item.get("district")
    terms = item.get("terms")
    if isinstance(terms, dict):
        term_items = _as_list(terms.get("item"))
        if term_items:
            latest = term_items[-1]
            if isinstance(latest, dict):
                state = state or latest.get("stateCode") or latest.get("state")
                district = district or latest.get("district")
    return normalize_state(state), normalize_district(district)


def extract_house_xml_district(member: ElementTree.Element, member_info: ElementTree.Element) -> str:
    district_text = _text(member_info.find("district"))
    if district_text:
        return normalize_district(district_text)
    statedistrict = _text(member.find("statedistrict"))
    if statedistrict:
        digits = "".join(character for character in statedistrict if character.isdigit())
        if digits:
            return normalize_district(digits)
    return ""


def classify_zip_source(repo_root: Path, path: Path) -> str:
    rel = _rel(repo_root, path)
    if rel.startswith("backend/fixtures/"):
        return "fixture"
    if rel.startswith("backend/data_sources/"):
        return "local_source_cache"
    return "repository_local"


def is_fixture_path(repo_root: Path, path: Path) -> bool:
    return _rel(repo_root, path).startswith("backend/fixtures/")


def normalize_state(value: Any) -> str:
    cleaned = _clean(value)
    if not cleaned:
        return ""
    if cleaned in STATE_NAME_TO_CODE:
        return STATE_NAME_TO_CODE[cleaned]
    return cleaned.upper()


def normalize_chamber(value: Any) -> str:
    cleaned = _clean(value).lower()
    if cleaned in {"house", "h", "representative", "house of representatives"}:
        return "house"
    if cleaned in {"senate", "s", "senator"}:
        return "senate"
    return cleaned


def normalize_district(value: Any) -> str:
    cleaned = _clean(value)
    if not cleaned:
        return ""
    lowered = cleaned.lower()
    if lowered in AT_LARGE_DISTRICTS:
        return "00"
    if re.fullmatch(r"\d+", cleaned):
        return cleaned.zfill(2)
    return cleaned


def is_valid_house_district(value: str) -> bool:
    if not value:
        return False
    if value in {"00"}:
        return True
    return bool(re.fullmatch(r"\d{2}", value))


def compact_zip_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "zip": row.get("zip", ""),
        "state": row.get("state", ""),
        "district": row.get("district", ""),
        "source_file": row.get("source_file", ""),
    }


def warning_item(key: str, active: bool, message: str) -> dict[str, Any]:
    return {"warning_key": key, "active": bool(active), "message": message}


def group_rows(rows: list[dict[str, Any]], key_func) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(key_func(row) or "")].append(row)
    return dict(grouped)


def mapping_key(zip_code: str, state: str, district: str) -> str:
    if not zip_code and not state and not district:
        return ""
    return f"{zip_code}:{state}:{district}"


def seat_key(state: str, district: str) -> str:
    return f"{state}-{district}" if state and district else ""


def markdown_table(headers: list[str], rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(format_cell(row.get(header, "")) for header in headers) + " |")
    return lines


def format_cell(value: Any) -> str:
    if isinstance(value, bool):
        value = _yes_no(value)
    elif isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True)
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _text(element: ElementTree.Element | None) -> str:
    return _clean(element.text if element is not None else "")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_output(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    raise SystemExit(main())
