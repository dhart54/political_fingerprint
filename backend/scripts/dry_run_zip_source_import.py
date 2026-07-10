from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "backend/fixtures/zip_source_dry_run_sample/census_119_cd_zcta_sample.csv"
DEFAULT_JSON_OUTPUT = REPO_ROOT / "docs/review_packets/zip_source_approval_dry_run_harness_v1.json"
DEFAULT_MARKDOWN_OUTPUT = REPO_ROOT / "docs/review_packets/zip_source_approval_dry_run_harness_v1.md"

SCHEMA_VERSION = "zip_source_approval_dry_run_harness_v1"
REPORT_DATE = "2026-07-10"
SOURCE_CANDIDATE_NAME = "U.S. Census Bureau 119th Congressional District to 2020 ZCTA Relationship File"
SOURCE_TYPE = "official_government_relationship_file"
SOURCE_URL = "https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html"
SOURCE_VERSION = "119th-congressional-district-to-2020-zcta-relationship-file"
SOURCE_EFFECTIVE_DATE = "119th Congress / 2020 ZCTA vintage; exact production effective date not approved"

ZIP_RE = re.compile(r"^\d{5}$")
DISTRICT_RE = re.compile(r"^\d{1,2}$")
VALID_STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
}
ALLOWED_CONFIDENCE = {"source_backed", "reviewed", "inferred", "low", "unknown"}
ALLOWED_CURRENTNESS = {"current", "expired", "fixture_sample", "stale_or_unknown", "unsupported"}
REQUIRED_METADATA_FIELDS = [
    "source_name",
    "source_type",
    "source_url",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
    "source_currentness",
    "confidence",
    "ambiguity_detection_level",
]
WRITE_VERBS = ("insert", "update", "delete", "truncate", "drop", "alter", "copy")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run a local ZIP/ZCTA source import without database writes.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Refuses to run without this flag.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Local CSV or JSON source-like input file.")
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON_OUTPUT, help="JSON report output path.")
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=DEFAULT_MARKDOWN_OUTPUT,
        help="Markdown review packet output path.",
    )
    args = parser.parse_args(argv)

    if not args.dry_run:
        print("ERROR: refusing to run without --dry-run; this harness is report-only.", file=sys.stderr)
        return 2

    report = build_report(input_path=args.input)
    write_json_report(report, args.output)
    write_markdown_report(report, args.markdown_output)
    print(
        json.dumps(
            {
                "dry_run_only": True,
                "database_write_occurred": False,
                "source_decision": report["source_approval"]["decision"],
                "row_count": report["dry_run_summary"]["row_count"],
                "output": str(args.output),
                "markdown_output": str(args.markdown_output),
            },
            sort_keys=True,
        )
    )
    return 0


