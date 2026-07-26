"""Generate a read-only local data inventory manifest.

This script only inspects repository files. It does not import app DB helpers,
open network connections, or require production credentials.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPORT_MD = Path("docs/review_packets/data_inventory_source_manifest_v1.md")
REPORT_JSON = Path("docs/review_packets/data_inventory_source_manifest_v1.json")
EXPECTED_HOUSE_YEARS = ("2023", "2024", "2025", "2026")
EXPECTED_SENATE_SESSIONS = ("118_1", "118_2", "119_1", "119_2")
OFFICIAL_SOURCE_DOMAINS = (
    "clerk.house.gov",
    "www.congress.gov",
    "congress.gov",
    "www.senate.gov",
    "senate.gov",
    "api.congress.gov",
)
INTERPRETATION_FIELDS = (
    "interpretation_status",
    "support_position",
    "oppose_position",
    "interpretation_reason",
    "plain_english_summary",
    "policy_effect",
    "issue_facet",
    "what_happened",
    "why_it_mattered",
    "what_not_to_infer",
    "uncertainty_note",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD)
    parser.add_argument("--json-out", type=Path, default=REPORT_JSON)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest = build_manifest(repo_root)
    write_outputs(
        manifest,
        repo_root=repo_root,
        markdown_out=args.markdown_out,
        json_out=args.json_out,
    )
    print(f"Wrote {args.markdown_out}")
    print(f"Wrote {args.json_out}")
    return 0


def build_manifest(repo_root: Path) -> dict[str, Any]:
    source_cache = inventory_source_cache(repo_root)
    fixtures = inventory_fixture_data(repo_root)
    legislators = inventory_legislators(repo_root, fixtures)
    zip_inventory = inventory_zip_mappings(fixtures)
    vote_inventory = inventory_votes(fixtures)
    source_url_coverage = inventory_source_urls(repo_root, fixtures)
    interpretation_coverage = inventory_interpretations(repo_root)
    derived_artifacts = inventory_derived_artifacts(repo_root)
    warnings = generate_warnings(
        source_cache=source_cache,
        fixtures=fixtures,
        legislators=legislators,
        zip_inventory=zip_inventory,
        source_url_coverage=source_url_coverage,
        interpretation_coverage=interpretation_coverage,
        derived_artifacts=derived_artifacts,
    )

    return {
        "schema_version": "data_inventory_source_manifest_v1",
        "scope": {
            "read_only": True,
            "requires_production_credentials": False,
            "coverage_statement": (
                "Repository/local-accessible data only. Counts are not production coverage "
                "unless a future read-only production manifest is generated with credentials."
            ),
        },
        "source_cache_inventory": source_cache,
        "fixture_inventory": fixtures["summary"],
        "legislator_metadata_inventory": legislators,
        "zip_district_inventory": zip_inventory,
        "vote_row_inventory": vote_inventory,
        "source_url_coverage": source_url_coverage,
        "interpretation_coverage": interpretation_coverage,
        "derived_artifacts": derived_artifacts,
        "warnings": warnings,
        "expansion_readiness_implications": [
            "Local caches show useful House, Senate, Congress.gov, fixture, interpretation, and derived-artifact coverage, but they do not prove production load state.",
            "The current manifest can identify gaps before expansion, but a production read-only companion should be added before broad rollout decisions.",
            "House current-Congress expansion remains the nearest pilot path only after source URL, member metadata, ZIP ambiguity, and sparse-profile gates are explicit.",
            "Senate public reads still need chamber-aware vote-type and interpretation rules before support/opposition claims scale.",
        ],
        "no_go_gates": [
            "Do not treat this local manifest as production truth.",
            "Do not publish Senate reads using House assumptions.",
            "Do not add broad member coverage without per-member source and interpretation coverage reporting.",
            "Do not generate top-level reads for thin, unreviewed, ambiguous, procedural, or not-voting-heavy evidence.",
            "Do not expand national ZIP lookup without split-ZIP/address ambiguity handling.",
            "Do not use Record Across artifacts to claim change, consistency, trend, or movement.",
        ],
        "recommended_next_milestone": (
            "Legislator metadata hardening, with currentness, term-boundary, identity, "
            "state/district, Senate LIS/Bioguide, and stale-member checks."
        ),
    }


def inventory_source_cache(repo_root: Path) -> dict[str, Any]:
    house_root = repo_root / "backend/data_sources/house_clerk"
    senate_root = repo_root / "backend/data_sources/senate_xml"
    congress_root = repo_root / "backend/data_sources/congress"

    house = []
    for year in EXPECTED_HOUSE_YEARS:
        path = house_root / year
        xml_files = _sorted_files(path, "roll*.xml")
        house.append(
            {
                "year": year,
                "path": _rel(repo_root, path),
                "exists": path.exists(),
                "roll_xml_count": len(xml_files),
            }
        )

    senate = []
    for session_key in EXPECTED_SENATE_SESSIONS:
        path = senate_root / session_key
        xml_files = _sorted_files(path, "vote_*.xml")
        senate.append(
            {
                "congress_session": session_key,
                "path": _rel(repo_root, path),
                "exists": path.exists(),
                "vote_xml_count": len(xml_files),
                "members_xml_exists": (path / "members.xml").exists(),
            }
        )

    congress = []
    for name in (
        "amendments",
        "bills",
        "bill_actions",
        "bill_amendments",
        "bill_committees",
        "bill_subjects",
        "bill_summaries",
        "bill_texts",
        "members",
    ):
        path = congress_root / name
        congress.append(
            {
                "source_type": name,
                "path": _rel(repo_root, path),
                "exists": path.exists(),
                "json_count": len(_sorted_files(path, "*.json")),
            }
        )

    loose_senate_xml = [
        path for path in _sorted_files(senate_root, "vote_*.xml")
        if path.parent == senate_root
    ]

    return {
        "paths_inspected": [
            _rel(repo_root, house_root),
            _rel(repo_root, senate_root),
            _rel(repo_root, congress_root),
        ],
        "house_clerk": house,
        "senate_xml": senate,
        "loose_senate_xml_count": len(loose_senate_xml),
        "congress_gov": congress,
    }


def inventory_fixture_data(repo_root: Path) -> dict[str, Any]:
    root = repo_root / "backend/fixtures"
    fixture_files = []
    data_by_path: dict[str, Any] = {}
    for path in _sorted_files(root, "*"):
        if not path.is_file():
            continue
        row = {
            "path": _rel(repo_root, path),
            "exists": path.exists(),
            "extension": path.suffix.lower(),
            "record_count": None,
        }
        if path.suffix.lower() == ".json":
            data = _load_json(path)
            data_by_path[_rel(repo_root, path)] = data
            row["record_count"] = _json_record_count(data)
        fixture_files.append(row)

    return {
        "root": root,
        "data_by_path": data_by_path,
        "summary": {
            "path": _rel(repo_root, root),
            "exists": root.exists(),
            "file_count": len(fixture_files),
            "json_file_count": sum(1 for row in fixture_files if row["extension"] == ".json"),
            "xml_file_count": sum(1 for row in fixture_files if row["extension"] == ".xml"),
            "files": fixture_files,
        },
    }


def inventory_legislators(repo_root: Path, fixtures: dict[str, Any]) -> dict[str, Any]:
    fixture_rows = _as_list(fixtures["data_by_path"].get("backend/fixtures/legislators.json"))
    fixture_summary = _summarize_legislator_rows(fixture_rows, source="fixtures")

    congress_member_rows: list[dict[str, Any]] = []
    congress_member_files = []
    for path in _sorted_files(repo_root / "backend/data_sources/congress/members", "*.json"):
        data = _load_json(path)
        rows = _as_list(data.get("members") if isinstance(data, dict) else data)
        congress_member_rows.extend(rows)
        congress_member_files.append(
            {
                "path": _rel(repo_root, path),
                "congress": data.get("congress") if isinstance(data, dict) else None,
                "member_count": len(rows),
            }
        )

    congress_summary = _summarize_congress_member_rows(congress_member_rows)

    return {
        "fixture_legislators": fixture_summary,
        "congress_member_files": congress_member_files,
        "congress_member_metadata": congress_summary,
        "identity_field_notes": [
            "Fixture legislators have Bioguide IDs but no LIS ID or persisted slug field.",
            "Congress.gov member cache uses bioguideId/name/state/partyName/terms and does not provide app slugs.",
            "This is local metadata coverage, not the loaded production legislators table.",
        ],
    }


def inventory_zip_mappings(fixtures: dict[str, Any]) -> dict[str, Any]:
    rows_by_file = []
    all_rows = []
    for rel_path, data in sorted(fixtures["data_by_path"].items()):
        if not rel_path.endswith("zip_district_map.json"):
            continue
        rows = _as_list(data)
        rows_by_file.append(
            {
                "path": rel_path,
                "mapping_count": len(rows),
                "fixture_only": rel_path.startswith("backend/fixtures/"),
            }
        )
        all_rows.extend(rows)

    by_state = Counter(str(row.get("state") or "missing") for row in all_rows if isinstance(row, dict))
    by_district = Counter(
        f"{row.get('state') or 'missing'}-{row.get('district') or 'missing'}"
        for row in all_rows
        if isinstance(row, dict)
    )
    districts_by_zip: dict[str, set[str]] = defaultdict(set)
    for row in all_rows:
        if not isinstance(row, dict):
            continue
        districts_by_zip[str(row.get("zip") or "missing")].add(
            f"{row.get('state') or 'missing'}-{row.get('district') or 'missing'}"
        )

    multi_district_zips = {
        zip_code: sorted(districts)
        for zip_code, districts in sorted(districts_by_zip.items())
        if len(districts) > 1
    }

    return {
        "paths": rows_by_file,
        "total_mapping_rows": len(all_rows),
        "unique_zips": len(districts_by_zip),
        "by_state": dict(sorted(by_state.items())),
        "by_district": dict(sorted(by_district.items())),
        "multi_district_zips_detected": multi_district_zips,
        "fixture_only_mapping_rows": sum(1 for row in rows_by_file if row["fixture_only"] for _ in range(row["mapping_count"])),
        "ambiguity_detection_limit": "Only multiple mappings present in local fixture files are detectable; address-level split ZIP coverage is not represented.",
    }


def inventory_votes(fixtures: dict[str, Any]) -> dict[str, Any]:
    roll_calls = _as_list(fixtures["data_by_path"].get("backend/fixtures/roll_calls.json"))
    votes_cast = _as_list(fixtures["data_by_path"].get("backend/fixtures/votes_cast.json"))
    tags = fixtures["data_by_path"].get("backend/fixtures/vote_subject_tags.json")
    tags = tags if isinstance(tags, dict) else {}
    roll_by_id = {row.get("id"): row for row in roll_calls if isinstance(row, dict)}

    roll_counts = Counter()
    roll_by_year = Counter()
    domain_counts = Counter()
    source_present = 0
    source_missing = 0
    for row in roll_calls:
        if not isinstance(row, dict):
            continue
        chamber = str(row.get("chamber") or "missing")
        congress = str(row.get("congress") or "missing")
        year = _year_from_date(row.get("vote_date"))
        session = _infer_session(row.get("congress"), year)
        roll_counts[f"{chamber}:{congress}:session_{session or 'unknown'}"] += 1
        roll_by_year[f"{chamber}:{year or 'unknown'}"] += 1
        bill_ref = row.get("bill_ref")
        for subject in tags.get(bill_ref, []) if bill_ref in tags else []:
            domain_counts[str(subject)] += 1
        if _has_text(row.get("source_url")):
            source_present += 1
        else:
            source_missing += 1

    vote_positions = Counter()
    member_vote_counts = Counter()
    for row in votes_cast:
        if not isinstance(row, dict):
            continue
        position = str(row.get("position") or "missing")
        vote_positions[position] += 1
        roll = roll_by_id.get(row.get("roll_call_id"), {})
        member_vote_counts[
            f"{roll.get('chamber', 'missing')}:{roll.get('congress', 'missing')}"
        ] += 1

    return {
        "fixture_roll_call_rows": len(roll_calls),
        "fixture_member_vote_rows": len(votes_cast),
        "roll_calls_by_chamber_congress_session": dict(sorted(roll_counts.items())),
        "roll_calls_by_chamber_year": dict(sorted(roll_by_year.items())),
        "member_vote_rows_by_chamber_congress": dict(sorted(member_vote_counts.items())),
        "member_vote_position_counts": dict(sorted(vote_positions.items())),
        "roll_call_source_url_present": source_present,
        "roll_call_source_url_missing": source_missing,
        "fixture_subject_tag_counts": dict(sorted(domain_counts.items())),
        "interpretation_note": "Fixture vote rows have positions but do not encode reviewed support/opposition semantics.",
    }


def inventory_source_urls(repo_root: Path, fixtures: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for rel_path in (
        "backend/fixtures/roll_calls.json",
        "docs/review_packets/senate_vote_facts_expansion_manifest_phase_11.json",
    ):
        path = repo_root / rel_path
        data = _load_json(path)
        for item in _walk_dicts(data):
            if "source_url" in item:
                rows.append({"path": rel_path, **item})

    for path in _sorted_files(repo_root / "docs/interpretation_batches", "*.json"):
        data = _load_json(path)
        for item in _walk_dicts(data):
            if "source_url" in item:
                rows.append({"path": _rel(repo_root, path), **item})

    with_url = [row for row in rows if _has_text(row.get("source_url"))]
    missing_url = [row for row in rows if not _has_text(row.get("source_url"))]
    official = [row for row in with_url if _is_official_url(str(row.get("source_url")))]
    non_official = [row for row in with_url if not _is_official_url(str(row.get("source_url")))]
    malformed = [
        row for row in with_url
        if not str(row.get("source_url")).startswith(("http://", "https://"))
    ]

    by_chamber_congress_domain = Counter()
    for row in with_url:
        chamber = str(row.get("chamber") or "unknown")
        congress = str(row.get("congress") or "unknown")
        domain = str(row.get("issue_domain") or row.get("domain") or row.get("primary_domain") or "unknown")
        by_chamber_congress_domain[f"{chamber}:{congress}:{domain}"] += 1

    return {
        "paths_inspected": [
            "backend/fixtures/roll_calls.json",
            "docs/interpretation_batches/*.json",
            "docs/review_packets/senate_vote_facts_expansion_manifest_phase_11.json",
        ],
        "total_rows_with_source_url_field": len(rows),
        "rows_with_source_url": len(with_url),
        "rows_missing_source_url": len(missing_url),
        "rows_with_official_source_url": len(official),
        "rows_with_non_official_source_url": len(non_official),
        "rows_with_malformed_source_url": len(malformed),
        "rows_with_source_url_by_chamber_congress_domain": dict(sorted(by_chamber_congress_domain.items())),
        "non_official_examples": _sample_values(non_official, "source_url", limit=5),
        "missing_examples": _sample_values(missing_url, "path", limit=5),
    }


def inventory_interpretations(repo_root: Path) -> dict[str, Any]:
    rows = []
    files = []
    for root in (repo_root / "docs/interpretation_batches", repo_root / "docs/review_packets"):
        for path in _sorted_files(root, "*.json"):
            if root.name == "review_packets" and not _is_review_manifest_candidate(path):
                continue
            data = _load_json(path)
            row_count = 0
            for item in _walk_dicts(data):
                if any(field in item for field in INTERPRETATION_FIELDS):
                    rows.append({"path": _rel(repo_root, path), **item})
                    row_count += 1
            if row_count:
                files.append({"path": _rel(repo_root, path), "interpretation_like_rows": row_count})

    status_counts = Counter(str(row.get("interpretation_status") or "missing") for row in rows)
    with_counting_positions = [
        row for row in rows
        if row.get("interpretation_status") == "interpreted"
        and _has_text(row.get("support_position"))
        and _has_text(row.get("oppose_position"))
    ]
    not_voting_rows = [
        row for row in rows
        if str(row.get("position") or "").lower() == "not_voting"
        or "not_voting" in str(row.get("interpretation_status") or "").lower()
    ]
    limited_rows = [
        row for row in rows
        if str(row.get("interpretation_status") or "").lower() in {"ambiguous", "insufficient_evidence"}
        or _has_text(row.get("uncertainty_note"))
        or _has_text(row.get("what_not_to_infer"))
    ]
    missing_reason = [row for row in rows if not _has_text(row.get("interpretation_reason"))]
    missing_what = [row for row in rows if not _has_text(row.get("what_happened"))]
    missing_why = [row for row in rows if not _has_text(row.get("why_it_mattered"))]
    missing_caveat = [
        row for row in rows
        if not _has_text(row.get("what_not_to_infer")) and not _has_text(row.get("uncertainty_note"))
    ]

    by_domain = Counter(
        str(row.get("issue_domain") or row.get("domain") or row.get("primary_domain") or "unknown")
        for row in rows
    )

    return {
        "paths_inspected": ["docs/interpretation_batches/*.json", "docs/review_packets/*manifest*.json and selected prewrite/audit JSON"],
        "files_with_interpretation_like_rows": files,
        "interpretation_like_rows": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "rows_with_interpreted_support_opposition": len(with_counting_positions),
        "ambiguous_or_limited_context_rows": len(limited_rows),
        "not_voting_rows_detected": len(not_voting_rows),
        "rows_missing_interpretation_reason": len(missing_reason),
        "rows_missing_what_happened": len(missing_what),
        "rows_missing_why_it_mattered": len(missing_why),
        "rows_missing_caveat_or_uncertainty_field": len(missing_caveat),
        "rows_excluded_from_top_level_summary_candidate": len(rows) - len(with_counting_positions),
        "rows_by_domain": dict(sorted(by_domain.items())),
    }


def inventory_derived_artifacts(repo_root: Path) -> dict[str, Any]:
    artifacts = []
    for rel_path in (
        "docs/derived/house_comparable_policy_question_families_v1.json",
        "docs/analysis/house_comparable_policy_question_families.json",
        "docs/analysis/house_comparable_policy_question_profiles.csv",
        "docs/analysis/house_comparable_policy_question_thresholds.csv",
        "docs/analysis/house_continuity_readiness_analysis.json",
        "docs/analysis/house_continuity_thresholds.csv",
    ):
        path = repo_root / rel_path
        artifacts.append(_artifact_summary(repo_root, path))

    interpretation_batch_files = _sorted_files(repo_root / "docs/interpretation_batches", "*.json")
    rollback_files = _sorted_files(repo_root / "docs/review_packets", "*rollback*.sql")
    manifest_files = _sorted_files(repo_root / "docs/review_packets", "*manifest*.json")
    deferred_files = [
        path for path in _sorted_files(repo_root / "docs/review_packets", "*.json")
        if "defer" in path.name.lower() or "deferred" in path.name.lower()
    ]

    return {
        "record_across_and_comparable_family_artifacts": artifacts,
        "reviewed_interpretation_batch_artifact_count": len(interpretation_batch_files),
        "reviewed_interpretation_batch_paths_sample": [_rel(repo_root, path) for path in interpretation_batch_files[:8]],
        "rollback_sql_artifact_count": len(rollback_files),
        "manifest_json_artifact_count": len(manifest_files),
        "deferred_artifact_count": len(deferred_files),
        "rollback_paths_sample": [_rel(repo_root, path) for path in rollback_files[:8]],
        "manifest_paths_sample": [_rel(repo_root, path) for path in manifest_files[:8]],
        "house_only_record_across": True,
    }


def generate_warnings(
    *,
    source_cache: dict[str, Any],
    fixtures: dict[str, Any],
    legislators: dict[str, Any],
    zip_inventory: dict[str, Any],
    source_url_coverage: dict[str, Any],
    interpretation_coverage: dict[str, Any],
    derived_artifacts: dict[str, Any],
) -> list[str]:
    warnings = [
        "This manifest describes repository/local-accessible files only; it is not production coverage truth.",
        "The script does not use production credentials and cannot distinguish loaded production rows from local caches.",
    ]

    for row in source_cache["house_clerk"]:
        if not row["exists"] or row["roll_xml_count"] == 0:
            warnings.append(f"House Clerk cache gap: {row['year']} has {row['roll_xml_count']} roll XML files at {row['path']}.")
    for row in source_cache["senate_xml"]:
        if not row["exists"] or row["vote_xml_count"] == 0:
            warnings.append(f"Senate XML cache gap: {row['congress_session']} has {row['vote_xml_count']} vote XML files at {row['path']}.")
        if row["exists"] and not row["members_xml_exists"]:
            warnings.append(f"Senate XML member metadata missing for {row['congress_session']} at {row['path']}.")

    if fixtures["summary"]["file_count"] > 0:
        warnings.append("Fixture data is present and intentionally small; fallback coverage must not be presented as production coverage.")

    missing_fixture_identity = legislators["fixture_legislators"]["missing_identity_fields"]
    for field, count in sorted(missing_fixture_identity.items()):
        if count:
            warnings.append(f"Fixture legislator metadata missing {field} for {count} rows.")

    if zip_inventory["total_mapping_rows"] and not zip_inventory["multi_district_zips_detected"]:
        warnings.append("ZIP inventory has one district per ZIP in local fixtures; split-ZIP/address ambiguity is not represented.")

    if source_url_coverage["rows_missing_source_url"]:
        warnings.append(f"Source URL coverage gap: {source_url_coverage['rows_missing_source_url']} inspected rows have no source_url.")
    if source_url_coverage["rows_with_non_official_source_url"]:
        warnings.append(f"Source URL trust gap: {source_url_coverage['rows_with_non_official_source_url']} inspected rows have non-official source URLs.")
    if interpretation_coverage["rows_excluded_from_top_level_summary_candidate"]:
        warnings.append(
            "Interpretation coverage gap: "
            f"{interpretation_coverage['rows_excluded_from_top_level_summary_candidate']} interpretation-like rows are not interpreted support/opposition candidates."
        )
    if derived_artifacts.get("house_only_record_across"):
        warnings.append("Record Across artifacts are House-only and must not be used as Senate comparison support.")

    warnings.append("Senate-specific vote types, nominations, treaties, cloture, and amendment references still need separate public-read gates.")
    return warnings


def write_outputs(
    manifest: dict[str, Any],
    *,
    repo_root: Path,
    markdown_out: Path,
    json_out: Path,
) -> None:
    markdown_path = repo_root / markdown_out
    json_path = repo_root / json_out
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(manifest), encoding="utf-8", newline="\n")
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def render_markdown(manifest: dict[str, Any]) -> str:
    source = manifest["source_cache_inventory"]
    legislators = manifest["legislator_metadata_inventory"]
    zip_inventory = manifest["zip_district_inventory"]
    votes = manifest["vote_row_inventory"]
    urls = manifest["source_url_coverage"]
    interpretations = manifest["interpretation_coverage"]
    derived = manifest["derived_artifacts"]

    lines = [
        "# Data Inventory / Source Manifest V1",
        "",
        "## Summary",
        "",
        manifest["scope"]["coverage_statement"],
        "",
        f"- Read-only: {_yes_no(manifest['scope']['read_only'])}",
        f"- Requires production credentials: {_yes_no(manifest['scope']['requires_production_credentials'])}",
        f"- Fixture roll calls: {votes['fixture_roll_call_rows']}",
        f"- Fixture member vote rows: {votes['fixture_member_vote_rows']}",
        f"- Local source URL rows inspected: {urls['total_rows_with_source_url_field']}",
        f"- Interpretation-like rows inspected: {interpretations['interpretation_like_rows']}",
        f"- Warnings emitted: {len(manifest['warnings'])}",
        "",
        "## Source Cache Inventory",
        "",
        "### House Clerk XML",
        "",
        _markdown_table(source["house_clerk"], ("year", "path", "exists", "roll_xml_count")),
        "",
        "### Senate XML",
        "",
        _markdown_table(source["senate_xml"], ("congress_session", "path", "exists", "vote_xml_count", "members_xml_exists")),
        "",
        f"Loose Senate XML files at `backend/data_sources/senate_xml`: {source['loose_senate_xml_count']}",
        "",
        "### Congress.gov Local Metadata",
        "",
        _markdown_table(source["congress_gov"], ("source_type", "path", "exists", "json_count")),
        "",
        "## Fixture Inventory",
        "",
        _markdown_table(manifest["fixture_inventory"]["files"], ("path", "extension", "record_count")),
        "",
        "## Legislator Metadata Inventory",
        "",
        "### Fixture Legislators",
        "",
        f"- Total: {legislators['fixture_legislators']['total']}",
        f"- By chamber: `{json.dumps(legislators['fixture_legislators']['by_chamber'], sort_keys=True)}`",
        f"- By party: `{json.dumps(legislators['fixture_legislators']['by_party'], sort_keys=True)}`",
        f"- By state: `{json.dumps(legislators['fixture_legislators']['by_state'], sort_keys=True)}`",
        f"- Current/in-office: `{json.dumps(legislators['fixture_legislators']['by_in_office'], sort_keys=True)}`",
        f"- Missing identity fields: `{json.dumps(legislators['fixture_legislators']['missing_identity_fields'], sort_keys=True)}`",
        "",
        "### Congress.gov Member Cache",
        "",
        _markdown_table(legislators["congress_member_files"], ("path", "congress", "member_count")),
        "",
        f"- Total cached member rows: {legislators['congress_member_metadata']['total']}",
        f"- By chamber: `{json.dumps(legislators['congress_member_metadata']['by_chamber'], sort_keys=True)}`",
        f"- By party: `{json.dumps(legislators['congress_member_metadata']['by_party'], sort_keys=True)}`",
        f"- By state count: {len(legislators['congress_member_metadata']['by_state'])}",
        f"- Currentness inferred from term end-year: `{json.dumps(legislators['congress_member_metadata']['by_currentness'], sort_keys=True)}`",
        f"- Missing identity fields: `{json.dumps(legislators['congress_member_metadata']['missing_identity_fields'], sort_keys=True)}`",
        "",
        "## ZIP/District Inventory",
        "",
        _markdown_table(zip_inventory["paths"], ("path", "mapping_count", "fixture_only")),
        "",
        f"- Total mapping rows: {zip_inventory['total_mapping_rows']}",
        f"- Unique ZIPs: {zip_inventory['unique_zips']}",
        f"- By state: `{json.dumps(zip_inventory['by_state'], sort_keys=True)}`",
        f"- By district: `{json.dumps(zip_inventory['by_district'], sort_keys=True)}`",
        f"- Multi-district ZIPs detected: `{json.dumps(zip_inventory['multi_district_zips_detected'], sort_keys=True)}`",
        f"- Limitation: {zip_inventory['ambiguity_detection_limit']}",
        "",
        "## Vote Row Inventory",
        "",
        f"- Fixture roll-call rows: {votes['fixture_roll_call_rows']}",
        f"- Fixture member vote rows: {votes['fixture_member_vote_rows']}",
        f"- Roll calls by chamber/Congress/session: `{json.dumps(votes['roll_calls_by_chamber_congress_session'], sort_keys=True)}`",
        f"- Member vote rows by chamber/Congress: `{json.dumps(votes['member_vote_rows_by_chamber_congress'], sort_keys=True)}`",
        f"- Member vote position counts: `{json.dumps(votes['member_vote_position_counts'], sort_keys=True)}`",
        f"- Fixture subject tag counts: `{json.dumps(votes['fixture_subject_tag_counts'], sort_keys=True)}`",
        f"- Interpretation note: {votes['interpretation_note']}",
        "",
        "## Source URL Coverage",
        "",
        f"- Total rows with `source_url` field inspected: {urls['total_rows_with_source_url_field']}",
        f"- Rows with source URL: {urls['rows_with_source_url']}",
        f"- Rows missing source URL: {urls['rows_missing_source_url']}",
        f"- Rows with official source URL: {urls['rows_with_official_source_url']}",
        f"- Rows with non-official source URL: {urls['rows_with_non_official_source_url']}",
        f"- Rows with malformed source URL: {urls['rows_with_malformed_source_url']}",
        f"- Non-official examples: `{json.dumps(urls['non_official_examples'])}`",
        "",
        "## Interpretation Coverage",
        "",
        f"- Interpretation-like rows: {interpretations['interpretation_like_rows']}",
        f"- Status counts: `{json.dumps(interpretations['status_counts'], sort_keys=True)}`",
        f"- Rows with interpreted support/opposition: {interpretations['rows_with_interpreted_support_opposition']}",
        f"- Ambiguous or limited-context rows: {interpretations['ambiguous_or_limited_context_rows']}",
        f"- Not-voting rows detected: {interpretations['not_voting_rows_detected']}",
        f"- Rows missing interpretation reason: {interpretations['rows_missing_interpretation_reason']}",
        f"- Rows missing what happened: {interpretations['rows_missing_what_happened']}",
        f"- Rows missing why it mattered: {interpretations['rows_missing_why_it_mattered']}",
        f"- Rows missing caveat or uncertainty field: {interpretations['rows_missing_caveat_or_uncertainty_field']}",
        f"- Rows excluded from top-level summary candidate: {interpretations['rows_excluded_from_top_level_summary_candidate']}",
        "",
        "## Derived Artifacts",
        "",
        _markdown_table(
            derived["record_across_and_comparable_family_artifacts"],
            ("path", "exists", "kind", "record_count", "notes"),
        ),
        "",
        f"- Reviewed interpretation batch JSON files: {derived['reviewed_interpretation_batch_artifact_count']}",
        f"- Rollback SQL artifacts: {derived['rollback_sql_artifact_count']}",
        f"- Manifest JSON artifacts: {derived['manifest_json_artifact_count']}",
        f"- Deferred artifact count: {derived['deferred_artifact_count']}",
        f"- Record Across House-only: {_yes_no(derived['house_only_record_across'])}",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in manifest["warnings"])
    lines.extend(
        [
            "",
            "## Expansion Readiness Implications",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in manifest["expansion_readiness_implications"])
    lines.extend(["", "## No-Go Gates", ""])
    lines.extend(f"- {item}" for item in manifest["no_go_gates"])
    lines.extend(
        [
            "",
            "## Recommended Next Milestone",
            "",
            manifest["recommended_next_milestone"],
            "",
        ]
    )
    return "\n".join(lines)


def _summarize_legislator_rows(rows: list[Any], *, source: str) -> dict[str, Any]:
    dict_rows = [row for row in rows if isinstance(row, dict)]
    return {
        "source": source,
        "total": len(dict_rows),
        "by_chamber": dict(sorted(Counter(str(row.get("chamber") or "missing") for row in dict_rows).items())),
        "by_party": dict(sorted(Counter(str(row.get("party") or "missing") for row in dict_rows).items())),
        "by_state": dict(sorted(Counter(str(row.get("state") or "missing") for row in dict_rows).items())),
        "by_in_office": dict(sorted(Counter(str(row.get("in_office") if "in_office" in row else "missing") for row in dict_rows).items())),
        "missing_identity_fields": {
            "bioguide_id": sum(1 for row in dict_rows if not _has_text(row.get("bioguide_id"))),
            "lis_id": sum(1 for row in dict_rows if not _has_text(row.get("lis_id"))),
            "slug": sum(1 for row in dict_rows if not _has_text(row.get("slug"))),
            "name_display": sum(1 for row in dict_rows if not _has_text(row.get("name_display"))),
        },
    }


def _summarize_congress_member_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dict_rows = [row for row in rows if isinstance(row, dict)]
    chamber_counts = Counter()
    currentness = Counter()
    for row in dict_rows:
        chamber_counts[_latest_term_chamber(row)] += 1
        currentness[_term_currentness(row)] += 1
    return {
        "total": len(dict_rows),
        "by_chamber": dict(sorted(chamber_counts.items())),
        "by_party": dict(sorted(Counter(str(row.get("partyName") or "missing") for row in dict_rows).items())),
        "by_state": dict(sorted(Counter(str(row.get("state") or "missing") for row in dict_rows).items())),
        "by_currentness": dict(sorted(currentness.items())),
        "missing_identity_fields": {
            "bioguideId": sum(1 for row in dict_rows if not _has_text(row.get("bioguideId"))),
            "lisId": sum(1 for row in dict_rows if not _has_text(row.get("lisId"))),
            "slug": sum(1 for row in dict_rows if not _has_text(row.get("slug"))),
            "name": sum(1 for row in dict_rows if not _has_text(row.get("name"))),
        },
    }


def _artifact_summary(repo_root: Path, path: Path) -> dict[str, Any]:
    row = {
        "path": _rel(repo_root, path),
        "exists": path.exists(),
        "kind": path.suffix.lower().lstrip(".") or "file",
        "record_count": None,
        "notes": "",
    }
    if not path.exists():
        row["notes"] = "missing"
        return row
    if path.suffix.lower() == ".json":
        data = _load_json(path)
        row["record_count"] = _json_record_count(data)
        if isinstance(data, dict):
            notes = []
            for key in ("families", "family_summaries", "threshold_simulations"):
                if isinstance(data.get(key), list):
                    notes.append(f"{key}={len(data[key])}")
            row["notes"] = ", ".join(notes)
    elif path.suffix.lower() == ".csv":
        row["record_count"] = _csv_data_row_count(path)
    elif path.suffix.lower() == ".mjs":
        text = _safe_read_text(path)
        row["record_count"] = len(re.findall(r"voteRow\(", text))
        row["notes"] = "golden fixture vote rows counted by constructor calls"
    return row


def _is_review_manifest_candidate(path: Path) -> bool:
    name = path.name.lower()
    return any(token in name for token in ("manifest", "prewrite", "audit", "validation", "post_write"))


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_dicts(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_dicts(item)


def _latest_term_chamber(row: dict[str, Any]) -> str:
    terms = row.get("terms")
    items = []
    if isinstance(terms, dict):
        items = _as_list(terms.get("item"))
    if not items:
        return "missing"
    last = sorted(items, key=lambda item: int(item.get("startYear") or 0))[-1]
    return str(last.get("chamber") or "missing")


def _term_currentness(row: dict[str, Any]) -> str:
    terms = row.get("terms")
    items = []
    if isinstance(terms, dict):
        items = _as_list(terms.get("item"))
    if not items:
        return "missing_terms"
    latest = sorted(items, key=lambda item: int(item.get("startYear") or 0))[-1]
    end_year = latest.get("endYear")
    if end_year is None:
        return "no_end_year_present"
    try:
        return "ended_before_2026" if int(end_year) < 2026 else "ends_2026_or_later"
    except (TypeError, ValueError):
        return "unparseable_end_year"


def _infer_session(congress: Any, year: Any) -> int | None:
    try:
        congress_int = int(congress)
        year_int = int(year)
    except (TypeError, ValueError):
        return None
    start_year = 1789 + ((congress_int - 1) * 2)
    if year_int == start_year:
        return 1
    if year_int == start_year + 1:
        return 2
    return None


def _year_from_date(value: Any) -> str | None:
    match = re.search(r"\b(20\d{2}|19\d{2})\b", str(value or ""))
    return match.group(1) if match else None


def _is_official_url(url: str) -> bool:
    normalized = url.lower()
    return any(domain in normalized for domain in OFFICIAL_SOURCE_DOMAINS)


def _json_record_count(data: Any) -> int | None:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("members", "roll_calls", "votes", "families", "family_summaries", "candidate_rows", "included_roll_calls"):
            if isinstance(data.get(key), list):
                return len(data[key])
        return len(data)
    return None


def _csv_data_row_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return max(sum(1 for _ in csv.reader(handle)) - 1, 0)
    except OSError:
        return 0


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
    return str(value).replace("|", "\\|")


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _sample_values(rows: list[dict[str, Any]], key: str, *, limit: int) -> list[str]:
    values = []
    for row in rows:
        value = row.get(key)
        if _has_text(value):
            values.append(str(value))
        if len(values) >= limit:
            break
    return values


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


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


def _sorted_files(root: Path, pattern: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob(pattern), key=lambda path: path.as_posix())


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    raise SystemExit(main())
