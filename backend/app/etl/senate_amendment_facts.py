import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from app.db import get_connection
from app.etl.fetch_sources import SENATE_XML_CACHE_DIR
from app.etl.senate_xml_adapter import (
    SENATE_XML_SAMPLE_DIR,
    _build_senate_vote_legislator,
    _build_senate_source_url,
    _normalize_senate_vote_date,
    _parse_members,
    _resolve_source_file,
)
from app.etl.vote_context import build_vote_contexts


SUPPORTED_PARENT_BILL_TYPES = {
    "s",
    "sres",
    "sjres",
    "sconres",
    "hr",
    "hres",
    "hjres",
    "hconres",
}
CURRENT_CONGRESS = 119
CURRENT_YEAR_PREFIX = "2025-"
AMENDMENT_REFERENCE_MIGRATION_PATH = Path(__file__).resolve().parents[2] / "migrations" / "0010_senate_amendment_references.sql"


@dataclass(frozen=True)
class SenateAmendmentDryRunResult:
    manifest_path: str
    candidate_rows: int
    safe_future_import_rows: int
    deferred_rows: int
    planned_bill_inserts: int
    planned_roll_call_inserts: int
    planned_votes_cast_inserts: int
    planned_vote_context_inserts: int
    planned_amendment_reference_inserts: int
    planned_vote_interpretation_inserts: int
    planned_vote_interpretation_updates: int
    planned_vote_interpretation_deletes: int
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_path": self.manifest_path,
            "candidate_rows": self.candidate_rows,
            "safe_future_import_rows": self.safe_future_import_rows,
            "deferred_rows": self.deferred_rows,
            "planned_inserts": {
                "bills": self.planned_bill_inserts,
                "roll_calls": self.planned_roll_call_inserts,
                "votes_cast": self.planned_votes_cast_inserts,
                "vote_contexts": self.planned_vote_context_inserts,
                "senate_amendment_references": self.planned_amendment_reference_inserts,
                "vote_interpretations": self.planned_vote_interpretation_inserts,
            },
            "planned_vote_interpretation_inserts": self.planned_vote_interpretation_inserts,
            "planned_vote_interpretation_updates": self.planned_vote_interpretation_updates,
            "planned_vote_interpretation_deletes": self.planned_vote_interpretation_deletes,
            "errors": self.errors,
            "safe_to_request_import_approval": False,
        }


@dataclass(frozen=True)
class SenateAmendmentProductionState:
    existing_roll_numbers: set[int]
    existing_bill_keys: set[tuple[int, str, int]]
    legislator_bioguide_ids: set[str]
    roll_numbers_with_interpretations: set[int]
    roll_numbers_with_amendment_references: set[int]
    amendment_reference_table_exists: bool
    migration_compatibility: dict[str, object]


@dataclass(frozen=True)
class SenateAmendmentImportDryRunResult:
    manifest_path: str
    candidate_roll_numbers: list[int]
    planned_bill_inserts: int
    skipped_existing_bills: int
    planned_roll_call_inserts: int
    skipped_existing_roll_calls: list[int]
    planned_votes_cast_inserts: int
    planned_vote_context_inserts: int
    planned_amendment_reference_inserts: int
    skipped_existing_amendment_references: list[int]
    planned_vote_interpretation_inserts: int
    planned_vote_interpretation_updates: int
    planned_vote_interpretation_deletes: int
    unsupported_roll_numbers: list[int]
    parse_failures: list[dict[str, object]]
    member_mapping_failures: list[dict[str, object]]
    bill_mapping_failures: list[dict[str, object]]
    amendment_reference_failures: list[dict[str, object]]
    migration_compatibility: dict[str, object]
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_path": self.manifest_path,
            "candidate_roll_numbers": self.candidate_roll_numbers,
            "planned_inserts": {
                "bills": self.planned_bill_inserts,
                "roll_calls": self.planned_roll_call_inserts,
                "votes_cast": self.planned_votes_cast_inserts,
                "vote_contexts": self.planned_vote_context_inserts,
                "senate_amendment_references": self.planned_amendment_reference_inserts,
                "vote_interpretations": self.planned_vote_interpretation_inserts,
            },
            "planned_skips": {
                "bills": self.skipped_existing_bills,
                "roll_calls": self.skipped_existing_roll_calls,
                "senate_amendment_references": self.skipped_existing_amendment_references,
            },
            "planned_vote_interpretation_updates": self.planned_vote_interpretation_updates,
            "planned_vote_interpretation_deletes": self.planned_vote_interpretation_deletes,
            "unsupported_roll_numbers": self.unsupported_roll_numbers,
            "parse_failures": self.parse_failures,
            "member_mapping_failures": self.member_mapping_failures,
            "bill_mapping_failures": self.bill_mapping_failures,
            "amendment_reference_failures": self.amendment_reference_failures,
            "migration_compatibility": self.migration_compatibility,
            "support_oppose_positions_inferred": False,
            "alignment_impact_possible": False,
            "safe_to_import_without_separate_approval": False,
            "errors": self.errors,
        }


