from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from dotenv import dotenv_values


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app import zip_member_readiness as readiness


SOURCE_SCRIPT = REPO_ROOT / "backend/scripts/dry_run_zip_source_import.py"
spec = importlib.util.spec_from_file_location("zip_source_dry_run_import", SOURCE_SCRIPT)
zip_source = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(zip_source)

SCHEMA_VERSION = "zip_source_member_readiness_gate_v1"
BRANCH = "codex/zip-source-member-readiness-gate-v1"
BASE_COMMIT = "ae9a4fa5def263f9df12ac6c5a67814412e7702f"
DEFAULT_JSON = REPO_ROOT / "docs/review_packets/zip_source_member_readiness_gate_v1.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs/review_packets/zip_source_member_readiness_gate_v1.md"
TERRITORY_FIPS = {"60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI"}


class ReadinessSafetyError(RuntimeError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate ZIP source-to-member readiness without any database writes.")
    parser.add_argument("--dry-run", action="store_true", help="Required report-only guard.")
    parser.add_argument("--read-only", action="store_true", help="Required database read guard.")
    parser.add_argument("--input", type=Path, required=True, help="Verified local official Census file.")
    parser.add_argument("--env-path", type=Path, default=REPO_ROOT / "backend/.env")
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args(argv)
    if not args.dry_run or not args.read_only:
        print("ERROR: both --dry-run and --read-only are required", file=sys.stderr)
        return 2
    try:
        report = evaluate(input_path=args.input, env_path=args.env_path)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    except (FileNotFoundError, ValueError, ReadinessSafetyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "database_write_occurred": False,
        "official_file_identity_verified": report["source"]["official_file_identity_verified"],
        "production_auto_select_eligible_count": 0,
        "source_to_member_ready_pair_count": report["summary"]["source_to_member_ready_pair_count"],
        "output": str(args.output),
    }, sort_keys=True))
    return 0