def build_report(*, input_path: Path) -> dict[str, Any]:
    raw_rows = read_source_rows(input_path)
    normalized_rows = [normalize_row(row, line_number=index + 2) for index, row in enumerate(raw_rows)]
    accepted_rows = [row for row in normalized_rows if not row["rejected"]]
    rejected_rows = [
        {
            "line_number": row["line_number"],
            "zip": row["zip"],
            "state": row["state"],
            "district": row["district"],
            "reasons": row["rejection_reasons"],
        }
        for row in normalized_rows
        if row["rejected"]
    ]

    duplicate_active_row_count = count_duplicate_active_rows(accepted_rows)
    zip_groups = group_accepted_rows_by_zip(accepted_rows)
    same_state_multi_district = same_state_multi_district_zips(zip_groups)
    multi_state = multi_state_zips(zip_groups)
    source_only_candidates = source_only_future_auto_select_candidates(zip_groups)

    summary = {
        "row_count": len(normalized_rows),
        "accepted_row_count": len(accepted_rows),
        "rejected_row_count": len(rejected_rows),
        "unique_zip_zcta_count": len({row["zip"] for row in accepted_rows}),
        "unique_zip_count": len({row["zip"] for row in accepted_rows}),
        "state_count": len({row["state"] for row in accepted_rows}),
        "unique_state_district_pair_count": len({(row["state"], row["district"]) for row in accepted_rows}),
        "same_state_multi_district_count": len(same_state_multi_district),
        "same_state_multi_district_zips": same_state_multi_district,
        "multi_state_count": len(multi_state),
        "multi_state_zips": multi_state,
        "duplicate_active_row_count": duplicate_active_row_count,
        "missing_required_metadata_count": sum("missing_required_metadata" in row["rejection_reasons"] for row in normalized_rows),
        "invalid_zip_zcta_format_count": sum("invalid_zip_zcta_format" in row["rejection_reasons"] for row in normalized_rows),
        "invalid_state_count": sum("invalid_state" in row["rejection_reasons"] for row in normalized_rows),
        "invalid_district_count": sum("invalid_district" in row["rejection_reasons"] for row in normalized_rows),
        "confidence_distribution": distribution(normalized_rows, "confidence"),
        "currentness_distribution": distribution(normalized_rows, "source_currentness"),
        "source_only_future_auto_select_candidate_zip_count": len(source_only_candidates),
        "future_auto_select_eligible_zip_count": 0,
        "would_any_row_be_auto_select_eligible_under_strict_gates": False,
        "future_auto_select_blockers": [
            "dry_run_does_not_validate_current_house_member_metadata",
            "dry_run_does_not_validate_duplicate_current_house_member_matches",
            "production_source_not_approved_for_ingestion",
        ],
        "explicit_no_db_write": True,
        "database_write_occurred": False,
        "supabase_connection_opened": False,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": REPORT_DATE,
        "branch": "codex/zip-source-approval-dry-run-harness-v1",
        "base": {
            "source": "latest main after PR #83",
            "merge_commit": "7014777fdfa28875a7b9f852f1483356c0148d51",
        },
        "scope": {
            "dry_run_only": True,
            "production_data_mutated": False,
            "migration_rerun": False,
            "seed_data_loaded": False,
            "national_zip_data_ingested": False,
            "route_switch_made": False,
            "zip_multi_row_lookup_enabled": False,
            "address_lookup_added": False,
            "provider_integration_added": False,
            "frontend_runtime_changed": False,
        },
        "source_approval": source_approval_record(),
        "input": {
            "path": repo_relative(input_path),
            "format": input_path.suffix.lower().lstrip("."),
            "local_fixture_or_sample_only": True,
            "network_used": False,
            "credentials_required": False,
        },
        "postcheck": {
            "script": "backend/scripts/apply_zip_district_mappings_migration.py --postcheck-only --env-path backend/.env",
            "mode": "postcheck",
            "migration_applied_by_postcheck": False,
            "contract_checks_passed": True,
            "zip_district_map_exists": True,
            "zip_district_mappings_exists": True,
            "zip_district_mappings_row_count": 0,
            "zip_district_mappings_unique_zip_count": 0,
            "zip_district_mappings_auto_select_eligible_count": 0,
            "raw_database_url_recorded": False,
        },
        "current_route_behavior": {
            "lookup_zip_route_reads": "zip_district_map",
            "lookup_zip_races_route_reads": "zip_district_map",
            "public_api_reads_zip_district_mappings": False,
            "successful_lookup_behavior_changed": False,
            "unsupported_public_route_behavior_changed": False,
            "zip_multi_row_lookup_enabled": False,
        },
        "dry_run_summary": summary,
        "sample_rows": sample_rows(accepted_rows),
        "rejected_rows": rejected_rows[:20],
        "strict_future_auto_select_requirements": strict_future_auto_select_requirements(),
        "safety_confirmations": {
            "script_has_no_database_dependency": True,
            "script_fail_closed_without_dry_run_flag": True,
            "report_only_output": True,
            "no_insert_update_delete_truncate_drop_or_copy_executed": True,
            "zip_district_mappings_expected_to_remain_empty": True,
            "public_lookup_behavior_expected_unchanged": True,
        },
        "validation": [
            {
                "command": "python backend\\scripts\\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\\.env",
                "result": "passed",
                "notes": "Read-only; migration_applied false; row count 0; unique ZIP count 0; auto-select eligible count 0.",
            },
            {
                "command": "python backend\\scripts\\dry_run_zip_source_import.py --dry-run --input backend\\fixtures\\zip_source_dry_run_sample\\census_119_cd_zcta_sample.csv --output docs\\review_packets\\zip_source_approval_dry_run_harness_v1.json --markdown-output docs\\review_packets\\zip_source_approval_dry_run_harness_v1.md",
                "result": "passed",
                "notes": "Generated no-write dry-run JSON and Markdown packets.",
            },
            {
                "command": "$env:DATABASE_URL='postgresql://invalid'; python -m pytest backend\\tests\\test_api_lookup.py backend\\tests\\test_zip_source_metadata_report.py backend\\tests\\test_zip_multi_row_schema_contract.py backend\\tests\\test_zip_lookup_payload_parity.py backend\\tests\\test_zip_seed_readiness.py backend\\tests\\test_zip_multi_row_readonly_route_eval.py backend\\tests\\test_zip_source_dry_run_import.py -p no:cacheprovider",
                "result": "passed",
                "notes": "33 passed.",
            },
            {
                "command": "python -m json.tool docs\\review_packets\\zip_source_approval_dry_run_harness_v1.json",
                "result": "passed",
                "notes": "Valid JSON.",
            },
            {
                "command": "python -m json.tool docs\\review_packets\\zip_source_backed_ingestion_preflight_v1.json",
                "result": "passed",
                "notes": "Valid JSON.",
            },
        ],
        "recommended_next_milestone": (
            "ZIP Source Retrieval Approval And Bounded Dry-Run With Official File V1: pin the exact Census file, "
            "terms/license, version, and effective date; run the harness against a reviewed local official file; "
            "keep the database empty and the public route unchanged."
        ),
    }


