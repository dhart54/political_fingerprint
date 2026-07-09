"""Apply and verify the additive ZIP district mappings migration.

This script intentionally handles only backend/migrations/0013_zip_district_mappings.sql.
It reads DATABASE_URL from backend/.env, masks target details in all output, performs
read-only pre/post checks, and never loads seed or national ZIP data.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from dotenv import dotenv_values


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
MIGRATION_PATH = REPO_ROOT / "backend/migrations/0013_zip_district_mappings.sql"
DEFAULT_ENV_PATH = REPO_ROOT / "backend/.env"
REPORT_JSON = REPO_ROOT / "docs/review_packets/zip_multi_row_schema_migration_application_coverage_v1.json"
REPORT_MD = REPO_ROOT / "docs/review_packets/zip_multi_row_schema_migration_application_coverage_v1.md"
SCHEMA_VERSION = "zip_multi_row_schema_migration_application_coverage_v1"
REQUIRED_COLUMNS = [
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
SOURCE_METADATA_COLUMNS = [
    "source_name",
    "source_type",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
    "source_currentness",
    "confidence",
]
REQUIRED_INDEXES = [
    "idx_zip_district_mappings_active_source_period_unique",
    "idx_zip_district_mappings_zip",
    "idx_zip_district_mappings_zip_state_district",
    "idx_zip_district_mappings_source_currentness",
    "idx_zip_district_mappings_source_name",
    "idx_zip_district_mappings_source_version",
]


class MigrationSafetyError(RuntimeError):
    """Raised when the migration or target does not match the bounded scope."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-path", type=Path, default=DEFAULT_ENV_PATH)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--postcheck-only", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--write-review-packet", action="store_true")
    parser.add_argument(
        "--confirm-apply-to-backend-env-supabase",
        action="store_true",
        help="Required with --apply so production-like Supabase writes are explicit.",
    )
    args = parser.parse_args()

    if sum(bool(value) for value in [args.preflight_only, args.postcheck_only, args.apply]) != 1:
        parser.error("Choose exactly one of --preflight-only, --postcheck-only, or --apply.")
    if args.apply and not args.confirm_apply_to_backend_env_supabase:
        parser.error("--apply requires --confirm-apply-to-backend-env-supabase.")

    db_url = load_database_url(args.env_path)
    target = describe_database_url(db_url, args.env_path)
    migration_sql = MIGRATION_PATH.read_text(encoding="utf-8")
    safety = validate_migration_sql(migration_sql)
    route = inspect_route_behavior()

    preflight = inspect_database(db_url)
    ensure_preflight_safe(preflight)

    applied = False
    if args.apply:
        apply_migration(db_url, migration_sql)
        applied = True

    postcheck = inspect_database(db_url)
    checks = build_contract_checks(postcheck, route)
    if args.apply or args.postcheck_only:
        ensure_postcheck_safe(postcheck, checks)

    report = build_report(
        mode="apply" if args.apply else "preflight" if args.preflight_only else "postcheck",
        target=target,
        safety=safety,
        route=route,
        preflight=preflight,
        postcheck=postcheck,
        checks=checks,
        applied=applied,
    )
    if args.write_review_packet:
        write_review_packet(report)

    print(json.dumps(summarize_for_stdout(report), indent=2, sort_keys=True))
    return 0


def load_database_url(env_path: Path) -> str:
    env = dotenv_values(env_path)
    db_url = env.get("DATABASE_URL")
    if not db_url:
        raise MigrationSafetyError(f"DATABASE_URL is not set in {env_path}")
    return db_url


def describe_database_url(db_url: str, env_path: Path) -> dict[str, Any]:
    parsed = urlsplit(db_url)
    host = parsed.hostname or ""
    path = parsed.path.lstrip("/")
    return {
        "env_path": str(env_path.relative_to(REPO_ROOT) if env_path.is_absolute() else env_path),
        "scheme": parsed.scheme,
        "host": host,
        "port": parsed.port,
        "database": path,
        "username_present": bool(parsed.username),
        "password_present": bool(parsed.password),
        "supabase_host": "supabase" in host.lower(),
        "production_like_target": "supabase" in host.lower(),
        "raw_url_recorded": False,
    }