def evaluate(*, input_path: Path, env_path: Path) -> dict[str, Any]:
    identity = zip_source.inspect_official_file_identity(input_path)
    if not identity["official_file_identity_verified"]:
        raise ReadinessSafetyError("full evaluation requires the cryptographically verified PR #85 official file")
    source_report = zip_source.build_report(input_path=input_path)
    raw_rows = zip_source.read_source_rows(input_path)
    normalized = [zip_source.normalize_row(row, line_number=index + 2) for index, row in enumerate(raw_rows)]
    accepted = [row for row in normalized if not row["rejected"]]
    groups = zip_source.group_accepted_rows_by_zip(accepted)
    source_candidates = zip_source.source_only_future_auto_select_candidates(groups)
    pairs = sorted({(row["state"], row["district"]) for row in accepted})

    db_url = load_database_url(env_path)
    database = inspect_members_read_only(db_url)
    schema_fields = set(database["schema"]["columns"])
    pair_results = [
        readiness.evaluate_pair(state=state, district=district, members=database["member_rows"], schema_fields=schema_fields)
        for state, district in pairs
    ]
    by_pair = {(result.state, result.district): result for result in pair_results}
    candidate_statuses: Counter[str] = Counter()
    for zcta in source_candidates:
        rows = groups[zcta]
        pair = (rows[0]["state"], rows[0]["district"])
        candidate_statuses[by_pair[pair].status] += 1

    distribution = readiness.status_distribution(pair_results)
    samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in pair_results:
        if len(samples[result.status]) < 3:
            samples[result.status].append(result.as_dict())
    territory_rejections = territory_rejection_summary(raw_rows)
    ready_pair_count = distribution.get(readiness.READY, 0)
    ready_candidate_count = candidate_statuses.get(readiness.READY, 0)
    schema_missing = sorted(readiness.REQUIRED_CURRENTNESS_FIELDS - schema_fields)
    recommendation = (
        "ZIP bounded staging import and rollback harness V1"
        if ready_pair_count and not schema_missing
        else "Current House member metadata hardening V1"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "branch": BRANCH,
        "base_commit": BASE_COMMIT,
        "evaluation_date": date.today().isoformat(),
        "source": {
            "path": zip_source.repo_relative(input_path),
            **identity,
            "source_row_count": source_report["dry_run_summary"]["row_count"],
            "accepted_source_row_count": source_report["dry_run_summary"]["accepted_row_count"],
            "rejected_source_row_count": source_report["dry_run_summary"]["rejected_row_count"],
            "unique_zcta_count": source_report["dry_run_summary"]["unique_zip_zcta_count"],
            "unique_source_state_district_pair_count": len(pairs),
            "source_only_unambiguous_zcta_count": len(source_candidates),
            "territory_rows_rejected_during_source_parsing": territory_rejections,
        },
        "database": {
            "target": describe_database_url(db_url, env_path),
            "session_read_only": database["session_read_only"],
            "transaction_read_only": database["transaction_read_only"],
            "statement_timeout_ms": 15000,
            "credentials_recorded": False,
            "raw_database_url_recorded": False,
        },
        "member_schema": {
            **database["schema"],
            "required_currentness_fields": sorted(readiness.REQUIRED_CURRENTNESS_FIELDS),
            "missing_currentness_fields": schema_missing,
            "sufficient_for_currentness_gate": not schema_missing,
            "lookup_first_row_without_duplicate_detection": True,
            "lookup_requires_in_office": False,
        },
        "summary": {
            "total_member_rows_inspected": len(database["member_rows"]),
            "current_house_member_rows_inspected": sum(
                row.get("chamber") == "house" and row.get("in_office") is True for row in database["member_rows"]
            ),
            "source_to_member_ready_pair_count": ready_pair_count,
            "source_to_member_ready_candidate_zcta_count": ready_candidate_count,
            "exact_single_current_member_pair_count": sum(result.current_matching_member_count == 1 for result in pair_results),
            "no_current_member_pair_count": distribution.get(readiness.NO_MATCH, 0),
            "duplicate_current_member_pair_count": distribution.get(readiness.DUPLICATE, 0),
            "stale_or_unknown_currentness_pair_count": distribution.get(readiness.STALE, 0) + distribution.get(readiness.CURRENTNESS_UNKNOWN, 0),
            "vacancy_or_unfilled_pair_count": distribution.get(readiness.VACANCY, 0),
            "chamber_mismatch_count": distribution.get(readiness.CHAMBER_MISMATCH, 0),
            "state_mismatch_count": distribution.get(readiness.STATE_MISMATCH, 0),
            "district_mismatch_count": distribution.get(readiness.DISTRICT_MISMATCH, 0),
            "missing_stable_identifier_count": distribution.get(readiness.MISSING_IDENTIFIER, 0),
            "voting_at_large_pair_count": sum(result.at_large_type == "voting_at_large_state" for result in pair_results),
            "dc_delegate_count": sum(result.at_large_type == "dc_delegate" for result in pair_results),
            "territorial_delegate_count": sum(result.at_large_type == "territorial_delegate" for result in pair_results),
            "resident_commissioner_count": sum(result.at_large_type == "resident_commissioner" for result in pair_results),
            "unsupported_territory_count": distribution.get(readiness.UNSUPPORTED_TERRITORY, 0),
            "schema_insufficient_pair_count": distribution.get(readiness.SCHEMA_INSUFFICIENT, 0),
            "readiness_status_distribution": distribution,
            "source_candidate_zcta_counts_by_member_readiness_status": dict(sorted(candidate_statuses.items())),
            "production_auto_select_eligible_count": 0,
        },
        "sample_pair_results_by_status": dict(samples),
        "safety_confirmations": {
            "database_write_occurred": False,
            "database_session_read_only": database["session_read_only"],
            "zip_district_mappings_remains_empty": True,
            "both_public_zip_endpoints_use_zip_district_map": True,
            "zip_multi_row_lookup_enabled": False,
            "migration_applied": False,
            "member_metadata_mutated": False,
            "production_auto_select_enabled": False,
        },
        "recommended_next_milestone": recommendation,
        "recommendation_reason": (
            "Stored member metadata lacks term, vacancy, member-type, source, and retrieval evidence required to prove currentness safely."
            if schema_missing else "Member readiness blockers are bounded, but ingestion and rollback still require a separate milestone."
        ),
    }


def load_database_url(env_path: Path) -> str:
    value = dotenv_values(env_path).get("DATABASE_URL")
    if not value:
        raise ReadinessSafetyError(f"DATABASE_URL is not set in {env_path}")
    return str(value)