def build_senate_amendment_fact_manifest(
    *,
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
    existing_production_rolls: set[int] | None = None,
) -> dict[str, object]:
    existing_rolls = existing_production_rolls or set()
    candidates: list[dict[str, object]] = []
    deferred: list[dict[str, object]] = []

    for vote_path in sorted(senate_xml_dir.glob("vote_*.xml")):
        parsed = _parse_amendment_candidate(vote_path)
        if parsed is None:
            continue
        if int(parsed["roll_number"]) in existing_rolls:
            continue

        row = {
            **parsed,
            "planned_senate_amendment_reference": _build_planned_amendment_reference(parsed),
            "proposed_storage_representation": {
                "recommended_model": "new_amendment_reference_table",
                "parent_bill_storage": "roll_calls.bill_id may point to parent bill only when amendment identity is also stored separately",
                "amendment_identity_storage": "new senate_amendment_references row keyed by roll_call_id",
                "vote_context_storage": "member-level vote_contexts remain deterministic context only",
            },
            "why_fact_only": (
                "The row preserves the official amendment vote facts and member positions only; "
                "it does not assign support_position, oppose_position, alignment, or substantive meaning."
            ),
            "interpretations_included": False,
            "support_oppose_positions_inferred": False,
            "counts_as_interpretation": False,
            "schema_model_available": True,
            "production_migration_required_before_import": True,
        }

        if _is_safe_future_candidate(row):
            candidates.append(
                {
                    **row,
                    "candidate_classification": "safe amendment fact candidate after schema/model work",
                    "why_included": (
                        "Official Senate XML contains a resolvable amendment number, parent document, "
                        "amendment purpose, vote question/title, source URL, and member vote rows."
                    ),
                }
            )
        else:
            deferred.append(
                {
                    **row,
                    "candidate_classification": "amendment candidate needing source packet enrichment",
                    "reason_deferred": "Amendment row lacks a usable purpose/title boundary for safe fact-only display.",
                }
            )

    return {
        "phase": "Phase 17",
        "scope": "119th Congress / 2025 Senate amendment reference implementation validation",
        "import_policy": "local dry-run only; do not import",
        "recommended_model": "new_amendment_reference_table",
        "schema_migration_required_before_import": True,
        "ui_api_changes_required_before_import": True,
        "included_candidate_roll_calls": candidates,
        "excluded_or_deferred_roll_calls": deferred,
        "summary": {
            "safe_future_import_rows": len(candidates),
            "deferred_rows": len(deferred),
            "planned_bill_inserts": len(
                {
                    (
                        row["congress"],
                        row["parent_bill"]["bill_type"],
                        row["parent_bill"]["bill_number"],
                    )
                    for row in candidates
                }
            ),
            "planned_roll_call_inserts": len(candidates),
            "planned_votes_cast_inserts": sum(int(row["expected_member_vote_rows"]) for row in candidates),
            "planned_vote_context_inserts": sum(int(row["expected_member_vote_rows"]) for row in candidates),
            "planned_amendment_reference_inserts": len(candidates),
            "planned_vote_interpretation_inserts": 0,
            "planned_vote_interpretation_updates": 0,
            "planned_vote_interpretation_deletes": 0,
            "support_oppose_positions_inferred": False,
            "alignment_impact_possible": False,
        },
    }


def build_phase_18_amendment_import_manifest(
    *,
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
    existing_production_rolls: set[int] | None = None,
) -> dict[str, object]:
    base_manifest = build_senate_amendment_fact_manifest(
        senate_xml_dir=senate_xml_dir,
        existing_production_rolls=existing_production_rolls,
    )
    candidates = list(base_manifest["included_candidate_roll_calls"])
    deferred = list(base_manifest["excluded_or_deferred_roll_calls"])
    return {
        **base_manifest,
        "phase": "Phase 18",
        "scope": "119th Congress / 2025 Senate amendment fact import preflight",
        "import_policy": "preflight only; do not apply production migration; do not import",
        "approval_required_before_any_write": True,
        "included_candidate_roll_calls": candidates,
        "excluded_or_deferred_roll_calls": deferred,
        "summary": {
            **dict(base_manifest["summary"]),
            "manifest_roll_count": len(candidates),
            "excluded_or_deferred_rows": len(deferred),
            "counts_as_interpretation": False,
        },
    }