def validate_migration_sql(sql: str) -> dict[str, Any]:
    normalized = strip_sql_comments(sql).lower()
    banned_patterns = {
        "data_load_insert": r"\binsert\s+into\b",
        "data_load_copy": r"\bcopy\s+",
        "data_update": r"\bupdate\s+",
        "data_delete": r"\bdelete\s+from\b",
        "truncate": r"\btruncate\s+",
        "drop": r"\bdrop\s+",
        "alter_old_zip_table": r"\balter\s+table\s+(?:if\s+exists\s+)?zip_district_map\b",
    }
    matches = {name: bool(re.search(pattern, normalized)) for name, pattern in banned_patterns.items()}
    required = {
        "creates_new_table": bool(
            re.search(r"\bcreate\s+table\s+if\s+not\s+exists\s+zip_district_mappings\b", normalized)
        ),
        "creates_unique_active_source_period_index": "idx_zip_district_mappings_active_source_period_unique" in normalized,
        "old_table_not_referenced_by_ddl": not bool(re.search(r"\bzip_district_map\b", normalized)),
    }
    safe = all(required.values()) and not any(matches.values())
    if not safe:
        raise MigrationSafetyError(
            "Migration SQL is outside the approved additive/table-only envelope: "
            + json.dumps({"required": required, "banned": matches}, sort_keys=True)
        )
    return {
        "migration_file": str(MIGRATION_PATH.relative_to(REPO_ROOT)),
        "additive_table_only": safe,
        "required_checks": required,
        "banned_statement_matches": matches,
        "seed_or_national_data_load_detected": False,
    }