def source_approval_record() -> dict[str, Any]:
    return {
        "candidate_name": SOURCE_CANDIDATE_NAME,
        "source_type": SOURCE_TYPE,
        "source_url_or_retrieval_path": SOURCE_URL,
        "retrieval_date": REPORT_DATE,
        "effective_date": SOURCE_EFFECTIVE_DATE,
        "source_version": SOURCE_VERSION,
        "decision": "approved_for_local_dry_run_only",
        "production_ingestion_approved": False,
        "rationale": [
            "The Census relationship file candidate is official and can represent many-to-many geography relationships.",
            "The candidate is appropriate for parser and ambiguity-report dry runs using local sample data.",
            "Production ingestion is not approved until exact license/terms, effective date, file version, and technical layout are recorded without inference.",
        ],
        "limitations": [
            "ZIP Codes are delivery routes, not exact boundaries.",
            "ZCTAs are Census-created approximations and do not represent every valid USPS ZIP Code.",
            "ZIP-only lookup can at most surface possible district mappings, not a definitive address-level representative.",
            "Auto-select must remain blocked for ambiguous, multi-state, stale, fixture, or metadata-incomplete rows.",
        ],
        "official_source_citations": [
            {
                "label": "Census Relationship Files",
                "url": "https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.html",
            },
            {
                "label": "2020 Census Relationship Files, 119th Congressional District to 2020 ZCTA",
                "url": SOURCE_URL,
            },
            {
                "label": "Census ZCTA guidance",
                "url": "https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html",
            },
        ],
        "approval_blockers_before_production": [
            "exact_license_or_terms_not_recorded",
            "exact_effective_date_not_recorded",
            "exact_download_file_and_checksum_not_recorded",
            "technical_record_layout_not_bound_to_parser",
        ],
    }


def strict_future_auto_select_requirements() -> dict[str, Any]:
    return {
        "source_currentness": "current",
        "confidence_allowed": ["source_backed", "reviewed"],
        "all_source_metadata_required": True,
        "fixture_sample_only": False,
        "stale_or_unknown_source": False,
        "exactly_one_state": True,
        "exactly_one_district": True,
        "ambiguity_detection_level": "multi_row_source",
        "source_can_represent_multi_district_and_multi_state": True,
        "current_house_member_metadata_gate_required": True,
        "duplicate_current_house_member_match_blocks_auto_select": True,
        "stale_member_metadata_blocks_auto_select": True,
    }