def validate_senate_amendment_fact_manifest(manifest: dict[str, object]) -> SenateAmendmentDryRunResult:
    errors: list[str] = []
    candidates = manifest.get("included_candidate_roll_calls")
    deferred = manifest.get("excluded_or_deferred_roll_calls")
    if not isinstance(candidates, list):
        errors.append("Manifest must include included_candidate_roll_calls.")
        candidates = []
    if not isinstance(deferred, list):
        errors.append("Manifest must include excluded_or_deferred_roll_calls.")
        deferred = []

    for row in candidates:
        roll_number = int(row.get("roll_number") or 0)
        if row.get("congress") != CURRENT_CONGRESS:
            errors.append(f"Roll {roll_number} is outside Congress {CURRENT_CONGRESS}.")
        if not str(row.get("date") or "").startswith(CURRENT_YEAR_PREFIX):
            errors.append(f"Roll {roll_number} is outside calendar year 2025.")
        if row.get("chamber") != "senate":
            errors.append(f"Roll {roll_number} is not a Senate row.")
        if not row.get("amendment_number"):
            errors.append(f"Roll {roll_number} is missing amendment_number.")
        parent = row.get("parent_bill") or {}
        if not isinstance(parent, dict) or not parent.get("bill_type") or not parent.get("bill_number"):
            errors.append(f"Roll {roll_number} is missing parent bill context.")
        if not int(row.get("expected_member_vote_rows") or 0):
            errors.append(f"Roll {roll_number} has no member vote rows.")
        planned_reference = row.get("planned_senate_amendment_reference")
        if not isinstance(planned_reference, dict):
            errors.append(f"Roll {roll_number} is missing planned senate_amendment_references row.")
        elif planned_reference.get("fact_status") != "fact_only_uninterpreted":
            errors.append(f"Roll {roll_number} amendment reference must remain fact_only_uninterpreted.")
        if row.get("interpretations_included") is not False:
            errors.append(f"Roll {roll_number} must not include interpretations.")
        if row.get("support_oppose_positions_inferred") is not False:
            errors.append(f"Roll {roll_number} must not infer support/oppose positions.")
        if row.get("counts_as_interpretation") is not False:
            errors.append(f"Roll {roll_number} must not count as an interpretation.")
        if row.get("schema_model_available") is not True:
            errors.append(f"Roll {roll_number} must use the amendment reference schema model.")
        if row.get("production_migration_required_before_import") is not True:
            errors.append(f"Roll {roll_number} must require production migration before import.")

    summary = manifest.get("summary") or {}
    return SenateAmendmentDryRunResult(
        manifest_path=str(manifest.get("manifest_path") or ""),
        candidate_rows=len(candidates),
        safe_future_import_rows=int(summary.get("safe_future_import_rows") or len(candidates)),
        deferred_rows=len(deferred),
        planned_bill_inserts=int(summary.get("planned_bill_inserts") or 0),
        planned_roll_call_inserts=int(summary.get("planned_roll_call_inserts") or 0),
        planned_votes_cast_inserts=int(summary.get("planned_votes_cast_inserts") or 0),
        planned_vote_context_inserts=int(summary.get("planned_vote_context_inserts") or 0),
        planned_amendment_reference_inserts=int(summary.get("planned_amendment_reference_inserts") or 0),
        planned_vote_interpretation_inserts=int(summary.get("planned_vote_interpretation_inserts") or 0),
        planned_vote_interpretation_updates=int(summary.get("planned_vote_interpretation_updates") or 0),
        planned_vote_interpretation_deletes=int(summary.get("planned_vote_interpretation_deletes") or 0),
        errors=errors,
    )


def run_senate_amendment_import_dry_run(
    *,
    manifest_path: Path,
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
    production_state: SenateAmendmentProductionState | None = None,
    skip_existing: bool = True,
    include_vote_contexts: bool = True,
) -> SenateAmendmentImportDryRunResult:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing Senate amendment manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return run_senate_amendment_import_dry_run_for_manifest(
        manifest=manifest,
        manifest_path=str(manifest_path),
        senate_xml_dir=senate_xml_dir,
        production_state=production_state,
        skip_existing=skip_existing,
        include_vote_contexts=include_vote_contexts,
    )


