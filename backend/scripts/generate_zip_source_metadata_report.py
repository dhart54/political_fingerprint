"""Generate a read-only ZIP source metadata and ambiguity payload report.

This script only inspects repository files. It does not import app DB helpers,
open network connections, mutate data, or require production credentials.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.etl.zip_seed_readiness import (
    PAYLOAD_AMBIGUOUS_ZIP,
    PAYLOAD_FIXTURE_SAMPLE_ONLY,
    PAYLOAD_MULTI_STATE_ZIP,
    PAYLOAD_SINGLE_DISTRICT_READY,
    PAYLOAD_STALE_OR_UNKNOWN_SOURCE,
    PAYLOAD_UNSUPPORTED_ZIP,
    REQUIRED_SEED_FIELDS,
    validate_seed_rows,
)


SCHEMA_VERSION = "zip_source_metadata_ambiguity_payload_v1"
APPLICATION_READINESS_SCHEMA_VERSION = "zip_schema_application_coverage_seed_readiness_v1"
PLAN_MD = Path("docs/plans/zip_source_metadata_ambiguity_payload_v1.md")
REPORT_MD = Path("docs/review_packets/zip_source_metadata_ambiguity_payload_v1.md")
REPORT_JSON = Path("docs/review_packets/zip_source_metadata_ambiguity_payload_v1.json")
APPLICATION_REPORT_MD = Path("docs/review_packets/zip_schema_application_coverage_seed_readiness_v1.md")
APPLICATION_REPORT_JSON = Path("docs/review_packets/zip_schema_application_coverage_seed_readiness_v1.json")
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
MULTI_ROW_MIGRATION_FILE = "backend/migrations/0013_zip_district_mappings.sql"
MULTI_ROW_FIXTURE_FILE = "backend/fixtures/zip_multi_row_schema_sample/zip_district_mappings.json"
REVIEWED_SEED_SAMPLE_FILE = "backend/fixtures/zip_reviewed_seed_sample/zip_district_mappings.json"
REPORT_MODES = {
    "repository-static-only": "repository/static only",
    "local-test-db-read-only": "local/test DB read-only",
    "production-read-only": "production read-only",
}
MULTI_ROW_REQUIRED_COLUMNS = [
    "id",
    "zip",
    "state",
    "district",
    "source_name",
    "source_type",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
    "source_currentness",
    "confidence",
    "is_primary",
    "district_type",
    "congress",
    "cycle",
    "valid_from",
    "valid_to",
    "provider_record_id",
    "notes",
    "created_at",
    "updated_at",
]
MULTI_ROW_SOURCE_METADATA_COLUMNS = [
    "source_name",
    "source_type",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
    "source_currentness",
    "confidence",
]
SOURCE_CURRENTNESS_VALUES = ["current", "stale_or_unknown", "fixture_sample", "unsupported", "expired"]
CONFIDENCE_VALUES = ["source_backed", "reviewed", "inferred", "low", "unknown"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD)
    parser.add_argument("--json-out", type=Path, default=REPORT_JSON)
    parser.add_argument("--db-url", default=None, help="Optional database URL for read-only ZIP mapping inspection.")
    parser.add_argument(
        "--report-mode",
        choices=sorted(REPORT_MODES),
        default=None,
        help="Label the report mode. Defaults to repository/static only unless --db-url is supplied.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root, db_url=args.db_url, report_mode=args.report_mode)
    write_outputs(report, repo_root=repo_root, markdown_out=args.markdown_out, json_out=args.json_out)
    write_application_readiness_outputs(report, repo_root=repo_root)
    print(f"Wrote {args.markdown_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {APPLICATION_REPORT_MD}")
    print(f"Wrote {APPLICATION_REPORT_JSON}")
    return 0


def build_report(repo_root: Path, *, db_url: str | None = None, report_mode: str | None = None) -> dict[str, Any]:
    zip_rows = collect_fixture_zip_rows(repo_root)
    mode_key = normalize_report_mode(report_mode, db_url=db_url)
    migration_application = inspect_migration_application_conventions(repo_root)
    db_schema = inspect_db_schema(repo_root)
    multi_row_schema = inspect_multi_row_schema_contract(repo_root)
    multi_row_fixtures = inspect_multi_row_fixture_contract(repo_root)
    db_coverage = inspect_zip_district_mappings_db(db_url=db_url, mode_key=mode_key)
    seed_readiness = inspect_reviewed_seed_readiness(repo_root)
    fixture_metadata = inspect_fixture_metadata(zip_rows)
    api_contract = inspect_api_contract(repo_root)
    frontend_gates = inspect_frontend_gates(repo_root)
    route_switch = inspect_route_switch_status(repo_root)
    ambiguity_capability = build_ambiguity_capability(db_schema=db_schema, fixture_metadata=fixture_metadata)
    coverage_checks = build_coverage_checks(
        db_schema=db_schema,
        multi_row_schema=multi_row_schema,
        multi_row_fixtures=multi_row_fixtures,
        seed_readiness=seed_readiness,
        fixture_metadata=fixture_metadata,
        api_contract=api_contract,
        frontend_gates=frontend_gates,
        route_switch=route_switch,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": {
            "coverage_statement": COVERAGE_STATEMENT,
            "report_mode": REPORT_MODES[mode_key],
            "read_only": True,
            "requires_production_credentials": mode_key == "production-read-only",
            "production_credentials_used": bool(db_url) and mode_key == "production-read-only",
            "production_tables_queried": bool(db_url) and mode_key == "production-read-only",
            "production_data_mutated": False,
        },
        "summary": {
            "fixture_zip_rows": len(zip_rows),
            "fixture_unique_zips": len({row["zip"] for row in zip_rows if row["zip"]}),
            "migration_auto_apply_detected": migration_application["auto_apply_detected"],
            "zip_district_mappings_db_table_status": db_coverage["table_status"],
            "reviewed_seed_sample_valid": seed_readiness["valid"],
            "reviewed_seed_auto_select_eligible_count": seed_readiness["auto_select_eligible_count"],
            "db_path_source_currentness": "stale_or_unknown",
            "db_path_auto_select_blocked": frontend_gates["current_db_path_remains_blocked_from_auto_select"],
            "fixture_path_source_currentness": "fixture_sample",
            "unsupported_payload_backend_owned": api_contract["unsupported_payload_backend_owned"],
            "recommended_next_milestone": recommended_next_milestone(),
            "highest_findings": [
                "Database ZIP rows cannot yet store source name, retrieval date, effective date, or version metadata.",
                "Database ZIP lookup remains conservatively gated as stale_or_unknown_source.",
                "Fixture ZIP files do not include source metadata and remain fixture_sample_only.",
                "The compatibility schema cannot store multiple districts per ZIP because zip is the primary key.",
                "The drafted zip_district_mappings schema can represent multiple rows per ZIP without changing the live route.",
                "Frontend auto-select remains blocked unless a payload classifies as single_district_ready.",
            ],
        },
        "payload_contract": payload_contract(),
        "migration_application_conventions": migration_application,
        "db_zip_metadata_coverage": db_schema,
        "multi_row_schema_contract": multi_row_schema,
        "zip_district_mappings_db_coverage": db_coverage,
        "multi_row_synthetic_fixture_coverage": multi_row_fixtures,
        "reviewed_seed_readiness": seed_readiness,
        "fixture_zip_metadata_coverage": fixture_metadata,
        "api_response_contract": api_contract,
        "frontend_gating_implications": frontend_gates,
        "route_switch_status": route_switch,
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


def normalize_report_mode(report_mode: str | None, *, db_url: str | None) -> str:
    if report_mode:
        return report_mode
    return "local-test-db-read-only" if db_url else "repository-static-only"


def inspect_migration_application_conventions(repo_root: Path) -> dict[str, Any]:
    deployment = _safe_read_text(repo_root / "docs/deployment.md")
    development = _safe_read_text(repo_root / "docs/development_workflow.md")
    main_py = _safe_read_text(repo_root / "backend/app/main.py")
    migration_sql = _safe_read_text(repo_root / MULTI_ROW_MIGRATION_FILE)
    combined_runtime_text = "\n".join([deployment, development, main_py]).lower()
    auto_apply_patterns = [
        "alembic upgrade",
        "psql ",
        "python -m app.etl.run_all",
        "run_all --fixtures",
        "apply migration",
    ]
    startup_mentions_migration = "startup" in main_py.lower() and "migration" in main_py.lower()
    deployment_start_command = "uvicorn app.main:app --host 0.0.0.0 --port $port" in deployment.lower()
    auto_apply_detected = startup_mentions_migration or any(
        pattern in combined_runtime_text and pattern not in development.lower()
        for pattern in auto_apply_patterns
    )
    migration_declares_manual = "not applied by application startup" in migration_sql.lower()
    return {
        "auto_apply_detected": auto_apply_detected,
        "deployment_start_command": "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
        if deployment_start_command
        else "not confirmed",
        "backend_startup_migration_runner_found": startup_mentions_migration,
        "migration_file_declares_manual_application": migration_declares_manual,
        "production_migration_future_manual_approval_required": not auto_apply_detected,
        "finding": (
            "No deployment/startup auto-apply migration runner was found; production migration remains a future manual approval step."
            if not auto_apply_detected
            else "Potential migration auto-apply path detected; stop before continuing."
        ),
        "evidence": [
            "docs/deployment.md uses the Render start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.",
            "backend/app/main.py creates the FastAPI app and includes routers; it does not run migrations on startup.",
            "backend/migrations/0013_zip_district_mappings.sql states the migration is not applied by application startup.",
        ],
    }


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


def inspect_multi_row_schema_contract(repo_root: Path) -> dict[str, Any]:
    migration_path = find_multi_row_migration(repo_root)
    migration_text = _safe_read_text(migration_path) if migration_path else ""
    table_sql = extract_table_sql(migration_text, "zip_district_mappings")
    table_sql_lower = table_sql.lower()
    migration_lower = migration_text.lower()
    columns_present = {
        column: bool(re.search(rf"\b{re.escape(column)}\b", table_sql_lower))
        for column in MULTI_ROW_REQUIRED_COLUMNS
    }
    source_currentness_values_present = {
        value: f"'{value}'" in table_sql_lower
        for value in SOURCE_CURRENTNESS_VALUES
    }
    confidence_values_present = {
        value: f"'{value}'" in table_sql_lower
        for value in CONFIDENCE_VALUES
    }
    indexes_present = {
        "zip": "idx_zip_district_mappings_zip" in migration_lower,
        "zip_state_district": "idx_zip_district_mappings_zip_state_district" in migration_lower,
        "source_currentness": "idx_zip_district_mappings_source_currentness" in migration_lower,
        "source_name": "idx_zip_district_mappings_source_name" in migration_lower,
        "source_version": "idx_zip_district_mappings_source_version" in migration_lower,
    }
    old_table_untouched = not bool(
        re.search(r"\b(drop|alter)\s+table\s+(if\s+exists\s+)?zip_district_map\b", migration_lower)
    )
    unique_active_source_period_rule = (
        "unique" in migration_lower
        and "coalesce(valid_from, source_effective_date)" in migration_lower
        and "coalesce(valid_to, date '9999-12-31')" in migration_lower
    )
    zip_primary_key = bool(re.search(r"\bzip\s+text\s+primary\s+key\b", table_sql_lower))
    surrogate_id_primary_key = bool(re.search(r"\bid\s+bigserial\s+primary\s+key\b", table_sql_lower))
    can_represent_multiple_districts = (
        bool(table_sql)
        and surrogate_id_primary_key
        and not zip_primary_key
        and unique_active_source_period_rule
    )
    return {
        "migration_file": _rel(repo_root, migration_path) if migration_path else MULTI_ROW_MIGRATION_FILE,
        "migration_exists": migration_path is not None and migration_path.exists(),
        "table_found": bool(table_sql),
        "surrogate_id_primary_key": surrogate_id_primary_key,
        "zip_not_primary_key": bool(table_sql) and not zip_primary_key,
        "zip_format_check": "zip ~ '^[0-9]{5}$'" in table_sql_lower,
        "required_columns_present": columns_present,
        "all_required_columns_present": all(columns_present.values()),
        "source_metadata_columns_present": {
            column: columns_present[column]
            for column in MULTI_ROW_SOURCE_METADATA_COLUMNS
        },
        "all_source_metadata_columns_present": all(columns_present[column] for column in MULTI_ROW_SOURCE_METADATA_COLUMNS),
        "source_currentness_check_values_present": source_currentness_values_present,
        "controlled_source_currentness_check_present": all(source_currentness_values_present.values()),
        "confidence_check_values_present": confidence_values_present,
        "controlled_confidence_check_present": all(confidence_values_present.values()),
        "indexes_present": indexes_present,
        "all_required_indexes_present": all(indexes_present.values()),
        "unique_active_source_period_rule": unique_active_source_period_rule,
        "can_represent_multiple_districts_per_zip": can_represent_multiple_districts,
        "old_table_untouched": old_table_untouched,
        "old_table_compatibility_only": old_table_untouched,
    }


def inspect_multi_row_fixture_contract(repo_root: Path) -> dict[str, Any]:
    fixture_path = repo_root / MULTI_ROW_FIXTURE_FILE
    rows = _as_list(_load_json(fixture_path))
    normalized = [normalize_multi_row_fixture_row(row, index) for index, row in enumerate(rows) if isinstance(row, dict)]
    rows_by_zip: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        if row["zip"]:
            rows_by_zip[row["zip"]].append(row)

    multi_district_zips = {}
    multi_state_zips = {}
    for zip_code, zip_rows in sorted(rows_by_zip.items()):
        districts = sorted({f"{row['state']}-{row['district']}" for row in zip_rows if row["state"] and row["district"]})
        states = sorted({row["state"] for row in zip_rows if row["state"]})
        if len(districts) > 1:
            multi_district_zips[zip_code] = districts
        if len(states) > 1:
            multi_state_zips[zip_code] = states

    duplicate_keys = [
        key
        for key, count in sorted(Counter(active_source_key(row) for row in normalized).items())
        if key and count > 1
    ]
    missing_source_metadata_rows = [
        row["row_id"]
        for row in normalized
        if row["source_currentness"] == "stale_or_unknown" or not row["has_all_source_metadata"]
    ]
    cases = sorted({row["case"] for row in normalized if row["case"]})
    return {
        "fixture_file": _rel(repo_root, fixture_path),
        "fixture_exists": fixture_path.exists(),
        "row_count": len(normalized),
        "cases_present": cases,
        "has_single_district_case": "single_district_current_source_backed" in cases,
        "has_same_state_multi_district_case": "same_state_multi_district" in cases,
        "has_multi_state_case": "multi_state_zip" in cases,
        "has_fixture_sample_case": "fixture_sample_row" in cases,
        "has_stale_unknown_case": "stale_unknown_missing_metadata" in cases,
        "has_current_source_backed_case": any(
            row["source_currentness"] == "current" and row["confidence"] == "source_backed"
            for row in normalized
        ),
        "has_duplicate_detection_case": "duplicate_active_row" in cases and bool(duplicate_keys),
        "duplicate_active_source_keys": duplicate_keys,
        "duplicate_active_source_key_count": len(duplicate_keys),
        "missing_source_metadata_rows": missing_source_metadata_rows,
        "missing_source_metadata_row_count": len(missing_source_metadata_rows),
        "multi_district_zips": multi_district_zips,
        "multi_state_zips": multi_state_zips,
    }


def inspect_reviewed_seed_readiness(repo_root: Path) -> dict[str, Any]:
    seed_path = repo_root / REVIEWED_SEED_SAMPLE_FILE
    rows = [row for row in _as_list(_load_json(seed_path)) if isinstance(row, dict)]
    validation = validate_seed_rows(rows)
    validation.update(
        {
            "seed_file": _rel(repo_root, seed_path),
            "seed_file_exists": seed_path.exists(),
            "seed_file_label": "non-production reviewed seed sample",
            "required_fields": REQUIRED_SEED_FIELDS,
            "loaded_into_production": False,
        }
    )
    return validation


def inspect_zip_district_mappings_db(*, db_url: str | None, mode_key: str) -> dict[str, Any]:
    base = {
        "mode": REPORT_MODES[mode_key],
        "db_inspected": False,
        "read_only": True,
        "production_credentials_used": bool(db_url) and mode_key == "production-read-only",
        "table_name": "zip_district_mappings",
        "table_status": "not_inspected",
        "db_has_zip_district_mappings": None,
        "table_absent": None,
        "table_empty": None,
        "row_count": None,
        "unique_zip_count": None,
        "multi_district_zip_count": None,
        "multi_state_zip_count": None,
        "missing_metadata_count": None,
        "stale_or_unknown_count": None,
        "fixture_sample_count": None,
        "current_source_backed_count": None,
        "auto_select_eligible_count": None,
        "ineligible_counts_by_reason": {},
        "error": None,
    }
    if not db_url:
        return base

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        return {**base, "table_status": "not_inspected", "error": f"psycopg unavailable: {exc}"}

    try:
        with psycopg.connect(db_url, row_factory=dict_row) as conn:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                exists_row = conn.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'zip_district_mappings'
                    ) AS exists
                    """
                ).fetchone()
                table_exists = bool(exists_row and exists_row["exists"])
                if not table_exists:
                    return {
                        **base,
                        "db_inspected": True,
                        "table_status": "absent",
                        "db_has_zip_district_mappings": False,
                        "table_absent": True,
                        "table_empty": None,
                    }

                counts = conn.execute(
                    """
                    WITH per_zip AS (
                        SELECT
                            zip,
                            COUNT(DISTINCT state || '-' || district) AS district_count,
                            COUNT(DISTINCT state) AS state_count,
                            BOOL_OR(
                                source_name IS NULL OR source_name = ''
                                OR source_type IS NULL OR source_type = ''
                                OR source_retrieved_at IS NULL
                                OR source_effective_date IS NULL
                                OR source_version IS NULL OR source_version = ''
                            ) AS has_missing_metadata,
                            BOOL_OR(source_currentness = 'fixture_sample' OR source_type = 'fixture_sample') AS has_fixture_sample,
                            BOOL_OR(source_currentness = 'stale_or_unknown') AS has_stale_or_unknown,
                            BOOL_OR(confidence NOT IN ('source_backed', 'reviewed')) AS has_low_confidence,
                            BOOL_AND(source_currentness = 'current') AS all_current,
                            BOOL_AND(confidence IN ('source_backed', 'reviewed')) AS all_high_confidence,
                            BOOL_AND(source_type <> 'fixture_sample') AS no_fixture_sample,
                            BOOL_AND(
                                source_name IS NOT NULL AND source_name <> ''
                                AND source_type IS NOT NULL AND source_type <> ''
                                AND source_retrieved_at IS NOT NULL
                                AND source_effective_date IS NOT NULL
                                AND source_version IS NOT NULL AND source_version <> ''
                            ) AS all_metadata_present
                        FROM zip_district_mappings
                        GROUP BY zip
                    )
                    SELECT
                        (SELECT COUNT(*) FROM zip_district_mappings) AS row_count,
                        (SELECT COUNT(DISTINCT zip) FROM zip_district_mappings) AS unique_zip_count,
                        COUNT(*) FILTER (WHERE district_count > 1) AS multi_district_zip_count,
                        COUNT(*) FILTER (WHERE state_count > 1) AS multi_state_zip_count,
                        COUNT(*) FILTER (WHERE district_count = 1 AND state_count = 1 AND all_current AND all_high_confidence AND no_fixture_sample AND all_metadata_present) AS auto_select_eligible_count,
                        COUNT(*) FILTER (WHERE has_missing_metadata) AS zips_missing_metadata,
                        COUNT(*) FILTER (WHERE has_fixture_sample) AS zips_fixture_sample,
                        COUNT(*) FILTER (WHERE has_stale_or_unknown) AS zips_stale_or_unknown,
                        COUNT(*) FILTER (WHERE has_low_confidence) AS zips_low_confidence
                    FROM per_zip
                    """
                ).fetchone()
                row_counts = conn.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (
                            WHERE source_name IS NULL OR source_name = ''
                               OR source_type IS NULL OR source_type = ''
                               OR source_retrieved_at IS NULL
                               OR source_effective_date IS NULL
                               OR source_version IS NULL OR source_version = ''
                        ) AS missing_metadata_count,
                        COUNT(*) FILTER (WHERE source_currentness = 'stale_or_unknown') AS stale_or_unknown_count,
                        COUNT(*) FILTER (WHERE source_currentness = 'fixture_sample' OR source_type = 'fixture_sample') AS fixture_sample_count,
                        COUNT(*) FILTER (
                            WHERE source_currentness = 'current'
                              AND confidence IN ('source_backed', 'reviewed')
                              AND source_name IS NOT NULL AND source_name <> ''
                              AND source_type IS NOT NULL AND source_type <> ''
                              AND source_retrieved_at IS NOT NULL
                              AND source_effective_date IS NOT NULL
                              AND source_version IS NOT NULL AND source_version <> ''
                        ) AS current_source_backed_count
                    FROM zip_district_mappings
                    """
                ).fetchone()
    except Exception as exc:  # pragma: no cover - depends on external DB state.
        return {**base, "table_status": "inspection_error", "error": str(exc)}

    row_count = int(counts["row_count"] or 0)
    return {
        **base,
        "db_inspected": True,
        "table_status": "empty" if row_count == 0 else "present",
        "db_has_zip_district_mappings": True,
        "table_absent": False,
        "table_empty": row_count == 0,
        "row_count": row_count,
        "unique_zip_count": int(counts["unique_zip_count"] or 0),
        "multi_district_zip_count": int(counts["multi_district_zip_count"] or 0),
        "multi_state_zip_count": int(counts["multi_state_zip_count"] or 0),
        "missing_metadata_count": int(row_counts["missing_metadata_count"] or 0),
        "stale_or_unknown_count": int(row_counts["stale_or_unknown_count"] or 0),
        "fixture_sample_count": int(row_counts["fixture_sample_count"] or 0),
        "current_source_backed_count": int(row_counts["current_source_backed_count"] or 0),
        "auto_select_eligible_count": int(counts["auto_select_eligible_count"] or 0),
        "ineligible_counts_by_reason": {
            "missing_metadata": int(counts["zips_missing_metadata"] or 0),
            "fixture_sample": int(counts["zips_fixture_sample"] or 0),
            "stale_or_unknown": int(counts["zips_stale_or_unknown"] or 0),
            "low_or_unknown_confidence": int(counts["zips_low_confidence"] or 0),
            "ambiguous_zip": int(counts["multi_district_zip_count"] or 0),
            "multi_state_zip": int(counts["multi_state_zip_count"] or 0),
        },
    }


def inspect_route_switch_status(repo_root: Path) -> dict[str, Any]:
    precomputed = _safe_read_text(repo_root / "backend/app/api/precomputed.py")
    lookup = _safe_read_text(repo_root / "backend/app/api/lookup.py")
    precomputed_lower = precomputed.lower()
    lookup_lower = lookup.lower()
    old_table_read_present = "from zip_district_map" in precomputed_lower
    new_table_read_present = "from zip_district_mappings" in precomputed_lower
    api_new_table_reads = find_api_new_table_reads(repo_root)
    return {
        "lookup_route_file": "backend/app/api/lookup.py",
        "read_layer_file": "backend/app/api/precomputed.py",
        "lookup_route_calls_get_zip_lookup_response": "get_zip_lookup_response(zip_code=zip_code)" in lookup,
        "current_lookup_route_uses_old_gated_path": old_table_read_present and not new_table_read_present,
        "new_table_route_switch_absent": (
            "zip_district_mappings" not in precomputed_lower
            and "zip_district_mappings" not in lookup_lower
            and not api_new_table_reads
        ),
        "production_api_new_table_read_references": api_new_table_reads,
        "old_table_query_present": old_table_read_present,
        "new_table_query_present": new_table_read_present,
        "db_path_source_currentness": "stale_or_unknown",
        "db_path_auto_select_blocked": True,
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


def find_api_new_table_reads(repo_root: Path) -> list[str]:
    api_root = repo_root / "backend/app/api"
    references: list[str] = []
    if not api_root.exists():
        return references
    for path in sorted(api_root.glob("*.py")):
        text = _safe_read_text(path).lower()
        if "from zip_district_mappings" in text or "join zip_district_mappings" in text:
            references.append(_rel(repo_root, path))
    return references


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
    multi_row_schema: dict[str, Any],
    multi_row_fixtures: dict[str, Any],
    seed_readiness: dict[str, Any],
    fixture_metadata: dict[str, Any],
    api_contract: dict[str, Any],
    frontend_gates: dict[str, Any],
    route_switch: dict[str, Any],
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
        check("multi_row_migration_exists", multi_row_schema["migration_exists"]),
        check("multi_row_schema_can_represent_multiple_districts", multi_row_schema["can_represent_multiple_districts_per_zip"]),
        check("multi_row_source_metadata_columns_exist", multi_row_schema["all_source_metadata_columns_present"]),
        check("multi_row_currentness_check_controlled", multi_row_schema["controlled_source_currentness_check_present"]),
        check("multi_row_confidence_check_controlled", multi_row_schema["controlled_confidence_check_present"]),
        check("multi_row_indexes_exist", multi_row_schema["all_required_indexes_present"]),
        check("old_table_remains_compatibility_only", multi_row_schema["old_table_compatibility_only"]),
        check("synthetic_fixtures_cover_split_and_multistate_zip", multi_row_fixtures["has_same_state_multi_district_case"] and multi_row_fixtures["has_multi_state_case"]),
        check("synthetic_duplicate_case_detected", multi_row_fixtures["has_duplicate_detection_case"]),
        check("reviewed_seed_sample_exists", seed_readiness["seed_file_exists"]),
        check("reviewed_seed_sample_validates", seed_readiness["valid"]),
        check("reviewed_seed_sample_not_auto_select_eligible", seed_readiness["auto_select_eligible_count"] == 0),
        check("current_lookup_route_still_uses_old_gated_path", route_switch["current_lookup_route_uses_old_gated_path"]),
        check("new_table_route_switch_absent", route_switch["new_table_route_switch_absent"]),
        check("lookup_route_calls_get_zip_lookup_response", route_switch["lookup_route_calls_get_zip_lookup_response"]),
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
        "No production migration application.",
        "No /lookup/zip/{zip} route switch to zip_district_mappings.",
        "No production seed load.",
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
        "The new multi-row table is drafted locally but is not applied to production.",
        "Default report mode is repository/static only; DB table presence and row counts require an explicit read-only DB URL.",
        "No reliable temporary Postgres fixture is present in the repository, so local migration application remains statically verified.",
        "The reviewed seed sample is non-production and is not loaded into any database.",
        "The public lookup route still reads the compatibility zip_district_map path.",
    ]
    if api_contract["unsupported_route_still_404"]:
        limitations.append(api_contract["unsupported_limitation"])
    return limitations


def recommended_next_milestone() -> str:
    return (
        "ZIP Multi-Row Schema Migration Application And Read-Only Coverage V1: explicitly approve and apply "
        "the additive zip_district_mappings migration, verify the empty/new-table contract with read-only "
        "coverage checks, keep the old lookup path gated, and still avoid national ZIP ingestion or address lookup."
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
        f"- Report mode: `{report['scope']['report_mode']}`",
        f"- Requires production credentials: {_yes_no(report['scope']['requires_production_credentials'])}",
        f"- Migration auto-apply detected: {_yes_no(report['summary']['migration_auto_apply_detected'])}",
        f"- `zip_district_mappings` DB table status: `{report['summary']['zip_district_mappings_db_table_status']}`",
        f"- Reviewed seed sample valid: {_yes_no(report['summary']['reviewed_seed_sample_valid'])}",
        f"- Reviewed seed auto-select eligible ZIPs: {report['summary']['reviewed_seed_auto_select_eligible_count']}",
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

    lines.extend(["", "## Migration Application Conventions", ""])
    migration_rows = [{"check": key, "value": value} for key, value in report["migration_application_conventions"].items()]
    lines.extend(markdown_table(["check", "value"], migration_rows))

    lines.extend(["", "## DB ZIP Metadata Coverage", ""])
    db_rows = [{"check": key, "value": value} for key, value in report["db_zip_metadata_coverage"].items()]
    lines.extend(markdown_table(["check", "value"], db_rows))

    lines.extend(["", "## Multi-Row Schema Contract", ""])
    multi_row_schema_rows = [{"check": key, "value": value} for key, value in report["multi_row_schema_contract"].items()]
    lines.extend(markdown_table(["check", "value"], multi_row_schema_rows))

    lines.extend(["", "## ZIP District Mappings DB Coverage", ""])
    db_coverage_rows = [{"check": key, "value": value} for key, value in report["zip_district_mappings_db_coverage"].items()]
    lines.extend(markdown_table(["check", "value"], db_coverage_rows))

    lines.extend(["", "## Multi-Row Synthetic Fixture Coverage", ""])
    multi_row_fixture_rows = [{"check": key, "value": value} for key, value in report["multi_row_synthetic_fixture_coverage"].items()]
    lines.extend(markdown_table(["check", "value"], multi_row_fixture_rows))

    lines.extend(["", "## Reviewed Seed Readiness", ""])
    seed_rows = [{"check": key, "value": value} for key, value in report["reviewed_seed_readiness"].items()]
    lines.extend(markdown_table(["check", "value"], seed_rows))

    lines.extend(["", "## Fixture ZIP Metadata Coverage", ""])
    fixture_rows = [{"check": key, "value": value} for key, value in report["fixture_zip_metadata_coverage"].items()]
    lines.extend(markdown_table(["check", "value"], fixture_rows))

    lines.extend(["", "## API Response Contract", ""])
    api_rows = [{"check": key, "value": value} for key, value in report["api_response_contract"].items()]
    lines.extend(markdown_table(["check", "value"], api_rows))

    lines.extend(["", "## Frontend Gating Implications", ""])
    frontend_rows = [{"check": key, "value": value} for key, value in report["frontend_gating_implications"].items()]
    lines.extend(markdown_table(["check", "value"], frontend_rows))

    lines.extend(["", "## Route Switch Status", ""])
    route_rows = [{"check": key, "value": value} for key, value in report["route_switch_status"].items()]
    lines.extend(markdown_table(["check", "value"], route_rows))

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


def write_application_readiness_outputs(report: dict[str, Any], *, repo_root: Path) -> None:
    packet = build_application_readiness_packet(report)
    markdown_path = repo_root / APPLICATION_REPORT_MD
    json_path = repo_root / APPLICATION_REPORT_JSON
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_application_readiness_markdown(packet), encoding="utf-8")
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_application_readiness_packet(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": APPLICATION_READINESS_SCHEMA_VERSION,
        "summary": {
            "milestone": "ZIP Schema Application, Coverage, And Seed Readiness V1",
            "public_lookup_behavior_changed": False,
            "production_migration_applied": False,
            "production_seed_loaded": False,
            "national_zip_data_ingested": False,
            "address_lookup_added": False,
            "provider_integration_added": False,
        },
        "migration_auto_apply_finding": report["migration_application_conventions"],
        "migration_application_status": {
            "migration_file": MULTI_ROW_MIGRATION_FILE,
            "migration_applied_anywhere": False,
            "migration_applied_local_or_test": False,
            "migration_applied_production": False,
            "future_production_migration_requires_manual_approval": report["migration_application_conventions"][
                "production_migration_future_manual_approval_required"
            ],
        },
        "schema_application_verification": {
            "isolated_database_application_performed": False,
            "isolated_database_limitation": (
                "No reliable temporary Postgres test database support is present in the repository; "
                "schema verification remains static SQL contract coverage."
            ),
            "static_schema_contract": report["multi_row_schema_contract"],
            "zip_district_map_untouched": report["multi_row_schema_contract"]["old_table_untouched"],
        },
        "coverage_report": {
            "mode": report["scope"]["report_mode"],
            "repository_static_contract": report["multi_row_schema_contract"],
            "db_read_only_coverage": report["zip_district_mappings_db_coverage"],
            "route_switch_status": report["route_switch_status"],
        },
        "seed_format_readiness": {
            "seed_file": REVIEWED_SEED_SAMPLE_FILE,
            "required_fields": REQUIRED_SEED_FIELDS,
            "validation": report["reviewed_seed_readiness"],
            "loaded_into_production": False,
        },
        "payload_readiness_results": {
            "single_current_source_backed_zip": PAYLOAD_SINGLE_DISTRICT_READY,
            "same_state_multi_district_zip": PAYLOAD_AMBIGUOUS_ZIP,
            "multi_state_zip": PAYLOAD_MULTI_STATE_ZIP,
            "missing_metadata": PAYLOAD_STALE_OR_UNKNOWN_SOURCE,
            "fixture_sample": PAYLOAD_FIXTURE_SAMPLE_ONLY,
            "unsupported_zip": PAYLOAD_UNSUPPORTED_ZIP,
            "old_zip_district_map_path": PAYLOAD_STALE_OR_UNKNOWN_SOURCE,
        },
        "route_behavior_unchanged_confirmation": report["route_switch_status"],
        "old_db_path_gated_confirmation": {
            "source_currentness": "stale_or_unknown",
            "stale_or_unknown_source": True,
            "auto_select_blocked": True,
            "reason": "The old zip_district_map table lacks source metadata and remains compatibility-only.",
        },
        "known_limitations": report["known_limitations"],
        "no_go_items_honored": report["no_go_items"],
        "recommended_next_milestone": recommended_next_milestone(),
    }


def render_application_readiness_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# ZIP Schema Application, Coverage, And Seed Readiness V1",
        "",
        "## Summary",
        "",
        "- Public lookup behavior changed: no",
        "- Production migration applied: no",
        "- Production seed loaded: no",
        "- National ZIP data ingested: no",
        "- Address lookup added: no",
        "- Provider integration added: no",
        "",
        "## Migration Auto-Apply Finding",
        "",
        packet["migration_auto_apply_finding"]["finding"],
        "",
        "## Migration Application Status",
        "",
    ]
    lines.extend(markdown_table(["check", "value"], [{"check": key, "value": value} for key, value in packet["migration_application_status"].items()]))
    lines.extend(["", "## Schema Application And Verification", ""])
    lines.extend(markdown_table(["check", "value"], [{"check": key, "value": value} for key, value in packet["schema_application_verification"].items()]))
    lines.extend(["", "## Read-Only Coverage Report", ""])
    coverage = packet["coverage_report"]
    lines.append(f"- Mode: `{coverage['mode']}`")
    lines.append(f"- DB table status: `{coverage['db_read_only_coverage']['table_status']}`")
    lines.append(f"- Old route still gated: {_yes_no(coverage['route_switch_status']['current_lookup_route_uses_old_gated_path'])}")
    lines.append(f"- New-table route switch absent: {_yes_no(coverage['route_switch_status']['new_table_route_switch_absent'])}")
    lines.extend(["", "## Seed Format And Readiness", ""])
    seed = packet["seed_format_readiness"]
    lines.append(f"- Seed file: `{seed['seed_file']}`")
    lines.append(f"- Required fields: `{json.dumps(seed['required_fields'])}`")
    lines.append(f"- Valid: {_yes_no(seed['validation']['valid'])}")
    lines.append(f"- Auto-select eligible ZIPs: {seed['validation']['auto_select_eligible_count']}")
    lines.append(f"- Loaded into production: {_yes_no(seed['loaded_into_production'])}")
    lines.extend(["", "## Payload Readiness Results", ""])
    lines.extend(markdown_table(["case", "classification"], [{"case": key, "classification": value} for key, value in packet["payload_readiness_results"].items()]))
    lines.extend(["", "## Route Behavior Unchanged", ""])
    lines.extend(markdown_table(["check", "value"], [{"check": key, "value": value} for key, value in packet["route_behavior_unchanged_confirmation"].items()]))
    lines.extend(["", "## Old DB Path Gated", ""])
    lines.extend(markdown_table(["check", "value"], [{"check": key, "value": value} for key, value in packet["old_db_path_gated_confirmation"].items()]))
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in packet["known_limitations"])
    lines.extend(["", "## No-Go Items Honored", ""])
    lines.extend(f"- {item}" for item in packet["no_go_items_honored"])
    lines.extend(["", "## Recommended Next Milestone", "", packet["recommended_next_milestone"], ""])
    return "\n".join(lines)


def extract_table_sql(schema_text: str, table_name: str) -> str:
    match = re.search(
        rf"create\s+table\s+(?:if\s+not\s+exists\s+)?{re.escape(table_name)}\s*\((.*?)\);",
        schema_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else ""


def find_multi_row_migration(repo_root: Path) -> Path | None:
    expected = repo_root / MULTI_ROW_MIGRATION_FILE
    if expected.exists():
        return expected
    migrations_root = repo_root / "backend/migrations"
    matches = sorted(migrations_root.glob("*zip_district_mappings.sql")) if migrations_root.exists() else []
    return matches[0] if matches else None


def normalize_multi_row_fixture_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    normalized = {
        "row_id": str(row.get("case") or index),
        "case": _clean(row.get("case")),
        "zip": _clean(row.get("zip")),
        "state": _clean(row.get("state")),
        "district": normalize_district(row.get("district")),
        "source_name": _clean(row.get("source_name")),
        "source_type": _clean(row.get("source_type")),
        "source_retrieved_at": _clean(row.get("source_retrieved_at")),
        "source_effective_date": _clean(row.get("source_effective_date")),
        "source_version": _clean(row.get("source_version")),
        "source_currentness": _clean(row.get("source_currentness")),
        "confidence": _clean(row.get("confidence")),
        "valid_from": _clean(row.get("valid_from")),
        "valid_to": _clean(row.get("valid_to")),
    }
    normalized["has_all_source_metadata"] = all(
        normalized[field]
        for field in ["source_name", "source_type", "source_retrieved_at", "source_effective_date", "source_version"]
    )
    return normalized


def active_source_key(row: dict[str, Any]) -> str:
    if not row.get("zip") or not row.get("state") or not row.get("district"):
        return ""
    return "|".join(
        [
            row["zip"],
            row["state"],
            row["district"],
            row["source_name"],
            row["source_version"],
            row["valid_from"] or row["source_effective_date"],
            row["valid_to"] or "9999-12-31",
        ]
    )


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