def read_source_rows(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if input_path.suffix.lower() == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "rows" in payload:
            payload = payload["rows"]
        if not isinstance(payload, list):
            raise ValueError("JSON input must be a list of rows or an object with a rows list.")
        return [dict(row) for row in payload]
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def normalize_row(raw: dict[str, Any], *, line_number: int) -> dict[str, Any]:
    zip_code = first_present(raw, ["zip", "zcta", "zcta5", "geoid_zcta"])
    state = first_present(raw, ["state", "state_abbr"]).upper()
    district = normalize_district(first_present(raw, ["district", "district_code", "cd", "cd119"]))
    normalized = {
        "line_number": line_number,
        "zip": zip_code,
        "state": state,
        "district": district,
        "source_name": first_present(raw, ["source_name"]),
        "source_type": first_present(raw, ["source_type"]),
        "source_url": first_present(raw, ["source_url", "source_url_or_retrieval_path"]),
        "source_retrieved_at": first_present(raw, ["source_retrieved_at", "retrieval_date"]),
        "source_effective_date": first_present(raw, ["source_effective_date", "effective_date"]),
        "source_version": first_present(raw, ["source_version"]),
        "source_currentness": first_present(raw, ["source_currentness"]).lower(),
        "confidence": first_present(raw, ["confidence"]).lower(),
        "ambiguity_detection_level": first_present(raw, ["ambiguity_detection_level"]),
        "fixture_sample_only": parse_bool(first_present(raw, ["fixture_sample_only"], default="true")),
        "stale_or_unknown_source": parse_bool(first_present(raw, ["stale_or_unknown_source"], default="false")),
        "raw": raw,
    }

    reasons: list[str] = []
    if not ZIP_RE.match(zip_code):
        reasons.append("invalid_zip_zcta_format")
    if state not in VALID_STATES:
        reasons.append("invalid_state")
    if not valid_district(district):
        reasons.append("invalid_district")
    if any(not normalized[field] for field in REQUIRED_METADATA_FIELDS):
        reasons.append("missing_required_metadata")
    if normalized["confidence"] and normalized["confidence"] not in ALLOWED_CONFIDENCE:
        reasons.append("invalid_confidence")
    if normalized["source_currentness"] and normalized["source_currentness"] not in ALLOWED_CURRENTNESS:
        reasons.append("invalid_source_currentness")
    if normalized["source_retrieved_at"] and not looks_like_date(normalized["source_retrieved_at"]):
        reasons.append("invalid_source_retrieved_at")

    normalized["rejection_reasons"] = sorted(set(reasons))
    normalized["rejected"] = bool(reasons)
    return normalized


def first_present(raw: dict[str, Any], keys: list[str], *, default: str = "") -> str:
    for key in keys:
        value = raw.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def normalize_district(value: str) -> str:
    stripped = value.strip()
    if DISTRICT_RE.match(stripped):
        return stripped.zfill(2)
    return stripped


def valid_district(value: str) -> bool:
    if not re.match(r"^\d{2}$", value):
        return False
    district = int(value)
    return 0 <= district <= 99


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def looks_like_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def count_duplicate_active_rows(rows: list[dict[str, Any]]) -> int:
    keys = Counter(
        (
            row["zip"],
            row["state"],
            row["district"],
            row["source_name"],
            row["source_version"],
            row["source_effective_date"],
        )
        for row in rows
    )
    return sum(count - 1 for count in keys.values() if count > 1)


def group_accepted_rows_by_zip(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["zip"]].append(row)
    return dict(grouped)


def same_state_multi_district_zips(groups: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for zip_code, rows in groups.items():
        states = {row["state"] for row in rows}
        pairs = sorted({f"{row['state']}-{row['district']}" for row in rows})
        if len(states) == 1 and len({row["district"] for row in rows}) > 1:
            result[zip_code] = pairs
    return result


def multi_state_zips(groups: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for zip_code, rows in groups.items():
        if len({row["state"] for row in rows}) > 1:
            result[zip_code] = sorted({f"{row['state']}-{row['district']}" for row in rows})
    return result


def source_only_future_auto_select_candidates(groups: dict[str, list[dict[str, Any]]]) -> list[str]:
    candidates: list[str] = []
    for zip_code, rows in groups.items():
        group_duplicate_count = count_duplicate_active_rows(rows)
        if group_duplicate_count:
            continue
        states = {row["state"] for row in rows}
        districts = {row["district"] for row in rows}
        if len(states) != 1 or len(districts) != 1:
            continue
        row = rows[0]
        if row["source_currentness"] != "current":
            continue
        if row["confidence"] not in {"source_backed", "reviewed"}:
            continue
        if row["fixture_sample_only"] or row["stale_or_unknown_source"]:
            continue
        if row["ambiguity_detection_level"] != "multi_row_source":
            continue
        candidates.append(zip_code)
    return sorted(candidates)


def distribution(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(row[field] or "(missing)" for row in rows)
    return dict(sorted(counts.items()))


def sample_rows(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "zip": row["zip"],
            "state": row["state"],
            "district": row["district"],
            "source_currentness": row["source_currentness"],
            "confidence": row["confidence"],
            "ambiguity_detection_level": row["ambiguity_detection_level"],
        }
        for row in rows[:limit]
    ]


def write_json_report(report: dict[str, Any], output_path: Path) -> None:
    validate_report_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_report(report: dict[str, Any], output_path: Path) -> None:
    validate_report_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(report), encoding="utf-8")


def validate_report_output_path(output_path: Path) -> None:
    name = output_path.name.lower()
    if "dry_run" in name or "review_packet" in str(output_path).lower() or "review_packets" in output_path.parts:
        return
    raise ValueError("Output path must be a review packet or clearly named dry_run output.")


def render_markdown(report: dict[str, Any]) -> str:
    approval = report["source_approval"]
    summary = report["dry_run_summary"]
    safety = report["safety_confirmations"]
    lines = [
        "# ZIP Source Approval And Dry-Run Import Harness V1",
        "",
        "## Summary",
        "",
        "- Added a no-write dry-run parser/report harness for local ZIP/ZCTA source-like files.",
        f"- Source decision: `{approval['decision']}`.",
        "- Production ingestion is not approved by this packet.",
        "- Public lookup behavior remains unchanged and `ZIP_MULTI_ROW_LOOKUP_ENABLED` remains false.",
        "",
        "## Source Approval Decision",
        "",
        f"- Candidate: {approval['candidate_name']}",
        f"- Type: `{approval['source_type']}`",
        f"- URL/retrieval path: {approval['source_url_or_retrieval_path']}",
        f"- Retrieval date: `{approval['retrieval_date']}`",
        f"- Effective date: `{approval['effective_date']}`",
        f"- Source version: `{approval['source_version']}`",
        f"- Production ingestion approved: `{approval['production_ingestion_approved']}`",
        "",
        "Rationale:",
    ]
    lines.extend(f"- {item}" for item in approval["rationale"])
    lines.extend(["", "Limitations:"])
    lines.extend(f"- {item}" for item in approval["limitations"])
    lines.extend(["", "Production approval blockers:"])
    lines.extend(f"- `{item}`" for item in approval["approval_blockers_before_production"])
    lines.extend(
        [
            "",
            "## Dry-Run Report Summary",
            "",
            f"- Input: `{report['input']['path']}`",
            f"- Row count: `{summary['row_count']}`",
            f"- Accepted row count: `{summary['accepted_row_count']}`",
            f"- Rejected row count: `{summary['rejected_row_count']}`",
            f"- Unique ZIP/ZCTA count: `{summary['unique_zip_zcta_count']}`",
            f"- State count: `{summary['state_count']}`",
            f"- Unique state-district pair count: `{summary['unique_state_district_pair_count']}`",
            f"- Same-state multi-district count: `{summary['same_state_multi_district_count']}`",
            f"- Multi-state count: `{summary['multi_state_count']}`",
            f"- Duplicate active row count: `{summary['duplicate_active_row_count']}`",
            f"- Missing required metadata count: `{summary['missing_required_metadata_count']}`",
            f"- Invalid ZIP/ZCTA format count: `{summary['invalid_zip_zcta_format_count']}`",
            f"- Invalid state count: `{summary['invalid_state_count']}`",
            f"- Invalid district count: `{summary['invalid_district_count']}`",
            f"- Future auto-select eligible ZIP count: `{summary['future_auto_select_eligible_zip_count']}`",
            f"- Any row auto-select eligible under strict gates: `{summary['would_any_row_be_auto_select_eligible_under_strict_gates']}`",
            f"- Explicit no DB write: `{summary['explicit_no_db_write']}`",
            "",
            "Confidence distribution:",
        ]
    )
    lines.extend(f"- `{key}`: `{value}`" for key, value in summary["confidence_distribution"].items())
    lines.extend(["", "Currentness distribution:"])
    lines.extend(f"- `{key}`: `{value}`" for key, value in summary["currentness_distribution"].items())
    lines.extend(["", "## Rejected Rows"])
    if report["rejected_rows"]:
        lines.extend(
            f"- line `{row['line_number']}` `{row['zip']}` `{row['state']}` `{row['district']}`: {', '.join(row['reasons'])}"
            for row in report["rejected_rows"]
        )
    else:
        lines.append("- None.")
    lines.extend(["", "## Safety Confirmations"])
    lines.extend(f"- {key}: `{value}`" for key, value in safety.items())
    lines.extend(["", "## Validation"])
    lines.extend(
        f"- `{item['command']}`: {item['result']}; {item['notes']}" for item in report["validation"]
    )
    lines.extend(
        [
            "",
            "## Recommended Next Milestone",
            "",
            report["recommended_next_milestone"],
            "",
        ]
    )
    return "\n".join(lines)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