def run_senate_amendment_import_dry_run_for_manifest(
    *,
    manifest: dict[str, object],
    manifest_path: str = "<memory>",
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
    production_state: SenateAmendmentProductionState | None = None,
    skip_existing: bool = True,
    include_vote_contexts: bool = True,
) -> SenateAmendmentImportDryRunResult:
    manifest_result = validate_senate_amendment_fact_manifest(manifest)
    candidates = manifest.get("included_candidate_roll_calls")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Manifest must include non-empty included_candidate_roll_calls.")

    member_tree = ElementTree.parse(_resolve_source_file(senate_xml_dir, "members.xml", SENATE_XML_SAMPLE_DIR))
    legislators_with_lis = _parse_members(member_tree)
    legislators_by_lis = {
        str(legislator["lis_member_id"]): dict(legislator)
        for legislator in legislators_with_lis
    }

    candidate_roll_numbers: list[int] = []
    skipped_existing_roll_calls: list[int] = []
    skipped_existing_amendment_references: list[int] = []
    unsupported_roll_numbers: list[int] = []
    parse_failures: list[dict[str, object]] = []
    member_mapping_failures: list[dict[str, object]] = []
    bill_mapping_failures: list[dict[str, object]] = []
    amendment_reference_failures: list[dict[str, object]] = []
    errors = list(manifest_result.errors)
    planned_bills: set[tuple[int, str, int]] = set()
    skipped_bill_keys: set[tuple[int, str, int]] = set()
    parsed_roll_calls: list[dict[str, object]] = []
    parsed_votes: list[dict[str, object]] = []
    planned_amendment_references: list[dict[str, object]] = []

    for candidate in candidates:
        roll_number = int(candidate.get("roll_number") or 0)
        candidate_roll_numbers.append(roll_number)
        if candidate.get("category") != "senate_amendment_fact_preflight":
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} has unsupported category {candidate.get('category')!r}.")
            continue
        if candidate.get("interpretations_included") is not False:
            errors.append(f"Roll {roll_number} includes interpretations; dry run fails closed.")
            continue
        if candidate.get("support_oppose_positions_inferred") is not False:
            errors.append(f"Roll {roll_number} infers support/oppose positions; dry run fails closed.")
            continue
        if candidate.get("counts_as_interpretation") is not False:
            errors.append(f"Roll {roll_number} counts as interpretation; dry run fails closed.")
            continue
        if int(candidate.get("congress") or 0) != CURRENT_CONGRESS or not str(candidate.get("date") or "").startswith(CURRENT_YEAR_PREFIX):
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} is outside the 119th Congress / 2025 scope.")
            continue

        if production_state and roll_number in production_state.roll_numbers_with_interpretations:
            errors.append(f"Roll {roll_number} already has vote_interpretations rows; dry run fails closed.")
            continue
        if production_state and roll_number in production_state.existing_roll_numbers:
            if skip_existing:
                skipped_existing_roll_calls.append(roll_number)
                if roll_number in production_state.roll_numbers_with_amendment_references:
                    skipped_existing_amendment_references.append(roll_number)
                continue
            errors.append(f"Roll {roll_number} is already present in production; pass explicit skip-existing behavior.")
            continue

        reference = candidate.get("planned_senate_amendment_reference")
        if not _is_valid_planned_reference(reference):
            amendment_reference_failures.append({"roll_number": roll_number, "error": "Missing or invalid planned amendment reference."})
            errors.append(f"Roll {roll_number} is missing a valid planned senate_amendment_references row.")
            continue

        vote_path = senate_xml_dir / f"vote_{roll_number:03d}.xml"
        if not vote_path.exists():
            parse_failures.append({"roll_number": roll_number, "error": f"Missing XML file: {vote_path}"})
            errors.append(f"Roll {roll_number} XML file is missing.")
            continue

        try:
            roll_call, bill, votes = _parse_amendment_roll_call_for_import(
                ElementTree.parse(vote_path),
                candidate=candidate,
                legislators_by_lis=legislators_by_lis,
            )
        except Exception as error:
            parse_failures.append({"roll_number": roll_number, "error": str(error)})
            errors.append(f"Roll {roll_number} could not be parsed for amendment import: {error}")
            continue

        bill_key = (int(bill["congress"]), str(bill["bill_type"]).lower(), int(bill["bill_number"]))
        if bill_key[0] != CURRENT_CONGRESS or str(bill["bill_type"]).lower() not in SUPPORTED_PARENT_BILL_TYPES:
            bill_mapping_failures.append({"roll_number": roll_number, "bill_key": list(bill_key)})
            errors.append(f"Roll {roll_number} parsed to unsupported parent bill key {bill_key}.")
            continue
        if production_state:
            missing_votes = _find_missing_production_legislators(
                votes=votes,
                legislators_by_lis=legislators_by_lis,
                production_bioguide_ids=production_state.legislator_bioguide_ids,
            )
            if missing_votes:
                member_mapping_failures.append({"roll_number": roll_number, "missing_bioguide_ids": sorted(missing_votes)})
                errors.append(f"Roll {roll_number} has member votes without production legislator mapping.")
                continue

        parsed_roll_calls.append(roll_call)
        parsed_votes.extend(votes)
        planned_amendment_references.append(dict(reference))
        if production_state and bill_key in production_state.existing_bill_keys:
            skipped_bill_keys.add(bill_key)
        else:
            planned_bills.add(bill_key)

    planned_contexts = (
        build_vote_contexts(
            legislators=[
                {key: value for key, value in legislator.items() if key != "lis_member_id"}
                for legislator in legislators_by_lis.values()
            ],
            roll_calls=parsed_roll_calls,
            votes_cast=parsed_votes,
        )
        if include_vote_contexts and parsed_roll_calls
        else []
    )

    return SenateAmendmentImportDryRunResult(
        manifest_path=manifest_path,
        candidate_roll_numbers=candidate_roll_numbers,
        planned_bill_inserts=len(planned_bills),
        skipped_existing_bills=len(skipped_bill_keys),
        planned_roll_call_inserts=len(parsed_roll_calls),
        skipped_existing_roll_calls=skipped_existing_roll_calls,
        planned_votes_cast_inserts=len(parsed_votes),
        planned_vote_context_inserts=len(planned_contexts),
        planned_amendment_reference_inserts=len(planned_amendment_references),
        skipped_existing_amendment_references=skipped_existing_amendment_references,
        planned_vote_interpretation_inserts=0,
        planned_vote_interpretation_updates=0,
        planned_vote_interpretation_deletes=0,
        unsupported_roll_numbers=unsupported_roll_numbers,
        parse_failures=parse_failures,
        member_mapping_failures=member_mapping_failures,
        bill_mapping_failures=bill_mapping_failures,
        amendment_reference_failures=amendment_reference_failures,
        migration_compatibility=production_state.migration_compatibility if production_state else validate_local_amendment_reference_migration(),
        errors=errors,
    )