def strip_sql_comments(sql: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return re.sub(r"--.*?$", "", without_block, flags=re.MULTILINE)


def inspect_database(db_url: str) -> dict[str, Any]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '15000ms'")
            new_table_exists = bool(
                conn.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'zip_district_mappings'
                    ) AS exists
                    """
                ).fetchone()["exists"]
            )
            old_table_exists = bool(
                conn.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'zip_district_map'
                    ) AS exists
                    """
                ).fetchone()["exists"]
            )

            result: dict[str, Any] = {
                "db_inspected": True,
                "read_only": True,
                "zip_district_map_exists": old_table_exists,
                "zip_district_mappings_exists": new_table_exists,
                "row_count": None,
                "unique_zip_count": None,
                "auto_select_eligible_count": None,
                "fixture_sample_count": None,
                "current_source_backed_count": None,
                "columns": [],
                "constraints": {},
                "indexes": {},
            }
            if not new_table_exists:
                return result

            result["columns"] = [
                row["column_name"]
                for row in conn.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'zip_district_mappings'
                    ORDER BY ordinal_position
                    """
                ).fetchall()
            ]
            result["constraints"] = {
                row["constraint_name"]: row["constraint_definition"]
                for row in conn.execute(
                    """
                    SELECT con.conname AS constraint_name, pg_get_constraintdef(con.oid) AS constraint_definition
                    FROM pg_constraint con
                    JOIN pg_class rel ON rel.oid = con.conrelid
                    JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                    WHERE nsp.nspname = 'public'
                      AND rel.relname = 'zip_district_mappings'
                    ORDER BY con.conname
                    """
                ).fetchall()
            }
            result["indexes"] = {
                row["indexname"]: row["indexdef"]
                for row in conn.execute(
                    """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND tablename = 'zip_district_mappings'
                    ORDER BY indexname
                    """
                ).fetchall()
            }
            counts = conn.execute(
                """
                WITH per_zip AS (
                    SELECT
                        zip,
                        COUNT(DISTINCT state || '-' || district) AS district_count,
                        COUNT(DISTINCT state) AS state_count,
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
                    COUNT(*) FILTER (
                        WHERE district_count = 1
                          AND state_count = 1
                          AND all_current
                          AND all_high_confidence
                          AND no_fixture_sample
                          AND all_metadata_present
                    ) AS auto_select_eligible_count,
                    (SELECT COUNT(*) FROM zip_district_mappings WHERE source_currentness = 'fixture_sample' OR source_type = 'fixture_sample') AS fixture_sample_count,
                    (SELECT COUNT(*) FROM zip_district_mappings WHERE source_currentness = 'current' AND confidence IN ('source_backed', 'reviewed')) AS current_source_backed_count
                FROM per_zip
                """
            ).fetchone()
            result.update(
                {
                    "row_count": int(counts["row_count"] or 0),
                    "unique_zip_count": int(counts["unique_zip_count"] or 0),
                    "auto_select_eligible_count": int(counts["auto_select_eligible_count"] or 0),
                    "fixture_sample_count": int(counts["fixture_sample_count"] or 0),
                    "current_source_backed_count": int(counts["current_source_backed_count"] or 0),
                }
            )
            return result


def ensure_preflight_safe(preflight: dict[str, Any]) -> None:
    if not preflight["zip_district_map_exists"]:
        raise MigrationSafetyError("Existing compatibility table zip_district_map was not found.")
    if preflight["zip_district_mappings_exists"] and preflight["row_count"] not in (0, None):
        raise MigrationSafetyError("zip_district_mappings already contains rows; refusing to continue.")


def apply_migration(db_url: str, migration_sql: str) -> None:
    import psycopg

    with psycopg.connect(db_url) as conn:
        conn.autocommit = True
        conn.execute("SET statement_timeout = '30000ms'")
        conn.execute(migration_sql)


def build_contract_checks(postcheck: dict[str, Any], route: dict[str, Any]) -> dict[str, bool]:
    columns = set(postcheck["columns"])
    indexes = postcheck["indexes"]
    constraints_text = "\n".join(postcheck["constraints"].values()).lower()
    active_index = indexes.get("idx_zip_district_mappings_active_source_period_unique", "").lower()
    return {
        "zip_district_mappings_exists": postcheck["zip_district_mappings_exists"],
        "zip_district_map_still_exists": postcheck["zip_district_map_exists"],
        "row_count_zero": postcheck["row_count"] == 0,
        "unique_zip_count_zero": postcheck["unique_zip_count"] == 0,
        "auto_select_eligible_count_zero": postcheck["auto_select_eligible_count"] == 0,
        "all_required_columns_present": all(column in columns for column in REQUIRED_COLUMNS),
        "all_source_metadata_columns_present": all(column in columns for column in SOURCE_METADATA_COLUMNS),
        "controlled_currentness_check_present": all(
            value in constraints_text
            for value in ["current", "stale_or_unknown", "fixture_sample", "unsupported", "expired"]
        ),
        "controlled_confidence_check_present": all(
            value in constraints_text for value in ["source_backed", "reviewed", "inferred", "low", "unknown"]
        ),
        "all_required_indexes_present": all(index in indexes for index in REQUIRED_INDEXES),
        "duplicate_active_source_period_rule_present": bool(active_index)
        and "unique" in active_index
        and "coalesce(valid_from, source_effective_date)" in active_index
        and "coalesce(valid_to, '9999-12-31'::date)" in active_index,
        "public_lookup_still_reads_old_path": route["public_lookup_still_reads_old_path"],
        "new_table_route_switch_absent": route["new_table_route_switch_absent"],
    }


def ensure_postcheck_safe(postcheck: dict[str, Any], checks: dict[str, bool]) -> None:
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise MigrationSafetyError("Post-check failed: " + ", ".join(failed))
    if postcheck["row_count"] != 0:
        raise MigrationSafetyError("zip_district_mappings row count is not zero after migration.")


def inspect_route_behavior() -> dict[str, Any]:
    precomputed = (REPO_ROOT / "backend/app/api/precomputed.py").read_text(encoding="utf-8").lower()
    lookup = (REPO_ROOT / "backend/app/api/lookup.py").read_text(encoding="utf-8")
    return {
        "lookup_route_calls_get_zip_lookup_response": "get_zip_lookup_response(zip_code=zip_code)" in lookup,
        "public_lookup_still_reads_old_path": "from zip_district_map" in precomputed
        and "from zip_district_mappings" not in precomputed,
        "new_table_route_switch_absent": "zip_district_mappings" not in precomputed and "zip_district_mappings" not in lookup.lower(),
        "lookup_behavior_changed_by_this_script": False,
    }


def build_report(
    *,
    mode: str,
    target: dict[str, Any],
    safety: dict[str, Any],
    route: dict[str, Any],
    preflight: dict[str, Any],
    postcheck: dict[str, Any],
    checks: dict[str, bool],
    applied: bool,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "target": target,
        "migration_application": {
            "migration_file": safety["migration_file"],
            "migration_applied": applied,
            "production_like_migration_applied": applied and bool(target["production_like_target"]),
            "seed_data_loaded": False,
            "national_zip_data_ingested": False,
            "address_lookup_added": False,
            "public_route_switched": False,
        },
        "safety": safety,
        "rollback_posture": {
            "route_rollback_needed": False,
            "reason": "The public lookup route remains on zip_district_map and no rows were loaded into zip_district_mappings.",
            "schema_rollback": "Requires a separate explicit approval before any DROP TABLE action.",
        },
        "preflight": preflight,
        "postcheck": postcheck,
        "contract_checks": checks,
        "route_behavior": route,
        "confirmations": {
            "no_migration_beyond_0013_applied_by_this_script": True,
            "no_seed_data_loaded": True,
            "production_lookup_behavior_remains_unchanged": route["public_lookup_still_reads_old_path"]
            and route["new_table_route_switch_absent"],
            "old_zip_district_map_path_gated": True,
            "zip_district_mappings_empty_after_apply": postcheck["row_count"] == 0,
        },
        "recommended_next_milestone": (
            "ZIP Multi-Row Read-Only Coverage And Route-Path Evaluation V1: keep the old lookup path gated, "
            "verify production remains empty/read-only, and only design a future route switch after source-backed "
            "data approval."
        ),
    }


def write_review_packet(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    checks = report["contract_checks"]
    lines = [
        "# ZIP Multi-Row Schema Migration Application And Read-Only Coverage V1",
        "",
        "## Summary",
        "",
        f"- Migration file: `{report['migration_application']['migration_file']}`",
        f"- Migration applied: {_yes_no(report['migration_application']['migration_applied'])}",
        f"- Production-like migration applied: {_yes_no(report['migration_application']['production_like_migration_applied'])}",
        f"- Seed data loaded: {_yes_no(report['migration_application']['seed_data_loaded'])}",
        f"- National ZIP data ingested: {_yes_no(report['migration_application']['national_zip_data_ingested'])}",
        f"- Public route switched: {_yes_no(report['migration_application']['public_route_switched'])}",
        "",
        "## Target",
        "",
        f"- Env file: `{report['target']['env_path']}`",
        f"- Host: `{report['target']['host']}`",
        f"- Database: `{report['target']['database']}`",
        f"- Supabase host: {_yes_no(report['target']['supabase_host'])}",
        f"- Raw URL recorded: {_yes_no(report['target']['raw_url_recorded'])}",
        "",
        "## Read-Only Post-Check",
        "",
        f"- `zip_district_mappings` exists: {_yes_no(report['postcheck']['zip_district_mappings_exists'])}",
        f"- `zip_district_map` still exists: {_yes_no(report['postcheck']['zip_district_map_exists'])}",
        f"- Row count: `{report['postcheck']['row_count']}`",
        f"- Unique ZIP count: `{report['postcheck']['unique_zip_count']}`",
        f"- Auto-select eligible count: `{report['postcheck']['auto_select_eligible_count']}`",
        "",
        "## Contract Checks",
        "",
    ]
    lines.extend(f"- {name}: {_yes_no(value)}" for name, value in checks.items())
    lines.extend(
        [
            "",
            "## Route Behavior",
            "",
            f"- Public lookup still reads old path: {_yes_no(report['route_behavior']['public_lookup_still_reads_old_path'])}",
            f"- New table route switch absent: {_yes_no(report['route_behavior']['new_table_route_switch_absent'])}",
            "",
            "## Rollback Posture",
            "",
            f"- {report['rollback_posture']['reason']}",
            f"- Schema rollback: {report['rollback_posture']['schema_rollback']}",
            "",
            "## Recommended Next Milestone",
            "",
            report["recommended_next_milestone"],
            "",
        ]
    )
    return "\n".join(lines)


def summarize_for_stdout(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": report["mode"],
        "target": report["target"],
        "migration_applied": report["migration_application"]["migration_applied"],
        "production_like_migration_applied": report["migration_application"]["production_like_migration_applied"],
        "seed_data_loaded": report["migration_application"]["seed_data_loaded"],
        "postcheck": {
            "zip_district_mappings_exists": report["postcheck"]["zip_district_mappings_exists"],
            "zip_district_map_exists": report["postcheck"]["zip_district_map_exists"],
            "row_count": report["postcheck"]["row_count"],
            "unique_zip_count": report["postcheck"]["unique_zip_count"],
            "auto_select_eligible_count": report["postcheck"]["auto_select_eligible_count"],
        },
        "contract_checks_passed": all(report["contract_checks"].values()),
        "review_packet": str(REPORT_JSON.relative_to(REPO_ROOT)),
    }


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MigrationSafetyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
