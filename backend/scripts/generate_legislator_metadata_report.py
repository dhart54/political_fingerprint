"""Generate a read-only local legislator metadata hardening report.

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


REPORT_MD = Path("docs/review_packets/legislator_metadata_hardening_v1.md")
REPORT_JSON = Path("docs/review_packets/legislator_metadata_hardening_v1.json")
COVERAGE_STATEMENT = (
    "This is repository/local-accessible metadata only. It is not production "
    "coverage truth unless a future read-only production report is generated "
    "with credentials."
)
SUPPORTED_START_YEAR = 2025
SUPPORTED_END_YEAR = 2026
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
HOUSE_STYLE_DISTRICT_VALUES = {"00", "0", "at large", "at-large", "delegate", "resident commissioner"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD)
    parser.add_argument("--json-out", type=Path, default=REPORT_JSON)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)
    write_outputs(
        report,
        repo_root=repo_root,
        markdown_out=args.markdown_out,
        json_out=args.json_out,
    )
    print(f"Wrote {args.markdown_out}")
    print(f"Wrote {args.json_out}")
    return 0


def build_report(repo_root: Path) -> dict[str, Any]:
    rows, source_summaries = collect_legislator_rows(repo_root)
    zip_inventory = inspect_zip_mappings(repo_root, rows)
    lookup_implications = inspect_lookup_assumptions(repo_root)
    identity = identity_completeness(rows)
    chamber_quality = chamber_state_district_quality(rows)
    currentness = currentness_term_boundary(rows)
    conflicts = duplicate_conflicts(rows, zip_inventory)
    senate = senate_metadata_readiness(rows)
    warnings = generate_warnings(
        identity=identity,
        chamber_quality=chamber_quality,
        currentness=currentness,
        conflicts=conflicts,
        zip_inventory=zip_inventory,
        senate=senate,
    )
    expansion_gates = [
        "No broad House rollout unless each current House member has stable Bioguide, state, district, currentness, and source coverage status.",
        "No Senate rollout unless Senate identity includes reliable Bioguide/LIS handling and chamber-specific caveats.",
        "No national ZIP rollout until split-ZIP/address ambiguity is handled.",
        "No profile auto-load from fallback/sample data without a clear user-facing sample or coverage label.",
        "No cross-Congress comparison unless member identity and term boundaries are reliable.",
    ]
    no_go_items = [
        "Do not treat this local report as production coverage truth.",
        "Do not fix metadata by editing fixture or production-like data in this milestone.",
        "Do not use fallback/sample rows as unlabeled public coverage.",
        "Do not auto-select a House member from split or ambiguous ZIP evidence.",
        "Do not publish Senate reads until LIS/Bioguide handling and Senate metadata caveats are reliable.",
        "Do not infer cross-time movement from rows whose term boundaries are ambiguous.",
    ]

    return {
        "schema_version": "legislator_metadata_hardening_v1",
        "scope": {
            "read_only": True,
            "requires_production_credentials": False,
            "coverage_statement": COVERAGE_STATEMENT,
            "supported_current_window": {
                "start_year": SUPPORTED_START_YEAR,
                "end_year": SUPPORTED_END_YEAR,
            },
        },
        "summary": {
            "sources_inspected": len(source_summaries),
            "legislator_or_member_rows": len(rows),
            "warnings_emitted": len(warnings),
            "highest_findings": [
                "Local app-style legislator rows do not persist Senate LIS IDs, slugs, or term boundaries.",
                "Congress.gov member cache rows are useful identity sources but do not contain app IDs, slugs, LIS IDs, or explicit current flags.",
                "Senate XML member cache contains LIS and Bioguide IDs, but the normalized app legislator shape drops LIS before persistence.",
                "ZIP fixture mappings are fixture-only and include a locally detectable split-ZIP conflict for ZIP 27601.",
                "Lookup/search code assumes one ZIP record maps to one district and empty search can expose all loaded legislators.",
            ],
        },
        "sources_inspected": source_summaries,
        "identity_completeness": identity,
        "chamber_state_district_quality": chamber_quality,
        "currentness_term_boundary": currentness,
        "duplicate_conflict_findings": conflicts,
        "zip_district_lookup_implications": {
            **zip_inventory,
            "lookup_safety_implications": lookup_implications,
        },
        "senate_metadata_readiness": senate,
        "warnings": warnings,
        "expansion_gates": expansion_gates,
        "no_go_items": no_go_items,
        "recommended_next_milestone": (
            "ZIP and district ambiguity hardening, followed by a production read-only "
            "metadata companion report before any broad House, Senate, or national ZIP rollout."
        ),
    }


def collect_legislator_rows(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    source_summaries: list[dict[str, Any]] = []

    loaders = [
        ("fixture_legislators", repo_root / "backend/fixtures/legislators.json", load_app_fixture_legislators),
        ("congress_sample_members", repo_root / "backend/fixtures/congress_sample/members.json", load_congress_sample_members),
        ("congress_gov_member_cache", repo_root / "backend/data_sources/congress/members", load_congress_member_cache),
        ("house_clerk_member_xml", repo_root / "backend/fixtures/house_clerk_sample/members.xml", load_house_member_xml_file),
        ("senate_member_xml", repo_root / "backend/fixtures/senate_xml_sample/members.xml", load_senate_member_xml_file),
    ]
    for source_kind, path, loader in loaders:
        loaded = loader(repo_root, path)
        rows.extend(loaded)
        source_summaries.append(source_summary(repo_root, source_kind, path, loaded))

    for path in sorted((repo_root / "backend/data_sources/house_clerk").glob("**/members.xml")):
        loaded = load_house_member_xml_file(repo_root, path)
        rows.extend(loaded)
        source_summaries.append(source_summary(repo_root, "house_clerk_member_xml", path, loaded))

    for path in sorted((repo_root / "backend/data_sources/senate_xml").glob("**/members.xml")):
        loaded = load_senate_member_xml_file(repo_root, path)
        rows.extend(loaded)
        source_summaries.append(source_summary(repo_root, "senate_member_xml", path, loaded))

    source_summaries.append(
        {
            "source_kind": "schema",
            "path": "backend/migrations/0001_initial_schema.sql",
            "exists": (repo_root / "backend/migrations/0001_initial_schema.sql").exists(),
            "row_count": None,
            "notes": "Stored legislators table has id, bioguide_id, name_display, chamber, state, district, party, and in_office; no LIS, slug, or term fields.",
        }
    )
    source_summaries.append(
        {
            "source_kind": "lookup_routes",
            "path": "backend/app/api/lookup.py; backend/app/api/search.py; backend/app/api/precomputed.py",
            "exists": True,
            "row_count": None,
            "notes": "Inspected ZIP lookup, supported ZIPs, legislator search, fallback serialization, and DB lookup helpers.",
        }
    )
    source_summaries.append(
        {
            "source_kind": "frontend_profile_lookup",
            "path": "frontend/app/page.js; frontend/components/ZipLookupPanel.js; frontend/lib/api.js",
            "exists": True,
            "row_count": None,
            "notes": "Inspected default profile, default ZIP lookup, supported ZIP labels, search API use, and visible metadata assumptions.",
        }
    )
    return rows, source_summaries


def source_summary(repo_root: Path, source_kind: str, path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_kind": source_kind,
        "path": _rel(repo_root, path),
        "exists": path.exists(),
        "row_count": len(rows),
        "notes": source_notes(source_kind),
    }


def source_notes(source_kind: str) -> str:
    notes = {
        "fixture_legislators": "App-style fixture rows with persisted ids but no slug, LIS, or term boundaries.",
        "congress_sample_members": "Sample Congress.gov-shaped rows normalized by the congress adapter.",
        "congress_gov_member_cache": "Local Congress.gov member cache; not proof of loaded app or production rows.",
        "house_clerk_member_xml": "House member XML includes Bioguide, state, district, party, and names; app ids are generated during normalization.",
        "senate_member_xml": "Senate member XML includes LIS and Bioguide IDs, state, party, and names; no district and no term boundaries.",
    }
    return notes.get(source_kind, "")


def load_app_fixture_legislators(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    data = _as_list(_load_json(path))
    rows = []
    for row in data:
        if not isinstance(row, dict):
            continue
        rows.append(
            normalize_row(
                repo_root=repo_root,
                source_kind="fixture_legislators",
                path=path,
                raw=row,
                app_internal_id=row.get("id"),
                bioguide_id=row.get("bioguide_id"),
                lis_id=row.get("lis_id"),
                display_name=row.get("name_display"),
                chamber=row.get("chamber"),
                state=row.get("state"),
                district=row.get("district"),
                party=row.get("party"),
                in_office=row.get("in_office"),
                term_start_year=row.get("term_start_year"),
                term_end_year=row.get("term_end_year"),
                slug=row.get("slug"),
            )
        )
    return rows


def load_congress_sample_members(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    data = _as_list(_load_json(path))
    rows = []
    for row in data:
        if not isinstance(row, dict):
            continue
        display_name = row.get("directOrderName") or row.get("name")
        rows.append(
            normalize_row(
                repo_root=repo_root,
                source_kind="congress_sample_members",
                path=path,
                raw=row,
                app_internal_id=_to_legislator_id(display_name),
                bioguide_id=row.get("bioguideId"),
                lis_id=row.get("lisId"),
                display_name=display_name,
                chamber=row.get("chamber"),
                state=row.get("state"),
                district=row.get("district"),
                party=row.get("partyCode") or row.get("partyName"),
                in_office=row.get("currentMember"),
                slug=row.get("slug"),
            )
        )
    return rows


def load_congress_member_cache(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    rows = []
    for member_path in sorted(path.glob("*.json")) if path.exists() else []:
        data = _load_json(member_path)
        members = _as_list(data.get("members") if isinstance(data, dict) else data)
        for row in members:
            if not isinstance(row, dict):
                continue
            terms = _term_items(row)
            latest_term = _latest_term(terms)
            chamber = latest_term.get("chamber") if latest_term else row.get("chamber")
            state = _state_code(row.get("state"))
            rows.append(
                normalize_row(
                    repo_root=repo_root,
                    source_kind="congress_gov_member_cache",
                    path=member_path,
                    raw=row,
                    app_internal_id=row.get("id"),
                    bioguide_id=row.get("bioguideId"),
                    lis_id=row.get("lisId"),
                    display_name=row.get("name"),
                    chamber=chamber,
                    state=state,
                    district=row.get("district"),
                    party=row.get("partyName"),
                    in_office=row.get("currentMember"),
                    term_start_year=latest_term.get("startYear") if latest_term else None,
                    term_end_year=latest_term.get("endYear") if latest_term else None,
                    slug=row.get("slug"),
                    update_date=row.get("updateDate"),
                )
            )
    return rows


def load_house_member_xml_file(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        return []
    rows = []
    for member in root.findall("./members/member"):
        member_info = member.find("member-info")
        if member_info is None:
            continue
        display_name = _first_text(member_info, ("official-name", "formal-name", "namelist"))
        state_element = member_info.find("state")
        state = state_element.attrib.get("postal-code") if state_element is not None else None
        rows.append(
            normalize_row(
                repo_root=repo_root,
                source_kind="house_clerk_member_xml",
                path=path,
                raw={},
                app_internal_id=None,
                bioguide_id=_text(member_info.find("bioguideID")),
                lis_id=None,
                display_name=display_name,
                chamber="house",
                state=state,
                district=extract_house_xml_district(member, member_info),
                party=_text(member_info.find("party")),
                in_office=True,
            )
        )
    return rows


def load_senate_member_xml_file(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        return []
    elements = root.findall("./members/member")
    if not elements:
        elements = root.findall("./senator")
    rows = []
    for member in elements:
        display_name = extract_senate_xml_name(member)
        rows.append(
            normalize_row(
                repo_root=repo_root,
                source_kind="senate_member_xml",
                path=path,
                raw={},
                app_internal_id=None,
                bioguide_id=_text(member.find("bioguide_id")) or _text(member.find("bioguideId")),
                lis_id=_text(member.find("lis_member_id")) or member.attrib.get("lis_member_id"),
                display_name=display_name,
                chamber="senate",
                state=_text(member.find("state")),
                district=None,
                party=_text(member.find("party")),
                in_office=parse_bool(_text(member.find("in_office"))) if member.find("in_office") is not None else None,
                seat_rank=_text(member.find("stateRank")),
            )
        )
    return rows


def normalize_row(
    *,
    repo_root: Path,
    source_kind: str,
    path: Path,
    raw: dict[str, Any],
    app_internal_id: Any,
    bioguide_id: Any,
    lis_id: Any,
    display_name: Any,
    chamber: Any,
    state: Any,
    district: Any,
    party: Any,
    in_office: Any,
    term_start_year: Any = None,
    term_end_year: Any = None,
    slug: Any = None,
    seat_rank: Any = None,
    seat_class: Any = None,
    update_date: Any = None,
) -> dict[str, Any]:
    display = _clean(display_name)
    chamber_raw = _clean(chamber)
    normalized_chamber = normalize_chamber(chamber_raw)
    state_code = _state_code(state)
    district_value = normalize_district(district)
    normalized_slug = _slug(display)
    return {
        "source_kind": source_kind,
        "source_path": _rel(repo_root, path),
        "app_internal_id": _clean(app_internal_id),
        "generated_app_id": _to_legislator_id(display),
        "bioguide_id": _clean(bioguide_id),
        "lis_id": _clean(lis_id),
        "display_name": display,
        "normalized_slug": _clean(slug) or normalized_slug,
        "source_slug_present": _has_text(slug),
        "chamber_raw": chamber_raw,
        "chamber": normalized_chamber,
        "state": state_code,
        "district": district_value,
        "party": normalize_party(party),
        "in_office": parse_bool(in_office),
        "term_start_year": parse_int(term_start_year),
        "term_end_year": parse_int(term_end_year),
        "currentness": infer_currentness(in_office, term_start_year, term_end_year),
        "seat_rank": _clean(seat_rank),
        "seat_class": _clean(seat_class),
        "update_date": _clean(update_date),
        "raw_field_keys": sorted(str(key) for key in raw.keys()),
    }


def identity_completeness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = []
    for source_kind in sorted({row["source_kind"] for row in rows}):
        source_rows = [row for row in rows if row["source_kind"] == source_kind]
        senators = [row for row in source_rows if row["chamber"] == "senate"]
        house = [row for row in source_rows if row["chamber"] == "house"]
        by_source.append(
            {
                "source_kind": source_kind,
                "rows": len(source_rows),
                "missing_app_internal_id": count_missing(source_rows, "app_internal_id"),
                "missing_bioguide_id": count_missing(source_rows, "bioguide_id"),
                "missing_lis_id_for_senators": count_missing(senators, "lis_id"),
                "missing_display_name": count_missing(source_rows, "display_name"),
                "missing_persisted_slug": sum(1 for row in source_rows if not row["source_slug_present"]),
                "missing_chamber": count_missing(source_rows, "chamber"),
                "missing_state": count_missing(source_rows, "state"),
                "missing_house_district": count_missing(house, "district"),
                "missing_party": count_missing(source_rows, "party"),
                "missing_current_flag": sum(1 for row in source_rows if row["in_office"] is None),
                "missing_term_start": count_missing(source_rows, "term_start_year"),
                "missing_term_end": count_missing(source_rows, "term_end_year"),
                "duplicate_bioguide_ids": duplicate_count(source_rows, "bioguide_id"),
                "duplicate_app_internal_ids": duplicate_count(source_rows, "app_internal_id"),
                "duplicate_slugs": duplicate_count(source_rows, "normalized_slug"),
            }
        )
    return {
        "table": by_source,
        "notes": [
            "Persisted slugs are not present in inspected local metadata; app routing derives `leg_...` ids from display names.",
            "The stored app schema has no LIS or term-boundary columns.",
            "Missing Senate LIS counts are source-specific: Senate XML has LIS, while app fixture and Congress.gov cache rows do not.",
        ],
    }


def chamber_state_district_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = []
    for source_kind in sorted({row["source_kind"] for row in rows}):
        source_rows = [row for row in rows if row["source_kind"] == source_kind]
        house = [row for row in source_rows if row["chamber"] == "house"]
        senate = [row for row in source_rows if row["chamber"] == "senate"]
        by_source.append(
            {
                "source_kind": source_kind,
                "rows": len(source_rows),
                "unknown_chamber": sum(1 for row in source_rows if row["chamber"] not in {"house", "senate"}),
                "mixed_chamber_format_rows": sum(1 for row in source_rows if row["chamber_raw"] and row["chamber_raw"] != row["chamber"]),
                "house_rows_missing_district": count_missing(house, "district"),
                "senate_rows_with_house_style_district": sum(1 for row in senate if is_house_style_district(row["district"])),
                "invalid_state_values": sum(1 for row in source_rows if row["state"] not in VALID_STATE_CODES),
                "invalid_house_district_values": sum(1 for row in house if not is_valid_house_district(row["district"])),
                "at_large_house_districts": sum(1 for row in house if is_at_large_district(row["district"])),
                "senate_lis_gaps": count_missing(senate, "lis_id"),
                "senate_bioguide_gaps": count_missing(senate, "bioguide_id"),
            }
        )
    return {
        "table": by_source,
        "notes": [
            "Congress.gov chamber values use labels such as `House of Representatives`; the report normalizes those while counting format inconsistency.",
            "Senate districts should be absent or explicitly statewide in UI copy; numeric districts on Senate rows are flagged as House-style confusion.",
            "At-large House districts are recognized as `00`, `0`, or at-large labels.",
        ],
    }


def currentness_term_boundary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = []
    for source_kind in sorted({row["source_kind"] for row in rows}):
        source_rows = [row for row in rows if row["source_kind"] == source_kind]
        status_counts = Counter(row["currentness"] for row in source_rows)
        conflicts = [
            compact_row(row)
            for row in source_rows
            if current_flag_conflicts_with_terms(row)
        ][:20]
        by_source.append(
            {
                "source_kind": source_kind,
                "rows": len(source_rows),
                "inferred_current_or_recent": status_counts.get("inferred_current_or_recent", 0),
                "clearly_stale": status_counts.get("clearly_stale_before_supported_119", 0),
                "ambiguous_currentness": status_counts.get("ambiguous_no_end_year", 0)
                + status_counts.get("locally_current_flag_no_term_boundary", 0)
                + status_counts.get("missing_terms_and_current_flag", 0),
                "no_end_year_or_no_term_boundary": status_counts.get("ambiguous_no_end_year", 0)
                + status_counts.get("locally_current_flag_no_term_boundary", 0)
                + status_counts.get("missing_terms_and_current_flag", 0),
                "term_dates_before_supported_window": sum(
                    1
                    for row in source_rows
                    if row["term_end_year"] is not None and row["term_end_year"] < SUPPORTED_START_YEAR
                ),
                "in_office_term_conflicts": len(conflicts),
                "conflict_examples": conflicts,
            }
        )
    return {
        "table": by_source,
        "notes": [
            "Currentness is inferred from local fields only. No external network or production query is used.",
            "`ambiguous_no_end_year` is not treated as production current truth; it means the local row lacks an end year.",
            "Fixture and XML current flags without term boundaries are useful but insufficient for cross-Congress expansion gates.",
        ],
    }


def duplicate_conflicts(rows: list[dict[str, Any]], zip_inventory: dict[str, Any]) -> dict[str, Any]:
    same_bioguide = group_conflicts(rows, "bioguide_id", minimum=2)
    same_slug = group_conflicts(rows, "normalized_slug", minimum=2, person_key="bioguide_id")
    current_house_by_seat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    senate_by_state_rank: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["chamber"] == "house" and row["state"] and row["district"] and is_currentish(row):
            current_house_by_seat[f"{row['state']}-{row['district']}"].append(row)
        if row["chamber"] == "senate" and row["state"] and is_currentish(row):
            rank = row["seat_rank"] or row["seat_class"] or "missing_seat_rank_or_class"
            senate_by_state_rank[f"{row['state']}:{rank}"].append(row)
    house_seat_conflicts = compact_conflict_groups(current_house_by_seat)
    senate_ambiguity = compact_conflict_groups(senate_by_state_rank, person_key="bioguide_id")
    fixture_congress_disagreements = fixture_congress_cache_disagreements(rows)
    return {
        "same_bioguide_mapped_to_multiple_app_ids": same_bioguide,
        "same_slug_mapped_to_multiple_people": same_slug,
        "same_state_district_current_house_seat_multiple_members": house_seat_conflicts,
        "same_senate_state_seat_or_missing_class_ambiguity": senate_ambiguity,
        "zip_mappings_resolving_to_multiple_districts": zip_inventory["multi_district_zips_detected"],
        "fixtures_disagree_with_congress_gov_cache": fixture_congress_disagreements,
        "notes": [
            "Conflict groups include cross-source local metadata and may reflect fixture/sample overlap rather than production duplicates.",
            "Senate seat/class is not reliably represented in the inspected app schema; stateRank in Senate XML is reported when present.",
        ],
    }


def inspect_zip_mappings(repo_root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    zip_rows = []
    for path in sorted((repo_root / "backend/fixtures").glob("**/zip_district_map.json")):
        data = _as_list(_load_json(path))
        for item in data:
            if not isinstance(item, dict):
                continue
            state = _state_code(item.get("state"))
            district = normalize_district(item.get("district"))
            zip_rows.append(
                {
                    "path": _rel(repo_root, path),
                    "zip": _clean(item.get("zip")),
                    "state": state,
                    "district": district,
                    "fixture_only": True,
                    "valid_zip": bool(re.fullmatch(r"\d{5}", str(item.get("zip") or ""))),
                    "valid_state": state in VALID_STATE_CODES,
                    "valid_district": is_valid_house_district(district),
                }
            )
    districts_by_zip: dict[str, set[str]] = defaultdict(set)
    for row in zip_rows:
        districts_by_zip[row["zip"]].add(f"{row['state']}-{row['district']}")
    all_house_seats = {
        f"{row['state']}-{row['district']}"
        for row in rows
        if row["chamber"] == "house" and row["state"] and row["district"]
    }
    app_fixture_house_seats = {
        f"{row['state']}-{row['district']}"
        for row in rows
        if row["source_kind"] in {"fixture_legislators", "congress_sample_members", "house_clerk_member_xml"}
        and row["chamber"] == "house"
        and row["state"]
        and row["district"]
    }
    missing_any = [
        row for row in zip_rows
        if f"{row['state']}-{row['district']}" not in all_house_seats
    ]
    missing_app_fixture = [
        row for row in zip_rows
        if f"{row['state']}-{row['district']}" not in app_fixture_house_seats
    ]
    return {
        "paths": sorted({row["path"] for row in zip_rows}),
        "total_mapping_rows": len(zip_rows),
        "fixture_only_mapping_rows": sum(1 for row in zip_rows if row["fixture_only"]),
        "unique_zips": len(districts_by_zip),
        "multi_district_zips_detected": {
            zip_code: sorted(districts)
            for zip_code, districts in sorted(districts_by_zip.items())
            if len(districts) > 1
        },
        "invalid_zip_rows": [row for row in zip_rows if not row["valid_zip"]],
        "invalid_state_rows": [row for row in zip_rows if not row["valid_state"]],
        "invalid_district_rows": [row for row in zip_rows if not row["valid_district"]],
        "zip_rows_without_any_local_house_match": missing_any,
        "zip_rows_without_app_fixture_house_match": missing_app_fixture,
        "ambiguity_detection_limit": "Only multiple mappings present in local fixture files are detectable; address-level split ZIP coverage is not represented.",
    }


def inspect_lookup_assumptions(repo_root: Path) -> dict[str, Any]:
    precomputed = _safe_read_text(repo_root / "backend/app/api/precomputed.py")
    search = _safe_read_text(repo_root / "backend/app/api/search.py")
    zip_panel = _safe_read_text(repo_root / "frontend/components/ZipLookupPanel.js")
    page = _safe_read_text(repo_root / "frontend/app/page.js")
    return {
        "current_lookup_assumes": [
            "A ZIP resolves to a single `zip_district_map` row with one state and district.",
            "The House representative is selected by state and district with `ORDER BY id LIMIT 1`.",
            "Senators are selected by state; no seat/class or currentness caveat is exposed in the route payload.",
            "Fallback ZIP lookup uses the first matching fixture ZIP row and fixture legislators.",
        ],
        "one_zip_one_district_assumed": "zip_district_map has ZIP as primary key and code uses a single zip_record." if "zip_district_map" in precomputed else "not detected",
        "empty_search_exposes_all_loaded_legislators": "yes" if "WHERE (%s = '' OR lower(name_display) LIKE %s)" in precomputed and 'q: str = ""' in search else "unknown",
        "fallback_sample_data_risk": [
            "Backend supported ZIP responses include `data_source = fixtures` when DB reads are unavailable.",
            "Frontend default ZIP `27701` runs automatically.",
            "Frontend labels the default profile as sample until a ZIP/search selection, but ZIP result cards can still load fixture officials.",
        ],
        "user_facing_warnings_needed_before_national_expansion": [
            "Loaded coverage is not national coverage.",
            "ZIP-only lookup may be ambiguous; address-level resolution may be needed.",
            "Fixture/sample rows must be visibly labeled when they appear.",
            "Currentness and term-boundary status should be shown or used as a gate before auto-loading a profile.",
            "Senate identity should disclose LIS/Bioguide handling and missing seat/class metadata.",
        ],
        "frontend_default_zip_detected": "yes" if 'const DEFAULT_ZIP = "27701"' in zip_panel else "unknown",
        "frontend_sample_profile_label_detected": "yes" if "Sample profile shown until you search your ZIP" in page else "unknown",
    }


def senate_metadata_readiness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    senate_rows = [row for row in rows if row["chamber"] == "senate"]
    by_source = []
    for source_kind in sorted({row["source_kind"] for row in senate_rows}):
        source_rows = [row for row in senate_rows if row["source_kind"] == source_kind]
        by_source.append(
            {
                "source_kind": source_kind,
                "rows": len(source_rows),
                "missing_lis_id": count_missing(source_rows, "lis_id"),
                "missing_bioguide_id": count_missing(source_rows, "bioguide_id"),
                "missing_state": count_missing(source_rows, "state"),
                "missing_seat_rank_or_class": sum(1 for row in source_rows if not row["seat_rank"] and not row["seat_class"]),
                "xml_source_identity_rows": sum(1 for row in source_rows if row["source_kind"] == "senate_member_xml"),
                "senate_rows_with_house_style_district": sum(1 for row in source_rows if is_house_style_district(row["district"])),
            }
        )
    return {
        "table": by_source,
        "exists": {
            "senate_lis_id": any(_has_text(row["lis_id"]) for row in senate_rows),
            "bioguide_id": any(_has_text(row["bioguide_id"]) for row in senate_rows),
            "state": any(_has_text(row["state"]) for row in senate_rows),
            "seat_rank_or_class": any(_has_text(row["seat_rank"]) or _has_text(row["seat_class"]) for row in senate_rows),
            "senate_class": any(_has_text(row["seat_class"]) for row in senate_rows),
            "member_xml_source_identity": any(row["source_kind"] == "senate_member_xml" for row in senate_rows),
        },
        "metadata_chamber_readiness_risks": [
            "Normalized app legislators do not preserve LIS IDs even though Senate vote matching uses LIS internally.",
            "The app schema has no Senate seat/class field; Senate XML stateRank is not a full Senate class model.",
            "Nominations, treaties, and cloture are not vote-semantics decisions here, but they require chamber-specific metadata and source caveats before public Senate rollout.",
            "Senate XML member files provide useful local identity, but local files alone do not prove production mapping completeness.",
        ],
    }


def generate_warnings(
    *,
    identity: dict[str, Any],
    chamber_quality: dict[str, Any],
    currentness: dict[str, Any],
    conflicts: dict[str, Any],
    zip_inventory: dict[str, Any],
    senate: dict[str, Any],
) -> list[str]:
    warnings = [COVERAGE_STATEMENT]
    if sum(row["missing_bioguide_id"] for row in identity["table"]):
        warnings.append("Missing Bioguide IDs are present in local metadata sources.")
    if sum(row["missing_lis_id_for_senators"] for row in identity["table"]):
        warnings.append("Missing Senate LIS IDs are present for senator rows in one or more local sources.")
    if sum(row["missing_persisted_slug"] for row in identity["table"]):
        warnings.append("Persisted slugs are missing even though app routing derives slug-like legislator IDs from display names.")
    if sum(row["house_rows_missing_district"] for row in chamber_quality["table"]):
        warnings.append("House rows missing districts are present.")
    if sum(row["ambiguous_currentness"] for row in currentness["table"]):
        warnings.append("Ambiguous currentness is present because rows lack term boundaries or explicit current flags.")
    if sum(row["clearly_stale"] for row in currentness["table"]):
        warnings.append("Stale member rows are present relative to the supported 119th Congress window.")
    if conflicts["same_bioguide_mapped_to_multiple_app_ids"]:
        warnings.append("Duplicate Bioguide conflicts are present across local sources.")
    if conflicts["same_state_district_current_house_seat_multiple_members"]:
        warnings.append("Duplicate current House state/district seat conflicts are present across local sources.")
    if zip_inventory["fixture_only_mapping_rows"]:
        warnings.append("Fixture-only ZIP mappings are present and must not be treated as production coverage.")
    if zip_inventory["multi_district_zips_detected"]:
        warnings.append("Split-ZIP ambiguity is detectable in local fixture mappings.")
    if not senate["exists"]["senate_class"] or any(row["missing_lis_id"] for row in senate["table"]):
        warnings.append("Senate metadata is not sufficient for public Senate rollout without LIS/seat/class caveats and mapping gates.")
    warnings.append("Production-vs-local ambiguity remains: this report does not query production credentials or production tables.")
    return warnings


def write_outputs(
    report: dict[str, Any],
    *,
    repo_root: Path,
    markdown_out: Path,
    json_out: Path,
) -> None:
    markdown_path = repo_root / markdown_out
    json_path = repo_root / json_out
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8", newline="\n")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Legislator Metadata Hardening V1",
        "",
        "## Summary",
        "",
        report["scope"]["coverage_statement"],
        "",
        f"- Read-only: {_yes_no(report['scope']['read_only'])}",
        f"- Requires production credentials: {_yes_no(report['scope']['requires_production_credentials'])}",
        f"- Sources inspected: {report['summary']['sources_inspected']}",
        f"- Legislator/member rows inspected: {report['summary']['legislator_or_member_rows']}",
        f"- Warnings emitted: {report['summary']['warnings_emitted']}",
        "",
        "Highest metadata findings:",
    ]
    lines.extend(f"- {item}" for item in report["summary"]["highest_findings"])
    lines.extend(
        [
            "",
            "## Sources Inspected",
            "",
            _markdown_table(report["sources_inspected"], ("source_kind", "path", "exists", "row_count", "notes")),
            "",
            "## Identity Completeness Table",
            "",
            _markdown_table(
                report["identity_completeness"]["table"],
                (
                    "source_kind",
                    "rows",
                    "missing_app_internal_id",
                    "missing_bioguide_id",
                    "missing_lis_id_for_senators",
                    "missing_display_name",
                    "missing_persisted_slug",
                    "missing_chamber",
                    "missing_state",
                    "missing_house_district",
                    "missing_party",
                    "missing_current_flag",
                    "missing_term_start",
                    "missing_term_end",
                    "duplicate_bioguide_ids",
                    "duplicate_app_internal_ids",
                    "duplicate_slugs",
                ),
            ),
            "",
        ]
    )
    lines.extend(f"- {note}" for note in report["identity_completeness"]["notes"])
    lines.extend(
        [
            "",
            "## Chamber/State/District Quality Table",
            "",
            _markdown_table(
                report["chamber_state_district_quality"]["table"],
                (
                    "source_kind",
                    "rows",
                    "unknown_chamber",
                    "mixed_chamber_format_rows",
                    "house_rows_missing_district",
                    "senate_rows_with_house_style_district",
                    "invalid_state_values",
                    "invalid_house_district_values",
                    "at_large_house_districts",
                    "senate_lis_gaps",
                    "senate_bioguide_gaps",
                ),
            ),
            "",
        ]
    )
    lines.extend(f"- {note}" for note in report["chamber_state_district_quality"]["notes"])
    lines.extend(
        [
            "",
            "## Currentness/Term-Boundary Table",
            "",
            _markdown_table(
                report["currentness_term_boundary"]["table"],
                (
                    "source_kind",
                    "rows",
                    "inferred_current_or_recent",
                    "clearly_stale",
                    "ambiguous_currentness",
                    "no_end_year_or_no_term_boundary",
                    "term_dates_before_supported_window",
                    "in_office_term_conflicts",
                ),
            ),
            "",
        ]
    )
    lines.extend(f"- {note}" for note in report["currentness_term_boundary"]["notes"])
    conflicts = report["duplicate_conflict_findings"]
    zip_section = report["zip_district_lookup_implications"]
    lines.extend(
        [
            "",
            "## Duplicate/Conflict Findings",
            "",
            f"- Same Bioguide mapped to multiple app IDs: {len(conflicts['same_bioguide_mapped_to_multiple_app_ids'])}",
            f"- Same slug mapped to multiple people: {len(conflicts['same_slug_mapped_to_multiple_people'])}",
            f"- Same state/district/current House seat mapped to multiple current members: {len(conflicts['same_state_district_current_house_seat_multiple_members'])}",
            f"- Same Senate state/seat/class ambiguity groups: {len(conflicts['same_senate_state_seat_or_missing_class_ambiguity'])}",
            f"- ZIP mappings resolving to multiple districts: `{json.dumps(conflicts['zip_mappings_resolving_to_multiple_districts'], sort_keys=True)}`",
            f"- Fixture/Congress.gov disagreements: {len(conflicts['fixtures_disagree_with_congress_gov_cache'])}",
            "",
            "## ZIP/District Lookup Implications",
            "",
            f"- ZIP mapping rows: {zip_section['total_mapping_rows']}",
            f"- Fixture-only ZIP mapping rows: {zip_section['fixture_only_mapping_rows']}",
            f"- Unique ZIPs: {zip_section['unique_zips']}",
            f"- Multi-district ZIPs detected: `{json.dumps(zip_section['multi_district_zips_detected'], sort_keys=True)}`",
            f"- ZIP rows without any local House match: {len(zip_section['zip_rows_without_any_local_house_match'])}",
            f"- ZIP rows without app/fixture House match: {len(zip_section['zip_rows_without_app_fixture_house_match'])}",
            f"- Limitation: {zip_section['ambiguity_detection_limit']}",
            "",
            "Lookup safety implications:",
        ]
    )
    for item in zip_section["lookup_safety_implications"]["current_lookup_assumes"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            f"- One-ZIP-one-district assumed: {zip_section['lookup_safety_implications']['one_zip_one_district_assumed']}",
            f"- Empty search exposes all loaded legislators: {zip_section['lookup_safety_implications']['empty_search_exposes_all_loaded_legislators']}",
            "",
            "Warnings needed before national expansion:",
        ]
    )
    lines.extend(f"- {item}" for item in zip_section["lookup_safety_implications"]["user_facing_warnings_needed_before_national_expansion"])
    senate = report["senate_metadata_readiness"]
    lines.extend(
        [
            "",
            "## Senate Metadata Readiness",
            "",
            _markdown_table(
                senate["table"],
                (
                    "source_kind",
                    "rows",
                    "missing_lis_id",
                    "missing_bioguide_id",
                    "missing_state",
                    "missing_seat_rank_or_class",
                    "xml_source_identity_rows",
                    "senate_rows_with_house_style_district",
                ),
            ),
            "",
            f"- Senate LIS ID exists in inspected local sources: {_yes_no(senate['exists']['senate_lis_id'])}",
            f"- Bioguide ID exists in inspected local sources: {_yes_no(senate['exists']['bioguide_id'])}",
            f"- State exists in inspected local sources: {_yes_no(senate['exists']['state'])}",
            f"- Seat rank or class exists in inspected local sources: {_yes_no(senate['exists']['seat_rank_or_class'])}",
            f"- Senate class exists in inspected local sources: {_yes_no(senate['exists']['senate_class'])}",
            f"- Member XML source identity exists: {_yes_no(senate['exists']['member_xml_source_identity'])}",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in senate["metadata_chamber_readiness_risks"])
    lines.extend(["", "## Expansion Gates", ""])
    lines.extend(f"- {item}" for item in report["expansion_gates"])
    lines.extend(["", "## No-Go Items", ""])
    lines.extend(f"- {item}" for item in report["no_go_items"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in report["warnings"])
    lines.extend(["", "## Recommended Next Milestone", "", report["recommended_next_milestone"], ""])
    return "\n".join(lines)


def extract_house_xml_district(member: ElementTree.Element, member_info: ElementTree.Element) -> str | None:
    district = _text(member_info.find("district"))
    if district:
        return normalize_district(district)
    statedistrict = _text(member.find("statedistrict"))
    if not statedistrict:
        return None
    digits = "".join(character for character in statedistrict if character.isdigit())
    return digits.zfill(2)[-2:] if digits else "00"


def extract_senate_xml_name(member: ElementTree.Element) -> str | None:
    full_name = _text(member.find("full_name")) or _text(member.find("member_full"))
    if full_name:
        return full_name
    name_element = member.find("name")
    if name_element is not None:
        parts = [_text(name_element.find("first")), _text(name_element.find("last"))]
        name = " ".join(part for part in parts if part)
        if name:
            return name
    parts = [_text(member.find("first_name")), _text(member.find("last_name"))]
    name = " ".join(part for part in parts if part)
    return name or None


def infer_currentness(in_office: Any, term_start_year: Any, term_end_year: Any) -> str:
    current_flag = parse_bool(in_office)
    start_year = parse_int(term_start_year)
    end_year = parse_int(term_end_year)
    if end_year is not None:
        if end_year < SUPPORTED_START_YEAR:
            return "clearly_stale_before_supported_119"
        if end_year >= SUPPORTED_END_YEAR:
            return "inferred_current_or_recent"
        return "term_boundary_risk"
    if start_year is not None:
        return "ambiguous_no_end_year"
    if current_flag is True:
        return "locally_current_flag_no_term_boundary"
    if current_flag is False:
        return "not_in_office_flag_no_term_boundary"
    return "missing_terms_and_current_flag"


def current_flag_conflicts_with_terms(row: dict[str, Any]) -> bool:
    if row["in_office"] is True and row["term_end_year"] is not None and row["term_end_year"] < SUPPORTED_END_YEAR:
        return True
    if row["in_office"] is False and (
        row["term_end_year"] is None or row["term_end_year"] >= SUPPORTED_END_YEAR
    ):
        return True
    return False


def fixture_congress_cache_disagreements(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fixture_rows = [row for row in rows if row["source_kind"] in {"fixture_legislators", "congress_sample_members"}]
    congress_by_bioguide = {
        row["bioguide_id"]: row
        for row in rows
        if row["source_kind"] == "congress_gov_member_cache" and _has_text(row["bioguide_id"])
    }
    disagreements = []
    for row in fixture_rows:
        cached = congress_by_bioguide.get(row["bioguide_id"])
        if cached is None:
            continue
        different = [
            field for field in ("display_name", "chamber", "state", "district", "party")
            if _clean(row.get(field)) and _clean(cached.get(field)) and _clean(row.get(field)) != _clean(cached.get(field))
        ]
        if different:
            disagreements.append(
                {
                    "bioguide_id": row["bioguide_id"],
                    "fixture": compact_row(row),
                    "congress_gov_cache": compact_row(cached),
                    "fields": different,
                }
            )
    return disagreements[:50]


def group_conflicts(
    rows: list[dict[str, Any]],
    key: str,
    *,
    minimum: int,
    person_key: str = "app_internal_id",
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = row.get(key)
        if _has_text(value):
            groups[str(value)].append(row)
    return compact_conflict_groups(groups, minimum=minimum, person_key=person_key)


def compact_conflict_groups(
    groups: dict[str, list[dict[str, Any]]],
    *,
    minimum: int = 2,
    person_key: str = "app_internal_id",
) -> list[dict[str, Any]]:
    conflicts = []
    for value, group_rows in sorted(groups.items()):
        people = {
            row.get(person_key) or row.get("bioguide_id") or row.get("display_name")
            for row in group_rows
            if row.get(person_key) or row.get("bioguide_id") or row.get("display_name")
        }
        if len(group_rows) >= minimum and len(people) >= minimum:
            conflicts.append(
                {
                    "value": value,
                    "row_count": len(group_rows),
                    "people_count": len(people),
                    "examples": [compact_row(row) for row in group_rows[:10]],
                }
            )
    return conflicts[:100]


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_kind": row.get("source_kind"),
        "source_path": row.get("source_path"),
        "app_internal_id": row.get("app_internal_id"),
        "generated_app_id": row.get("generated_app_id"),
        "bioguide_id": row.get("bioguide_id"),
        "lis_id": row.get("lis_id"),
        "display_name": row.get("display_name"),
        "chamber": row.get("chamber"),
        "state": row.get("state"),
        "district": row.get("district"),
        "party": row.get("party"),
        "in_office": row.get("in_office"),
        "term_start_year": row.get("term_start_year"),
        "term_end_year": row.get("term_end_year"),
        "currentness": row.get("currentness"),
    }


def normalize_chamber(value: Any) -> str | None:
    text = _clean(value)
    lowered = text.lower() if text else ""
    if lowered in {"house", "house of representatives", "u.s. house", "representative"}:
        return "house"
    if lowered in {"senate", "u.s. senate", "senator"}:
        return "senate"
    return text.lower() if text else None


def normalize_party(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    lowered = text.lower()
    if lowered.startswith("democrat") or text == "D":
        return "D"
    if lowered.startswith("republican") or text == "R":
        return "R"
    if lowered.startswith("independent") or text == "I":
        return "I"
    return text


def normalize_district(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    lowered = text.lower()
    if lowered in HOUSE_STYLE_DISTRICT_VALUES or "at large" in lowered or "at-large" in lowered:
        return "00"
    digits = "".join(character for character in text if character.isdigit())
    if digits:
        return digits.zfill(2)[-2:]
    if lowered == "statewide":
        return "Statewide"
    return text


def is_valid_house_district(value: Any) -> bool:
    text = _clean(value)
    if not text:
        return False
    if is_at_large_district(text):
        return True
    return bool(re.fullmatch(r"\d{1,2}", text))


def is_at_large_district(value: Any) -> bool:
    text = _clean(value)
    return bool(text and text.lower() in {"00", "0", "at large", "at-large"})


def is_house_style_district(value: Any) -> bool:
    text = _clean(value)
    if not text:
        return False
    return is_valid_house_district(text) and text.lower() != "statewide"


def is_currentish(row: dict[str, Any]) -> bool:
    return row["currentness"] not in {"clearly_stale_before_supported_119", "not_in_office_flag_no_term_boundary"}


def count_missing(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if not _has_text(row.get(key)))


def duplicate_count(rows: list[dict[str, Any]], key: str) -> int:
    counts = Counter(str(row.get(key)) for row in rows if _has_text(row.get(key)))
    return sum(1 for count in counts.values() if count > 1)


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    return None


def parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _term_items(row: dict[str, Any]) -> list[dict[str, Any]]:
    terms = row.get("terms")
    if isinstance(terms, dict):
        return [item for item in _as_list(terms.get("item")) if isinstance(item, dict)]
    return []


def _latest_term(terms: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not terms:
        return None
    return sorted(terms, key=lambda item: parse_int(item.get("startYear")) or 0)[-1]


def _state_code(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    if text in STATE_NAME_TO_CODE:
        return STATE_NAME_TO_CODE[text]
    upper = text.upper()
    if upper in VALID_STATE_CODES:
        return upper
    return text


def _to_legislator_id(name_display: Any) -> str | None:
    slug = _slug(name_display)
    return f"leg_{slug}" if slug else None


def _slug(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or None


def _first_text(element: ElementTree.Element, tags: tuple[str, ...]) -> str | None:
    for tag in tags:
        value = _text(element.find(tag))
        if value:
            return value
    return None


def _text(element: ElementTree.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return _clean(element.text)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _markdown_table(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> str:
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_md_value(row.get(column)) for column in columns) + " |")
    return "\n".join([header, divider, *body])


def _md_value(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", "\\|")
    return str(value).replace("|", "\\|")


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    raise SystemExit(main())