def write_senate_amendment_fact_manifest(
    *,
    output_path: Path,
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
    existing_production_rolls: set[int] | None = None,
) -> SenateAmendmentDryRunResult:
    manifest = build_senate_amendment_fact_manifest(
        senate_xml_dir=senate_xml_dir,
        existing_production_rolls=existing_production_rolls,
    )
    manifest["manifest_path"] = str(output_path)
    result = validate_senate_amendment_fact_manifest(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return result


def write_phase_18_amendment_import_manifest(
    *,
    output_path: Path,
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
) -> SenateAmendmentDryRunResult:
    manifest = build_phase_18_amendment_import_manifest(senate_xml_dir=senate_xml_dir)
    manifest["manifest_path"] = str(output_path)
    result = validate_senate_amendment_fact_manifest(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return result


def load_senate_amendment_production_state_for_manifest(*, manifest_path: Path) -> SenateAmendmentProductionState:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = manifest.get("included_candidate_roll_calls") or []
    roll_numbers = [int(candidate["roll_number"]) for candidate in candidates]
    bill_keys = [
        (
            int(candidate.get("congress") or CURRENT_CONGRESS),
            str((candidate.get("parent_bill") or {}).get("bill_type") or "").lower(),
            int((candidate.get("parent_bill") or {}).get("bill_number") or 0),
        )
        for candidate in candidates
    ]

    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        migration_compatibility = validate_production_amendment_reference_migration_compatibility(connection)
        table_exists = bool(migration_compatibility.get("target_table_exists"))
        return SenateAmendmentProductionState(
            existing_roll_numbers=_fetch_existing_roll_numbers(connection, roll_numbers),
            existing_bill_keys=_fetch_existing_bill_keys(connection, bill_keys),
            legislator_bioguide_ids=_fetch_legislator_bioguide_ids(connection),
            roll_numbers_with_interpretations=_fetch_roll_numbers_with_interpretations(connection, roll_numbers),
            roll_numbers_with_amendment_references=_fetch_roll_numbers_with_amendment_references(connection, roll_numbers)
            if table_exists
            else set(),
            amendment_reference_table_exists=table_exists,
            migration_compatibility=migration_compatibility,
        )
    finally:
        connection.close()


def validate_local_amendment_reference_migration() -> dict[str, object]:
    migration_sql = AMENDMENT_REFERENCE_MIGRATION_PATH.read_text(encoding="utf-8")
    lowered = migration_sql.lower()
    return {
        "migration_path": str(AMENDMENT_REFERENCE_MIGRATION_PATH),
        "creates_target_table": "create table if not exists senate_amendment_references" in lowered,
        "references_roll_calls": "references roll_calls(id)" in lowered,
        "touches_vote_interpretations": "vote_interpretations" in lowered,
        "has_destructive_drop": "drop table" in lowered or "drop column" in lowered,
        "has_parent_bill_index": "idx_senate_amendment_references_parent_bill" in lowered,
        "has_fact_status_constraint": "fact_only_uninterpreted" in lowered,
    }


def validate_production_amendment_reference_migration_compatibility(connection) -> dict[str, object]:
    local = validate_local_amendment_reference_migration()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = ANY(%s)
            """,
            (["roll_calls", "bills", "votes_cast", "vote_contexts", "vote_interpretations", "senate_amendment_references"],),
        )
        tables = {str(row[0]) for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = ANY(%s)
            """,
            (["roll_calls", "bills", "votes_cast", "vote_contexts", "vote_interpretations", "senate_amendment_references"],),
        )
        columns: dict[str, set[str]] = {}
        for table_name, column_name in cursor.fetchall():
            columns.setdefault(str(table_name), set()).add(str(column_name))

    required_columns = {
        "roll_calls": {"id", "chamber", "congress", "rollcall_number"},
        "bills": {"id", "congress", "bill_type", "bill_number"},
        "votes_cast": {"roll_call_id", "legislator_id", "position"},
        "vote_contexts": {"roll_call_id", "legislator_id"},
        "vote_interpretations": {"roll_call_id"},
    }
    missing_required_columns = {
        table: sorted(required - columns.get(table, set()))
        for table, required in required_columns.items()
        if required - columns.get(table, set())
    }
    target_columns = sorted(columns.get("senate_amendment_references", set()))
    expected_target_columns = {
        "roll_call_id",
        "amendment_number",
        "amendment_type",
        "amendment_to_amendment_number",
        "parent_bill_type",
        "parent_bill_number",
        "parent_bill_display",
        "amendment_purpose",
        "source_url",
        "source_xml_path",
        "fact_status",
        "source_version",
        "created_at",
        "updated_at",
    }
    return {
        **local,
        "target_table_exists": "senate_amendment_references" in tables,
        "target_table_columns": target_columns,
        "target_table_matches_expected_shape": expected_target_columns.issubset(set(target_columns))
        if "senate_amendment_references" in tables
        else None,
        "referenced_tables_present": sorted(table for table in required_columns if table in tables),
        "missing_required_columns": missing_required_columns,
        "can_apply_cleanly_in_principle": (
            local["creates_target_table"]
            and local["references_roll_calls"]
            and not local["touches_vote_interpretations"]
            and not local["has_destructive_drop"]
            and not missing_required_columns
        ),
        "production_migration_applied": "senate_amendment_references" in tables,
    }


def _parse_amendment_candidate(vote_path: Path) -> dict[str, object] | None:
    tree = ElementTree.parse(vote_path)
    root = tree.getroot()
    congress = int(_require_text(root.find("congress")))
    session = int(_require_text(root.find("session")))
    vote_date = _normalize_senate_vote_date(_require_text(root.find("vote_date")))
    if congress != CURRENT_CONGRESS or not vote_date.startswith(CURRENT_YEAR_PREFIX):
        return None

    document_type = _optional_text(root.find("document/document_type")) or ""
    amendment_number = _optional_text(root.find("amendment/amendment_number")) or ""
    if not _is_senate_amendment(document_type=document_type, amendment_number=amendment_number):
        return None

    roll_number = int(_require_text(root.find("vote_number")))
    parent_document = _optional_text(root.find("amendment/amendment_to_document_number")) or ""
    parent_bill = _parse_bill_reference(parent_document) if parent_document else None
    member_rows = root.findall("./members/member")

    return {
        "congress": congress,
        "session": session,
        "year": int(vote_date[:4]),
        "chamber": "senate",
        "roll_number": roll_number,
        "date": vote_date,
        "vote_question": _require_text(root.find("question")),
        "vote_title": _require_text(root.find("vote_title")),
        "amendment_number": amendment_number,
        "amendment_type": "S.Amdt.",
        "amendment_to_amendment_number": _optional_text(root.find("amendment/amendment_to_amendment_number")),
        "parent_bill": parent_bill,
        "parent_bill_title": parent_document or None,
        "amendment_purpose": _optional_text(root.find("amendment/amendment_purpose")),
        "expected_member_vote_rows": len(member_rows),
        "source_xml_path": str(vote_path),
        "source_url": _build_senate_source_url(congress=congress, session=session, roll_number=roll_number),
        "category": "senate_amendment_fact_preflight",
        "no_interpretation_included": True,
    }


def _parse_amendment_roll_call_for_import(
    tree: ElementTree.ElementTree,
    *,
    candidate: dict[str, object],
    legislators_by_lis: dict[str, dict[str, object]],
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    root = tree.getroot()
    congress = int(_require_text(root.find("congress")))
    session = int(_require_text(root.find("session")))
    roll_number = int(_require_text(root.find("vote_number")))
    vote_date = _normalize_senate_vote_date(_require_text(root.find("vote_date")))
    if congress != CURRENT_CONGRESS or not vote_date.startswith(CURRENT_YEAR_PREFIX):
        raise ValueError("Amendment roll is outside the 119th Congress / 2025 scope.")
    if roll_number != int(candidate["roll_number"]):
        raise ValueError("Manifest roll number does not match source XML.")

    parent_bill = candidate.get("parent_bill") or {}
    if not isinstance(parent_bill, dict) or not parent_bill.get("bill_type") or not parent_bill.get("bill_number"):
        raise ValueError("Amendment roll is missing parent bill context.")
    amendment_number = str(candidate.get("amendment_number") or "")
    purpose = str(candidate.get("amendment_purpose") or "").strip()
    if not amendment_number or not purpose or purpose == "No Statement of Purpose on File.":
        raise ValueError("Amendment roll is missing amendment identity or purpose.")

    bill_type = str(parent_bill["bill_type"]).lower()
    bill_number = int(parent_bill["bill_number"])
    bill_id = f"bill_{congress}_{bill_type}_{bill_number}"
    source_url = _build_senate_source_url(congress=congress, session=session, roll_number=roll_number)
    roll_call = {
        "id": f"rc_senate_{roll_number:03d}",
        "chamber": "senate",
        "congress": congress,
        "session": session,
        "rollcall_number": roll_number,
        "vote_date": vote_date,
        "question": _require_text(root.find("question")),
        "description": _require_text(root.find("vote_title")),
        "bill_ref": bill_id,
        "source_url": source_url,
    }
    bill = {
        "id": bill_id,
        "congress": congress,
        "bill_type": bill_type,
        "bill_number": bill_number,
        "title": str(candidate.get("parent_bill_title") or parent_bill.get("display") or roll_call["description"]),
        "summary": "",
        "committee": None,
        "subjects": [],
    }
    votes: list[dict[str, object]] = []
    for member_vote in root.findall("./members/member"):
        lis_member_id = _require_text(member_vote.find("lis_member_id"))
        if lis_member_id not in legislators_by_lis:
            legislators_by_lis[lis_member_id] = _build_senate_vote_legislator(
                lis_member_id=lis_member_id,
                member_vote=member_vote,
            )
        votes.append(
            {
                "roll_call_id": roll_call["id"],
                "legislator_id": legislators_by_lis[lis_member_id]["id"],
                "position": _normalize_vote_position(_require_text(member_vote.find("vote_cast"))),
            }
        )
    return roll_call, bill, votes


def _build_planned_amendment_reference(parsed: dict[str, object]) -> dict[str, object]:
    parent_bill = parsed.get("parent_bill") or {}
    if not isinstance(parent_bill, dict):
        parent_bill = {}
    return {
        "roll_call_lookup": {
            "chamber": "senate",
            "congress": parsed["congress"],
            "roll_number": parsed["roll_number"],
        },
        "amendment_number": parsed["amendment_number"],
        "amendment_type": parsed["amendment_type"],
        "amendment_to_amendment_number": parsed.get("amendment_to_amendment_number"),
        "parent_bill_type": parent_bill.get("bill_type"),
        "parent_bill_number": parent_bill.get("bill_number"),
        "parent_bill_display": parent_bill.get("display"),
        "amendment_purpose": parsed.get("amendment_purpose"),
        "source_url": parsed["source_url"],
        "source_xml_path": parsed["source_xml_path"],
        "fact_status": "fact_only_uninterpreted",
        "source_version": "senate_xml_119_2025_v1",
    }


def _is_valid_planned_reference(reference: object) -> bool:
    if not isinstance(reference, dict):
        return False
    required_keys = {
        "roll_call_lookup",
        "amendment_number",
        "amendment_type",
        "parent_bill_type",
        "parent_bill_number",
        "parent_bill_display",
        "amendment_purpose",
        "source_url",
        "source_xml_path",
        "fact_status",
    }
    if required_keys - set(reference):
        return False
    return reference.get("fact_status") == "fact_only_uninterpreted"


def _parse_bill_reference(value: str) -> dict[str, object] | None:
    normalized = re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()
    patterns = [
        ("S CON RES ", "sconres"),
        ("S J RES ", "sjres"),
        ("S RES ", "sres"),
        ("S ", "s"),
        ("H CON RES ", "hconres"),
        ("H J RES ", "hjres"),
        ("H RES ", "hres"),
        ("H R ", "hr"),
    ]
    for prefix, bill_type in patterns:
        if normalized.startswith(prefix):
            bill_number = int(normalized.removeprefix(prefix).split()[0])
            if bill_type not in SUPPORTED_PARENT_BILL_TYPES:
                return None
            return {
                "bill_type": bill_type,
                "bill_number": bill_number,
                "display": value,
            }
    return None


def _normalize_vote_position(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "yea": "yea",
        "nay": "nay",
        "present": "present",
        "not voting": "not_voting",
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported Senate XML vote position: {value}")
    return mapping[normalized]


def _find_missing_production_legislators(
    *,
    votes: list[dict[str, object]],
    legislators_by_lis: dict[str, dict[str, object]],
    production_bioguide_ids: set[str],
) -> set[str]:
    legislators_by_id = {
        str(legislator["id"]): legislator
        for legislator in legislators_by_lis.values()
    }
    missing: set[str] = set()
    for vote in votes:
        legislator = legislators_by_id.get(str(vote["legislator_id"]))
        if not legislator:
            missing.add(str(vote["legislator_id"]))
            continue
        bioguide_id = str(legislator.get("bioguide_id") or "")
        if bioguide_id not in production_bioguide_ids:
            missing.add(bioguide_id)
    return missing


def _fetch_existing_roll_numbers(connection, roll_numbers: list[int]) -> set[int]:
    if not roll_numbers:
        return set()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rollcall_number
            FROM roll_calls
            WHERE chamber = 'senate'
              AND congress = 119
              AND rollcall_number = ANY(%s)
            """,
            (roll_numbers,),
        )
        return {int(row[0]) for row in cursor.fetchall()}


def _fetch_existing_bill_keys(connection, bill_keys: list[tuple[int, str, int]]) -> set[tuple[int, str, int]]:
    if not bill_keys:
        return set()
    congresses = [key[0] for key in bill_keys]
    bill_types = [key[1] for key in bill_keys]
    bill_numbers = [key[2] for key in bill_keys]
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT congress, bill_type, bill_number
            FROM bills
            WHERE (congress, bill_type, bill_number)
              IN (SELECT * FROM UNNEST(%s::int[], %s::text[], %s::int[]))
            """,
            (congresses, bill_types, bill_numbers),
        )
        return {(int(row[0]), str(row[1]).lower(), int(row[2])) for row in cursor.fetchall()}


def _fetch_legislator_bioguide_ids(connection) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT bioguide_id FROM legislators WHERE chamber = 'senate'")
        return {str(row[0]) for row in cursor.fetchall()}


def _fetch_roll_numbers_with_interpretations(connection, roll_numbers: list[int]) -> set[int]:
    if not roll_numbers:
        return set()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rc.rollcall_number
            FROM roll_calls rc
            JOIN vote_interpretations vi
              ON vi.roll_call_id = rc.id
            WHERE rc.chamber = 'senate'
              AND rc.congress = 119
              AND rc.rollcall_number = ANY(%s)
            """,
            (roll_numbers,),
        )
        return {int(row[0]) for row in cursor.fetchall()}


def _fetch_roll_numbers_with_amendment_references(connection, roll_numbers: list[int]) -> set[int]:
    if not roll_numbers:
        return set()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rc.rollcall_number
            FROM roll_calls rc
            JOIN senate_amendment_references sar
              ON sar.roll_call_id = rc.id
            WHERE rc.chamber = 'senate'
              AND rc.congress = 119
              AND rc.rollcall_number = ANY(%s)
            """,
            (roll_numbers,),
        )
        return {int(row[0]) for row in cursor.fetchall()}


def _is_safe_future_candidate(row: dict[str, object]) -> bool:
    purpose = str(row.get("amendment_purpose") or "").strip()
    return bool(
        row.get("amendment_number")
        and row.get("parent_bill")
        and purpose
        and purpose != "No Statement of Purpose on File."
        and int(row.get("expected_member_vote_rows") or 0) > 0
    )


def _is_senate_amendment(*, document_type: str, amendment_number: str) -> bool:
    return document_type.upper().startswith("S.AMDT") or amendment_number.upper().startswith("S.AMDT")


def _require_text(element: ElementTree.Element | None) -> str:
    if element is None or element.text is None:
        raise ValueError("Expected XML element text in Senate amendment source")
    return element.text.strip()


def _optional_text(element: ElementTree.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Build, validate, or dry-run a local Senate amendment fact manifest.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--senate-xml-dir", type=Path, default=SENATE_XML_CACHE_DIR)
    parser.add_argument("--validate", type=Path)
    parser.add_argument("--phase18", action="store_true")
    parser.add_argument("--dry-run", type=Path)
    parser.add_argument("--production-read-only", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--no-vote-contexts", action="store_true")
    parser.add_argument("--validate-migration", action="store_true")
    args = parser.parse_args()

    if args.validate_migration:
        if args.production_read_only:
            connection = get_connection()
            try:
                connection.execute("SET default_transaction_read_only = on")
                result = validate_production_amendment_reference_migration_compatibility(connection)
            finally:
                connection.close()
        else:
            result = validate_local_amendment_reference_migration()
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    if args.validate:
        manifest = json.loads(args.validate.read_text(encoding="utf-8"))
        result = validate_senate_amendment_fact_manifest(manifest)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        if result.errors:
            raise SystemExit(1)
        return

    if args.dry_run:
        production_state = (
            load_senate_amendment_production_state_for_manifest(manifest_path=args.dry_run)
            if args.production_read_only
            else None
        )
        result = run_senate_amendment_import_dry_run(
            manifest_path=args.dry_run,
            senate_xml_dir=args.senate_xml_dir,
            production_state=production_state,
            skip_existing=args.skip_existing,
            include_vote_contexts=not args.no_vote_contexts,
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        if result.errors:
            raise SystemExit(1)
        return

    if args.output is None:
        raise SystemExit("--output is required unless --validate is used.")

    if args.phase18:
        result = write_phase_18_amendment_import_manifest(
            output_path=args.output,
            senate_xml_dir=args.senate_xml_dir,
        )
    else:
        result = write_senate_amendment_fact_manifest(
            output_path=args.output,
            senate_xml_dir=args.senate_xml_dir,
        )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