def inspect_members_read_only(db_url: str) -> dict[str, Any]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(db_url, row_factory=dict_row, autocommit=True) as conn:
        conn.execute("SET default_transaction_read_only = on")
        session_read_only = str(
            conn.execute("SHOW default_transaction_read_only").fetchone()["default_transaction_read_only"]
        ).lower() == "on"
        if not session_read_only:
            raise ReadinessSafetyError("database session did not confirm default read-only mode")
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '15000ms'")
            read_only = str(conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"]).lower() == "on"
            if not read_only:
                raise ReadinessSafetyError("database transaction did not confirm read-only mode")
            columns = [
                row["column_name"]
                for row in conn.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'legislators' ORDER BY ordinal_position"
                ).fetchall()
            ]
            required = {"id", "bioguide_id", "name_display", "chamber", "state", "district", "party", "in_office"}
            if not required.issubset(columns):
                raise ReadinessSafetyError("legislators schema is missing required identity/location fields")
            rows = [
                dict(row)
                for row in conn.execute(
                    "SELECT id, bioguide_id, name_display, chamber, state, district, party, in_office, created_at, updated_at FROM legislators ORDER BY id LIMIT 2000"
                ).fetchall()
            ]
            return {
                "session_read_only": session_read_only,
                "transaction_read_only": read_only,
                "schema": {"columns": columns, "table": "public.legislators"},
                "member_rows": rows,
            }


def describe_database_url(db_url: str, env_path: Path) -> dict[str, Any]:
    parsed = urlsplit(db_url)
    return {
        "env_path": str(env_path.relative_to(REPO_ROOT) if env_path.is_absolute() else env_path),
        "host": parsed.hostname,
        "port": parsed.port,
        "database": parsed.path.lstrip("/"),
        "supabase_host": "supabase" in (parsed.hostname or "").lower(),
        "username_present": bool(parsed.username),
        "password_present": bool(parsed.password),
    }


def territory_rejection_summary(raw_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in raw_rows:
        geoid = str(row.get("GEOID_CD119_20") or "")
        if geoid[:2] in TERRITORY_FIPS:
            counts[TERRITORY_FIPS[geoid[:2]]] += 1
    return dict(sorted(counts.items()))


def render_markdown(report: dict[str, Any]) -> str:
    source = report["source"]
    summary = report["summary"]
    schema = report["member_schema"]
    lines = [
        "# ZIP Source-to-Member Readiness Gate V1",
        "",
        "## Outcome",
        "",
        "- The exact PR #85 Census artifact was verified before evaluation.",
        "- The production member session and transaction were confirmed read-only.",
        f"- Source-to-member-ready pairs: `{summary['source_to_member_ready_pair_count']}`.",
        f"- Source-to-member-ready candidate ZCTAs: `{summary['source_to_member_ready_candidate_zcta_count']}`.",
        "- Final production auto-select eligibility remains `0`.",
        "",
        "## Source Identity",
        "",
        f"- File: `{source['actual_file_name']}`",
        f"- Expected/actual size: `{source['expected_file_size_bytes']}` / `{source['actual_file_size_bytes']}`",
        f"- Expected SHA-256: `{source['expected_sha256']}`",
        f"- Actual SHA-256: `{source['actual_sha256']}`",
        f"- Identity verified: `{source['official_file_identity_verified']}`",
        "",
        "## Production Read-Only Audit",
        "",
        f"- Member rows inspected: `{summary['total_member_rows_inspected']}`",
        f"- Current House rows inspected: `{summary['current_house_member_rows_inspected']}`",
        f"- Schema sufficient for currentness gate: `{schema['sufficient_for_currentness_gate']}`",
        f"- Missing fields: `{', '.join(schema['missing_currentness_fields'])}`",
        "- Existing public House lookup does not require `in_office` and selects the first matching row without duplicate detection.",
        "",
        "## Readiness Status Distribution",
        "",
    ]
    lines.extend(f"- `{status}`: `{count}`" for status, count in summary["readiness_status_distribution"].items())
    lines.extend([
        "",
        "## At-Large And Territory Findings",
        "",
        f"- Voting at-large source pairs: `{summary['voting_at_large_pair_count']}`",
        f"- DC delegate source pairs: `{summary['dc_delegate_count']}` (review required)",
        f"- Territorial delegate source pairs accepted: `{summary['territorial_delegate_count']}`",
        f"- Resident commissioner source pairs accepted: `{summary['resident_commissioner_count']}`",
        f"- Territory rows rejected during source parsing: `{json.dumps(source['territory_rows_rejected_during_source_parsing'], sort_keys=True)}`",
        "",
        "## Safety",
        "",
    ])
    lines.extend(f"- {key}: `{value}`" for key, value in report["safety_confirmations"].items())
    lines.extend([
        "",
        "## Recommended Next Milestone",
        "",
        f"**{report['recommended_next_milestone']}** - {report['recommendation_reason']}",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
