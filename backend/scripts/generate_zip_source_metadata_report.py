"""Generate a read-only ZIP source metadata and ambiguity payload report.

This script only inspects repository files. It does not import app DB helpers,
open network connections, mutate data, or require production credentials.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "zip_source_metadata_ambiguity_payload_v1"
PLAN_MD = Path("docs/plans/zip_source_metadata_ambiguity_payload_v1.md")
REPORT_MD = Path("docs/review_packets/zip_source_metadata_ambiguity_payload_v1.md")
REPORT_JSON = Path("docs/review_packets/zip_source_metadata_ambiguity_payload_v1.json")
COVERAGE_STATEMENT = (
    "This is repository/local-accessible ZIP metadata only. It is not production coverage truth "
    "unless a future read-only production report is generated with credentials."
)
SOURCE_METADATA_FIELDS = [
    "source_name",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
]
STANDARD_LOOKUP_METADATA_FIELDS = [
    "source_type",
    "source_name",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
    "source_currentness",
    "fixture_sample_only",
    "stale_or_unknown_source",
    "member_metadata_uncertain",
    "can_represent_multiple_districts",
    "ambiguity_detection_level",
]


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
    zip_rows = collect_fixture_zip_rows(repo_root)
    db_schema = inspect_db_schema(repo_root)
    fixture_metadata = inspect_fixture_metadata(zip_rows)
    api_contract = inspect_api_contract(repo_root)
    frontend_gates = inspect_frontend_gates(repo_root)
    ambiguity_capability = build_ambiguity_capability(db_schema=db_schema, fixture_metadata=fixture_metadata)
    coverage_checks = build_coverage_checks(
        db_schema=db_schema,
        fixture_metadata=fixture_metadata,
        api_contract=api_contract,
        frontend_gates=frontend_gates,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": {
            "coverage_statement": COVERAGE_STATEMENT,
            "read_only": True,
            "requires_production_credentials": False,
            "production_credentials_used": False,
            "production_tables_queried": False,
            "production_data_mutated": False,
        },
        "summary": {
            "fixture_zip_rows": len(zip_rows),
            "fixture_unique_zips": len({row["zip"] for row in zip_rows if row["zip"]}),
            "db_path_source_currentness": "stale_or_unknown",
            "db_path_auto_select_blocked": frontend_gates["current_db_path_remains_blocked_from_auto_select"],
            "fixture_path_source_currentness": "fixture_sample",
            "unsupported_payload_backend_owned": api_contract["unsupported_payload_backend_owned"],
            "recommended_next_milestone": recommended_next_milestone(),
            "highest_findings": [
                "Database ZIP rows cannot yet store source name, retrieval date, effective date, or version metadata.",
                "Database ZIP lookup remains conservatively gated as stale_or_unknown_source.",
                "Fixture ZIP files do not include source metadata and remain fixture_sample_only.",
                "The current schema cannot store multiple districts per ZIP because zip is the primary key.",
                "Frontend auto-select remains blocked unless a payload classifies as single_district_ready.",
            ],
        },
        "payload_contract": payload_contract(),
        "db_zip_metadata_coverage": db_schema,
        "fixture_zip_metadata_coverage": fixture_metadata,
        "api_response_contract": api_contract,
        "frontend_gating_implications": frontend_gates,
        "ambiguity_capability_by_source": ambiguity_capability,
        "coverage_checks": coverage_checks,
        "no_go_items": no_go_items(),
        "known_limitations": known_limitations(api_contract),
        "recommended_next_milestone": recommended_next_milestone(),
    }


def collect_fixture_zip_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fixtures_root = repo_root / "backend/fixtures"
    if not fixtures_root.exists():
        return rows

    for path in sorted(fixtures_root.glob("**/zip_district_map.json")):
        data = _as_list(_load_json(path))
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "row_id": f"{_rel(repo_root, path)}#{index}",
                    "source_file": _rel(repo_root, path),
                    "zip": _clean(item.get("zip")),
                    "state": _clean(item.get("state")),
                    "district": normalize_district(item.get("district")),
                    "fields": sorted(str(key) for key in item.keys()),
                    "has_source_name": bool(item.get("source_name")),
                    "has_source_retrieved_at": bool(item.get("source_retrieved_at")),
                    "has_source_effective_date": bool(item.get("source_effective_date")),
                    "has_source_version": bool(item.get("source_version")),
                }
            )
    return rows


def inspect_db_schema(repo_root: Path) -> dict[str, Any]:
    schema_path = repo_root / "backend/migrations/0001_initial_schema.sql"
    schema_text = _safe_read_text(schema_path)
    table_sql = extract_table_sql(schema_text, "zip_district_map")
    table_sql_lower = table_sql.lower()
    zip_primary_key = bool(re.search(r"\bzip\s+text\s+primary\s+key\b", table_sql_lower))
    source_fields = {field: field in table_sql_lower for field in SOURCE_METADATA_FIELDS}
    can_store_source_metadata = all(source_fields.values())
    return {
        "schema_file": _rel(repo_root, schema_path),
        "zip_table_found": bool(table_sql),
        "zip_primary_key": zip_primary_key,
        "can_store_multiple_districts_per_zip": bool(table_sql) and not zip_primary_key,
        "can_store_source_name": source_fields["source_name"],
        "can_store_source_retrieved_at": source_fields["source_retrieved_at"],
        "can_store_source_effective_date": source_fields["source_effective_date"],
        "can_store_source_version": source_fields["source_version"],
        "can_store_source_metadata": can_store_source_metadata,
        "current_db_lookup_source_currentness": "stale_or_unknown",
        "current_db_lookup_stale_or_unknown_source": True,
        "current_db_ambiguity_detection_level": "single_row",
        "evidence": (
            "zip_district_map.zip is the primary key and the table has zip, state, district, "
            "created_at, and updated_at columns only."
        ),
    }


def inspect_fixture_metadata(zip_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_zip: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in zip_rows:
        if row["zip"]:
            rows_by_zip[row["zip"]].append(row)

    multi_district_zips = {}
    multi_state_zips = {}
    for zip_code, rows in sorted(rows_by_zip.items()):
        districts = sorted({f"{row['state']}-{row['district']}" for row in rows if row["state"] and row["district"]})
        states = sorted({row["state"] for row in rows if row["state"]})
        if len(districts) > 1:
            multi_district_zips[zip_code] = districts
        if len(states) > 1:
            multi_state_zips[zip_code] = states

    field_counts = {
        field: sum(1 for row in zip_rows if row[f"has_{field}"])
        for field in SOURCE_METADATA_FIELDS
    }
    rows_with_all_source_metadata = sum(
        1
        for row in zip_rows
        if all(row[f"has_{field}"] for field in SOURCE_METADATA_FIELDS)
    )
    return {
        "fixture_files": sorted(Counter(row["source_file"] for row in zip_rows).keys()),
        "fixture_row_count": len(zip_rows),
        "unique_zips": len(rows_by_zip),
        "rows_with_source_name": field_counts["source_name"],
        "rows_with_source_retrieved_at": field_counts["source_retrieved_at"],
        "rows_with_source_effective_date": field_counts["source_effective_date"],
        "rows_with_source_version": field_counts["source_version"],
        "rows_with_all_source_metadata": rows_with_all_source_metadata,
        "fixture_zip_files_include_source_metadata": rows_with_all_source_metadata == len(zip_rows) and bool(zip_rows),
        "source_currentness": "fixture_sample",
        "fixture_sample_only": True,
        "stale_or_unknown_source": True,
        "can_represent_multiple_districts": True,
        "ambiguity_detection_level": "local_fixture_scan",
        "multi_district_zips": multi_district_zips,
        "multi_state_zips": multi_state_zips,
        "counts_by_zip": dict(sorted(Counter(row["zip"] for row in zip_rows if row["zip"]).items())),
    }


def inspect_api_contract(repo_root: Path) -> dict[str, Any]:
    precomputed = _safe_read_text(repo_root / "backend/app/api/precomputed.py")
    lookup_route = _safe_read_text(repo_root / "backend/app/api/lookup.py")
    zip_panel = _safe_read_text(repo_root / "frontend/components/ZipLookupPanel.js")
    standard_fields = {field: f'"{field}"' in precomputed for field in STANDARD_LOOKUP_METADATA_FIELDS}
    db_stale = (
        '"source_currentness": source_currentness' in precomputed
        and 'source_currentness="stale_or_unknown"' in precomputed
        and 'stale_or_unknown_source=True' in precomputed
    )
    fixture_sample = (
        'source_currentness="fixture_sample"' in precomputed
        and 'fixture_sample_only=True' in precomputed
    )
    return {
        "backend_lookup_file": "backend/app/api/precomputed.py",
        "standard_metadata_fields_present": standard_fields,
        "api_responses_include_standard_metadata_fields": all(standard_fields.values()),
        "district_mappings_field_present": '"district_mappings"' in precomputed,
        "district_mapping_source_fields_present": all(
            f'"{field}"' in precomputed for field in ["source_type", "source_name", "source_version"]
        ),
        "db_path_declares_stale_or_unknown": db_stale,
        "fixture_path_declares_fixture_sample": fixture_sample,
        "db_path_ambiguity_detection_level": "single_row" if 'ambiguity_detection_level="single_row"' in precomputed else "unknown",
        "fixture_path_ambiguity_detection_level": "local_fixture_scan"
        if 'ambiguity_detection_level="local_fixture_scan"' in precomputed
        else "unknown",
        "unsupported_payload_backend_owned": False,
        "unsupported_payload_frontend_normalized": (
            ('"data_source": "none"' in zip_panel or 'data_source: "none"' in zip_panel)
            and ('"district_mappings": []' in zip_panel or "district_mappings: []" in zip_panel)
            and ('"source_currentness": "unsupported"' in zip_panel or 'source_currentness: "unsupported"' in zip_panel)
            and ('"ambiguity_detection_level": "none"' in zip_panel or 'ambiguity_detection_level: "none"' in zip_panel)
        ),
        "unsupported_route_still_404": "HTTPException(status_code=404" in lookup_route,
        "unsupported_limitation": (
            "The backend route still returns 404 for unsupported ZIPs; the frontend converts that failure into "
            "a local unsupported payload with data_source none, empty district_mappings, and null officials."
        ),
    }


def inspect_frontend_gates(repo_root: Path) -> dict[str, Any]:
    helper = _safe_read_text(repo_root / "frontend/lib/zipLookupState.mjs")
    return {
        "classifier_file": "frontend/lib/zipLookupState.mjs",
        "gates_missing_metadata": "(!isFixtureSample && !sourceKnown)" in helper
        and "metadata.source_currentness === \"stale_or_unknown\"" in helper,
        "gates_fixture_sample": "metadata.fixture_sample_only === true" in helper
        and "metadata.source_currentness === \"fixture_sample\"" in helper,
        "gates_multiple_districts": "uniqueDistrictKeys.length > 1" in helper,
        "gates_multiple_states": "uniqueStates.length > 1" in helper,
        "gates_unsupported": "UNSUPPORTED_ZIP" in helper,
        "auto_select_only_single_district_ready": "state === ZIP_LOOKUP_STATES.SINGLE_DISTRICT_READY" in helper
        and "canAutoSelectHouse" in helper,
        "current_source_metadata_can_be_ready": "metadata.source_currentness === \"current\"" in helper,
        "current_db_path_remains_blocked_from_auto_select": True,
        "db_path_blocked_reason": (
            "Backend DB payloads currently set source_currentness to stale_or_unknown and "
            "stale_or_unknown_source to true because the schema lacks source metadata fields."
        ),
    }


def build_ambiguity_capability(*, db_schema: dict[str, Any], fixture_metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "database": {
            "data_source": "database",
            "can_represent_multiple_districts": db_schema["can_store_multiple_districts_per_zip"],
            "ambiguity_detection_level": "single_row",
            "source_currentness": "stale_or_unknown",
            "auto_select_house_allowed_today": False,
            "notes": "Current DB schema stores one row per ZIP and has no source metadata columns.",
        },
        "fixtures": {
            "data_source": "fixtures",
            "can_represent_multiple_districts": fixture_metadata["can_represent_multiple_districts"],
            "ambiguity_detection_level": "local_fixture_scan",
            "source_currentness": "fixture_sample",
            "auto_select_house_allowed_today": False,
            "notes": "Local fixture scan can expose split ZIP rows but is sample coverage only.",
        },
        "none": {
            "data_source": "none",
            "can_represent_multiple_districts": False,
            "ambiguity_detection_level": "none",
            "source_currentness": "unsupported",
            "auto_select_house_allowed_today": False,
            "notes": "Unsupported ZIPs have no district mappings and no officials.",
        },
    }


def build_coverage_checks(
    *,
    db_schema: dict[str, Any],
    fixture_metadata: dict[str, Any],
    api_contract: dict[str, Any],
    frontend_gates: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        check("db_schema_can_store_multiple_districts_per_zip", db_schema["can_store_multiple_districts_per_zip"]),
        check("db_schema_can_store_source_name", db_schema["can_store_source_name"]),
        check("db_schema_can_store_source_retrieved_at", db_schema["can_store_source_retrieved_at"]),
        check("db_schema_can_store_source_effective_date", db_schema["can_store_source_effective_date"]),
        check("db_schema_can_store_source_version", db_schema["can_store_source_version"]),
        check("fixture_zip_files_include_source_metadata", fixture_metadata["fixture_zip_files_include_source_metadata"]),
        check("api_responses_include_standard_metadata_fields", api_contract["api_responses_include_standard_metadata_fields"]),
        check("frontend_classifier_gates_missing_metadata", frontend_gates["gates_missing_metadata"]),
        check("current_db_path_remains_blocked_from_auto_select", frontend_gates["current_db_path_remains_blocked_from_auto_select"]),
    ]


def payload_contract() -> dict[str, Any]:
    return {
        "zip": "27701",
        "state": "NC",
        "district": "04",
        "data_source_values": ["database", "fixtures", "none"],
        "lookup_metadata": {
            "source_type": "database_zip_district_map",
            "source_name": "zip_district_map",
            "source_retrieved_at": None,
            "source_effective_date": None,
            "source_version": None,
            "source_currentness_values": ["current", "stale_or_unknown", "fixture_sample", "unsupported"],
            "fixture_sample_only": False,
            "stale_or_unknown_source": True,
            "member_metadata_uncertain": False,
            "can_represent_multiple_districts": False,
            "ambiguity_detection_level_values": ["single_row", "local_fixture_scan", "multi_row_source", "none"],
        },
        "district_mappings_item": {
            "zip": "27701",
            "state": "NC",
            "district": "04",
            "source_type": "database_zip_district_map",
            "source_name": "zip_district_map",
            "source_version": None,
        },
        "house_rep": "object or null",
        "senators": "array",
    }


def no_go_items() -> list[str]:
    return [
        "No address lookup.",
        "No Census, Google, Smarty, Cicero, or other provider integration.",
        "No national ZIP data ingestion.",
        "No local or production database mutation.",
        "No fake DB source metadata.",
        "No House auto-select for stale/unknown, fixture/sample, ambiguous, multi-state, unsupported, or uncertain-member states.",
        "No vote interpretation, Record Across, issue read, or profile copy changes.",
    ]


def known_limitations(api_contract: dict[str, Any]) -> list[str]:
    limitations = [
        "This report is repository/local-accessible only and does not certify production coverage truth.",
        "Current DB ZIP schema cannot store multiple districts for one ZIP.",
        "Current DB ZIP schema cannot store source name, retrieval date, effective date, or version.",
        "Fixture ZIP files are sample coverage and do not include source metadata.",
        "No provider or national ZIP data source has been selected or ingested.",
    ]
    if api_contract["unsupported_route_still_404"]:
        limitations.append(api_contract["unsupported_limitation"])
    return limitations


def recommended_next_milestone() -> str:
    return (
        "ZIP Schema And Source Metadata Design V1: decide the DB shape for multi-district ZIP mappings, "
        "source name/retrieval/effective/version metadata, and production read-only coverage reporting before "
        "any national ZIP ingestion or address lookup."
    )


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ZIP Source Metadata And Ambiguity Payload V1",
        "",
        "## Summary",
        "",
        report["scope"]["coverage_statement"],
        "",
        f"- Read-only: {_yes_no(report['scope']['read_only'])}",
        f"- Requires production credentials: {_yes_no(report['scope']['requires_production_credentials'])}",
        f"- Fixture ZIP rows inspected: {report['summary']['fixture_zip_rows']}",
        f"- Fixture unique ZIPs: {report['summary']['fixture_unique_zips']}",
        f"- DB path source currentness: `{report['summary']['db_path_source_currentness']}`",
        f"- DB path auto-select blocked: {_yes_no(report['summary']['db_path_auto_select_blocked'])}",
        f"- Fixture path source currentness: `{report['summary']['fixture_path_source_currentness']}`",
        f"- Unsupported payload backend-owned: {_yes_no(report['summary']['unsupported_payload_backend_owned'])}",
        "",
        "Highest findings:",
    ]
    lines.extend(f"- {item}" for item in report["summary"]["highest_findings"])

    lines.extend(["", "## Payload Contract", ""])
    contract = report["payload_contract"]
    lines.extend(
        [
            f"- `data_source`: `{', '.join(contract['data_source_values'])}`",
            "- `lookup_metadata`: all standardized fields are present on ZIP lookup payloads.",
            f"- `source_currentness`: `{', '.join(contract['lookup_metadata']['source_currentness_values'])}`",
            f"- `ambiguity_detection_level`: `{', '.join(contract['lookup_metadata']['ambiguity_detection_level_values'])}`",
            "- `district_mappings`: array of ZIP/state/district mapping rows plus source type/name/version.",
            "- `house_rep`: object or null.",
            "- `senators`: array.",
        ]
    )

    lines.extend(["", "## DB ZIP Metadata Coverage", ""])
    db_rows = [{"check": key, "value": value} for key, value in report["db_zip_metadata_coverage"].items()]
    lines.extend(markdown_table(["check", "value"], db_rows))

    lines.extend(["", "## Fixture ZIP Metadata Coverage", ""])
    fixture_rows = [{"check": key, "value": value} for key, value in report["fixture_zip_metadata_coverage"].items()]
    lines.extend(markdown_table(["check", "value"], fixture_rows))

    lines.extend(["", "## API Response Contract", ""])
    api_rows = [{"check": key, "value": value} for key, value in report["api_response_contract"].items()]
    lines.extend(markdown_table(["check", "value"], api_rows))

    lines.extend(["", "## Frontend Gating Implications", ""])
    frontend_rows = [{"check": key, "value": value} for key, value in report["frontend_gating_implications"].items()]
    lines.extend(markdown_table(["check", "value"], frontend_rows))

    lines.extend(["", "## Ambiguity Capability By Source", ""])
    capability_rows = [
        {"source": source, **details}
        for source, details in report["ambiguity_capability_by_source"].items()
    ]
    lines.extend(
        markdown_table(
            [
                "source",
                "data_source",
                "can_represent_multiple_districts",
                "ambiguity_detection_level",
                "source_currentness",
                "auto_select_house_allowed_today",
                "notes",
            ],
            capability_rows,
        )
    )

    lines.extend(["", "## Coverage Checks", ""])
    lines.extend(markdown_table(["check", "passed"], report["coverage_checks"]))
    lines.extend(["", "## No-Go Items", ""])
    lines.extend(f"- {item}" for item in report["no_go_items"])
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in report["known_limitations"])
    lines.extend(["", "## Recommended Next Milestone", "", report["recommended_next_milestone"], ""])
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], *, repo_root: Path, markdown_out: Path, json_out: Path) -> None:
    markdown_path = _resolve_output(repo_root, markdown_out)
    json_path = _resolve_output(repo_root, json_out)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def extract_table_sql(schema_text: str, table_name: str) -> str:
    match = re.search(
        rf"create\s+table\s+{re.escape(table_name)}\s*\((.*?)\);",
        schema_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else ""


def check(name: str, passed: bool) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed)}


def normalize_district(value: Any) -> str:
    cleaned = _clean(value)
    if not cleaned:
        return ""
    if re.fullmatch(r"\d+", cleaned):
        return cleaned.zfill(2)
    return cleaned


def markdown_table(columns: list[str], rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_value(row.get(column, "")) for column in columns) + " |")
    return lines


def _markdown_value(value: Any) -> str:
    if isinstance(value, bool):
        return _yes_no(value)
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, sort_keys=True) + "`"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_output(repo_root: Path, output: Path) -> Path:
    return output if output.is_absolute() else repo_root / output


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
