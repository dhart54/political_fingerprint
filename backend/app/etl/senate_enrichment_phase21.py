import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db import get_connection
from app.etl.amendment_evidence import WritePrecondition, require_write_precondition
from app.etl.manual_interpretations import validate_manual_interpretations


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "docs" / "review_packets" / "senate_enrichment_classification_manifest_phase_21.json"
CLASSIFICATION_ROLLBACK_PATH = (
    REPO_ROOT / "docs" / "review_packets" / "senate_enrichment_classification_rollback_phase_21.sql"
)
INTERPRETATION_ROLLBACK_PATH = (
    REPO_ROOT / "docs" / "review_packets" / "senate_enrichment_interpretation_rollback_phase_21.sql"
)
SUBSTANTIVE_BATCH_PATH = (
    REPO_ROOT / "docs" / "interpretation_batches" / "batch_017_senate_substantive_enrichment_candidates.json"
)
PROCEDURAL_BATCH_PATH = (
    REPO_ROOT / "docs" / "interpretation_batches" / "batch_018_senate_procedural_context_candidates.json"
)
BATCH_015_PATH = (
    REPO_ROOT / "docs" / "interpretation_batches" / "batch_015_senate_sjres55_procedural_context_candidates.json"
)

CLASSIFICATION_VERSION = "v1"
SCHEMA_VERSION = "senate_enrichment_phase_21_v1"
CLASSIFICATION_APPROVAL_PHRASE = (
    "Approve bounded Phase 21 production write of deterministic Senate vote classifications for 119th Congress / 2025 "
    "priority evidence families, capped at 100 classification rows, with no support/opposition inference, no alignment "
    "changes, no PN nominations, no treaty/executive votes, and rollback generated before write."
)
SUBSTANTIVE_APPROVAL_PHRASE = (
    "Approve production import of the Phase 21 batch_017 Senate substantive interpretation package, capped at 50 fully "
    "validated rows, with exact roll_call_ids documented, authoritative source grounding, type-aware amendment and "
    "final-passage handling, procedural rows excluded, rollback generated before write, and immediate post-import "
    "validation of support/opposition, readiness, alignment, and not-voting treatment."
)
PROCEDURAL_APPROVAL_PHRASE = (
    "Approve production import of the Phase 21 batch_018 Senate procedural-context package, capped at 25 rows, with "
    "support_position and oppose_position null, no support/opposition or alignment counting changes, rollback generated "
    "before write, and immediate post-import validation."
)

PRIORITY_FAMILIES = {
    ("hr", 1): "H.R. 1 reconciliation package",
    ("sconres", 7): "S.Con.Res. 7 budget-resolution amendments",
    ("hconres", 14): "H.Con.Res. 14 budget-resolution amendments",
    ("hr", 5371): "H.R. 5371 appropriations package",
    ("sjres", 55): "S.J.Res. 55 procedural CRA floor sequence",
}

GENERIC_PURPOSE_MARKERS = (
    "in the nature of a substitute",
    "to improve the bill",
    "no statement of purpose",
)

DOMAIN_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("HEALTH_SOCIAL", "medicaid_and_medicare", ("medicaid", "medicare", "health care", "health coverage", "nursing home")),
    ("HEALTH_SOCIAL", "prescription_drugs_and_medicare_benefits", ("prescription drug", "drug costs", "drug prices")),
    ("HEALTH_SOCIAL", "reproductive_and_family_health", ("fertility", "in vitro fertilization", "maternal", "pediatric")),
    ("HEALTH_SOCIAL", "nutrition_and_food_assistance", ("school lunch", "school breakfast", "food assistance", "nutrition")),
    ("HEALTH_SOCIAL", "veterans_health_and_benefits", ("veterans affairs", "veteran dental", "pact act")),
    ("ECONOMY_TAXES", "tax_policy", ("tax", "taxes", "internal revenue code", "premium tax credits", "tax relief")),
    ("ECONOMY_TAXES", "budget_and_debt", ("debt", "deficit", "budget", "reconciliation", "appropriations")),
    ("ECONOMY_TAXES", "consumer_costs", ("rent", "housing", "groceries", "everyday goods", "cost of housing")),
    ("EDUCATION_WORKFORCE", "education_scholarships_and_school_meals", ("school", "education", "scholarships", "teacher")),
    ("EDUCATION_WORKFORCE", "federal_workforce_and_labor", ("federal employees", "collective bargaining", "right to organize", "minimum wage", "caregivers")),
    ("ENVIRONMENT_ENERGY", "energy_costs_and_clean_energy", ("energy", "electricity", "wind", "solar", "clean energy")),
    ("ENVIRONMENT_ENERGY", "public_lands_and_disaster_response", ("public land", "forest service", "wildland", "fema", "disaster")),
    ("NATIONAL_SECURITY_FOREIGN", "ukraine_and_foreign_security", ("ukraine", "russia", "foreign countries", "military operations")),
    ("NATIONAL_SECURITY_FOREIGN", "defense_spending", ("defense", "pentagon", "armed forces")),
    ("IMMIGRATION_BORDER", "immigration_status_and_benefits", ("alien", "aliens", "immigration", "citizenship")),
    ("JUSTICE_PUBLIC_SAFETY", "law_enforcement_and_public_safety", ("police", "law enforcement", "crime", "criminal")),
    ("INFRASTRUCTURE_TECH_TRANSPORT", "aviation_and_transportation", ("aviation", "airports", "transportation")),
    ("INFRASTRUCTURE_TECH_TRANSPORT", "technology_and_ai", ("artificial intelligence", "technology", "broadband")),
)


@dataclass(frozen=True)
class DryRun:
    planned_inserts: int
    planned_updates: int
    skipped_existing: int
    deferred: int
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "planned_inserts": self.planned_inserts,
            "planned_updates": self.planned_updates,
            "skipped_existing": self.skipped_existing,
            "deferred": self.deferred,
            "planned_vote_interpretation_writes": 0,
            "errors": self.errors,
            "safe_to_write": not self.errors,
        }


def build_manifest() -> dict[str, Any]:
    rows = _fetch_priority_rows()
    considered = [_manifest_row(row) for row in rows]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classification_version": CLASSIFICATION_VERSION,
        "scope": {
            "congress": 119,
            "calendar_year": 2025,
            "chamber": "senate",
            "priority_families": list(PRIORITY_FAMILIES.values()),
            "excluded": ["PN nominations", "treaty/executive votes", "prior Congresses"],
        },
        "summary": _summary(considered),
        "considered_roll_calls": considered,
    }


def write_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    manifest = build_manifest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(path), "summary": manifest["summary"]}


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    rows = manifest.get("considered_roll_calls")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("Unexpected manifest schema_version.")
    if not isinstance(rows, list) or not rows:
        errors.append("Manifest must contain considered_roll_calls.")
        rows = []
    seen: set[int] = set()
    for index, row in enumerate(rows):
        label = f"considered_roll_calls[{index}]"
        roll_call_id = row.get("roll_call_id")
        if not isinstance(roll_call_id, int):
            errors.append(f"{label}: roll_call_id must be an integer.")
            continue
        if roll_call_id in seen:
            errors.append(f"{label}: duplicate roll_call_id {roll_call_id}.")
        seen.add(roll_call_id)
        if row.get("eligible_for_write") is True:
            classification = row.get("proposed_classification") or {}
            if classification.get("support_oppose_positions_inferred") is not False:
                errors.append(f"{label}: classification inferred support/oppose.")
            if row.get("evidence_type") == "senate_amendment_fact":
                purpose = str(row.get("amendment_purpose") or "")
                if _purpose_is_generic(purpose):
                    errors.append(f"{label}: amendment purpose is too generic.")
                basis = " ".join(classification.get("classification_basis") or []).lower()
                if "amendment purpose" not in basis:
                    errors.append(f"{label}: amendment classification must use amendment purpose first.")
            if classification.get("primary_domain") is None:
                errors.append(f"{label}: eligible row missing primary_domain.")
    return {"valid": not errors, "errors": errors, "considered_count": len(rows)}


def dry_run(path: Path = MANIFEST_PATH) -> DryRun:
    manifest = _load_json(path)
    validation = validate_manifest(manifest)
    rows = manifest.get("considered_roll_calls") if isinstance(manifest.get("considered_roll_calls"), list) else []
    write_rows = [row for row in rows if row.get("eligible_for_write") is True]
    if len(write_rows) > 100:
        validation["errors"].append("Classification package exceeds 100-row cap.")
    interpretation_ids = _target_interpretation_ids([int(row["roll_call_id"]) for row in write_rows])
    if interpretation_ids:
        validation["errors"].append("Classification targets unexpectedly have vote_interpretations: " + ", ".join(map(str, sorted(interpretation_ids))))
    return DryRun(
        planned_inserts=sum(1 for row in write_rows if row.get("operation") == "insert"),
        planned_updates=sum(1 for row in write_rows if row.get("operation") == "update"),
        skipped_existing=sum(1 for row in rows if row.get("operation") == "skip_existing"),
        deferred=sum(1 for row in rows if row.get("operation") == "defer"),
        errors=list(validation["errors"]),
    )


def write_classification_rollback(path: Path = MANIFEST_PATH, output: Path = CLASSIFICATION_ROLLBACK_PATH) -> dict[str, Any]:
    manifest = _load_json(path)
    insert_ids = [
        int(row["roll_call_id"])
        for row in manifest["considered_roll_calls"]
        if row.get("eligible_for_write") is True and row.get("operation") == "insert"
    ]
    update_rows = [
        row
        for row in manifest["considered_roll_calls"]
        if row.get("eligible_for_write") is True and row.get("operation") == "update"
    ]
    lines = [
        "-- Rollback for Phase 21 deterministic Senate vote classifications.",
        "-- Scope: exact Phase 21 classification manifest target rows only.",
        "BEGIN;",
        "",
        "DO $$",
        "BEGIN",
        "  IF EXISTS (",
        "    SELECT 1 FROM vote_interpretations",
        f"    WHERE roll_call_id = ANY(ARRAY[{', '.join(map(str, insert_ids + [int(row['roll_call_id']) for row in update_rows])) or 'NULL'}]::bigint[])",
        "  ) THEN",
        "    RAISE EXCEPTION 'Phase 21 classification rollback stopped: target roll calls have interpretations.';",
        "  END IF;",
        "END $$;",
        "",
    ]
    if insert_ids:
        lines.extend(
            [
                "DELETE FROM vote_classifications",
                f"WHERE roll_call_id = ANY(ARRAY[{', '.join(map(str, insert_ids))}]::bigint[])",
                f"  AND classification_version = '{CLASSIFICATION_VERSION}';",
                "",
            ]
        )
    for row in update_rows:
        existing = row["existing_classification"]
        primary = "NULL" if existing.get("primary_domain") is None else f"'{existing['primary_domain']}'"
        score = json.dumps(existing.get("score_breakdown") or {}, sort_keys=True).replace("'", "''")
        lines.extend(
            [
                "UPDATE vote_classifications",
                f"SET is_eligible = {'TRUE' if existing['is_eligible'] else 'FALSE'},",
                f"    eligibility_reason = '{str(existing['eligibility_reason']).replace(chr(39), chr(39) + chr(39))}',",
                f"    primary_domain = {primary},",
                f"    score_breakdown = '{score}'::jsonb,",
                f"    classification_version = '{str(existing['classification_version']).replace(chr(39), chr(39) + chr(39))}',",
                "    updated_at = NOW()",
                f"WHERE roll_call_id = {int(row['roll_call_id'])};",
                "",
            ]
        )
    lines.append("COMMIT;")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(output), "insert_ids": insert_ids, "update_ids": [int(row["roll_call_id"]) for row in update_rows]}


def write_classifications(path: Path = MANIFEST_PATH, approval_phrase: str = "") -> dict[str, Any]:
    if approval_phrase != CLASSIFICATION_APPROVAL_PHRASE:
        raise ValueError("Phase 21 classification approval phrase is missing or incorrect.")
    result = dry_run(path)
    if result.errors:
        raise ValueError(f"Classification dry-run failed: {result.errors}")
    manifest = _load_json(path)
    rows = [row for row in manifest["considered_roll_calls"] if row.get("eligible_for_write") is True]
    require_write_precondition(
        WritePrecondition(
            scope="Phase 21 deterministic Senate evidence classifications",
            approval_phrase=CLASSIFICATION_APPROVAL_PHRASE,
            provided_approval_phrase=approval_phrase,
            target_row_ids=tuple(int(row["roll_call_id"]) for row in rows),
            rollback_path=CLASSIFICATION_ROLLBACK_PATH,
            preflight_errors=tuple(result.errors),
            planned_vote_interpretation_writes=0,
            expected_vote_interpretation_writes=0,
        )
    )
    inserted: list[int] = []
    updated: list[int] = []
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for row in rows:
                classification = row["proposed_classification"]
                params = {
                    "roll_call_id": row["roll_call_id"],
                    "is_eligible": True,
                    "eligibility_reason": "policy_vote",
                    "primary_domain": classification["primary_domain"],
                    "score_breakdown": json.dumps(classification["score_breakdown"], sort_keys=True),
                    "classification_version": CLASSIFICATION_VERSION,
                }
                if row["operation"] == "insert":
                    cursor.execute(
                        """
                        INSERT INTO vote_classifications (
                            roll_call_id, is_eligible, eligibility_reason, primary_domain,
                            score_breakdown, classification_version
                        )
                        VALUES (
                            %(roll_call_id)s, %(is_eligible)s, %(eligibility_reason)s,
                            %(primary_domain)s, %(score_breakdown)s::jsonb, %(classification_version)s
                        )
                        RETURNING roll_call_id
                        """,
                        params,
                    )
                    if cursor.fetchone():
                        inserted.append(int(row["roll_call_id"]))
                elif row["operation"] == "update":
                    cursor.execute(
                        """
                        UPDATE vote_classifications
                        SET is_eligible = %(is_eligible)s,
                            eligibility_reason = %(eligibility_reason)s,
                            primary_domain = %(primary_domain)s,
                            score_breakdown = %(score_breakdown)s::jsonb,
                            classification_version = %(classification_version)s,
                            updated_at = NOW()
                        WHERE roll_call_id = %(roll_call_id)s
                        RETURNING roll_call_id
                        """,
                        params,
                    )
                    if cursor.fetchone():
                        updated.append(int(row["roll_call_id"]))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"inserted": inserted, "updated": updated, "dry_run": result.to_dict()}


def build_batches(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    substantive = _build_substantive_candidates(manifest)
    procedural = _build_procedural_candidates()
    SUBSTANTIVE_BATCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUBSTANTIVE_BATCH_PATH.write_text(json.dumps(substantive, indent=2, sort_keys=True), encoding="utf-8")
    PROCEDURAL_BATCH_PATH.write_text(json.dumps(procedural, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "substantive_path": str(SUBSTANTIVE_BATCH_PATH),
        "substantive_count": len(substantive["interpretations"]),
        "procedural_path": str(PROCEDURAL_BATCH_PATH),
        "procedural_count": len(procedural["interpretations"]),
    }


def validate_batch(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    records = payload.get("interpretations", [])
    errors: list[str] = []
    manual = validate_manual_interpretations(records)
    errors.extend(manual.errors)
    seen: set[int] = set()
    for index, record in enumerate(records):
        label = f"interpretations[{index}]"
        roll_call_id = int(record.get("roll_call_id") or 0)
        if roll_call_id in seen:
            errors.append(f"{label}: duplicate roll_call_id {roll_call_id}")
        seen.add(roll_call_id)
        candidate_type = record.get("candidate_type")
        vote_type = record.get("vote_type")
        text = " ".join(str(record.get(field) or "") for field in ("plain_english_summary", "what_happened", "why_it_mattered", "what_not_to_infer")).lower()
        if candidate_type == "substantive_interpretation":
            if vote_type in {"motion", "cloture", "procedural"}:
                errors.append(f"{label}: procedural vote type in substantive batch")
            if record.get("support_position") != "yea" or record.get("oppose_position") != "nay":
                errors.append(f"{label}: substantive support/oppose must be yea/nay")
            if vote_type == "amendment" and "final passage" in text:
                errors.append(f"{label}: amendment blurred into final passage")
        elif candidate_type == "procedural_context":
            if record.get("support_position") is not None or record.get("oppose_position") is not None:
                errors.append(f"{label}: procedural context must have null support/oppose")
        else:
            errors.append(f"{label}: unsupported candidate_type {candidate_type}")
    return {"valid": not errors, "errors": errors, "candidate_count": len(records)}


def interpretation_preflight(substantive_path: Path = SUBSTANTIVE_BATCH_PATH, procedural_path: Path = PROCEDURAL_BATCH_PATH) -> dict[str, Any]:
    return {
        "substantive": _preflight_batch(substantive_path),
        "procedural": _preflight_batch(procedural_path),
    }


def idempotency_check(substantive_path: Path = SUBSTANTIVE_BATCH_PATH, procedural_path: Path = PROCEDURAL_BATCH_PATH) -> dict[str, Any]:
    return {
        "substantive": _idempotency_batch(substantive_path),
        "procedural": _idempotency_batch(procedural_path),
    }


def write_interpretation_rollback(paths: list[Path] | None = None, output: Path = INTERPRETATION_ROLLBACK_PATH) -> dict[str, Any]:
    paths = paths or [SUBSTANTIVE_BATCH_PATH, PROCEDURAL_BATCH_PATH]
    target_ids: list[int] = []
    prior_rows = _existing_interpretation_rows([int(row["roll_call_id"]) for path in paths for row in _load_json(path)["interpretations"]])
    for path in paths:
        target_ids.extend(int(row["roll_call_id"]) for row in _load_json(path)["interpretations"])
    insert_ids = [roll_call_id for roll_call_id in target_ids if roll_call_id not in prior_rows]
    update_ids = [roll_call_id for roll_call_id in target_ids if roll_call_id in prior_rows]
    lines = [
        "-- Rollback for Phase 21 Senate interpretation imports.",
        "-- Scope: exact batch_017 and batch_018 target roll_call_ids only.",
        "BEGIN;",
        "",
    ]
    if insert_ids:
        lines.extend(
            [
                "DELETE FROM vote_interpretations",
                f"WHERE roll_call_id = ANY(ARRAY[{', '.join(map(str, insert_ids))}]::bigint[]);",
                "",
            ]
        )
    for roll_call_id in update_ids:
        row = prior_rows[roll_call_id]
        lines.extend(_restore_interpretation_sql(roll_call_id, row))
    lines.append("COMMIT;")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(output), "insert_ids": insert_ids, "update_ids": update_ids}


def import_batch(path: Path, approval_phrase: str) -> dict[str, Any]:
    payload = _load_json(path)
    records = payload["interpretations"]
    validation = validate_batch(path)
    if not validation["valid"]:
        raise ValueError(f"Batch validation failed: {validation['errors']}")
    expected_phrase = SUBSTANTIVE_APPROVAL_PHRASE if "batch_017" in path.name else PROCEDURAL_APPROVAL_PHRASE
    if approval_phrase != expected_phrase:
        raise ValueError("Approval phrase is missing or incorrect.")
    if len(records) > (50 if "batch_017" in path.name else 25):
        raise ValueError("Batch exceeds cap.")
    require_write_precondition(
        WritePrecondition(
            scope=f"Phase 21 interpretation import for {path.name}",
            approval_phrase=expected_phrase,
            provided_approval_phrase=approval_phrase,
            target_row_ids=tuple(int(row["roll_call_id"]) for row in records),
            rollback_path=INTERPRETATION_ROLLBACK_PATH,
            preflight_errors=tuple(validation["errors"]),
            planned_vote_interpretation_writes=len(records),
            expected_vote_interpretation_writes=len(records),
        )
    )
    prior = _existing_interpretation_rows([int(row["roll_call_id"]) for row in records])
    from app.etl.manual_interpretations import import_manual_interpretations

    result = import_manual_interpretations(input_path=path, reviewed_by="phase_21_approved")
    return {
        "result": result,
        "inserts": len([row for row in records if int(row["roll_call_id"]) not in prior]),
        "updates": len([row for row in records if int(row["roll_call_id"]) in prior]),
    }


def post_validate() -> dict[str, Any]:
    target_ids = [
        int(row["roll_call_id"])
        for path in (SUBSTANTIVE_BATCH_PATH, PROCEDURAL_BATCH_PATH)
        if path.exists()
        for row in _load_json(path)["interpretations"]
    ]
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vote_interpretations WHERE roll_call_id = ANY(%s)", (target_ids,))
            target_interpretations = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM vote_interpretations WHERE support_position IS NOT NULL")
            support_non_null = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM vote_interpretations WHERE oppose_position IS NOT NULL")
            oppose_non_null = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM vote_classifications")
            classifications = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM bills")
            bills = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM roll_calls")
            roll_calls = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM votes_cast")
            votes_cast = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM vote_contexts")
            vote_contexts = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM senate_amendment_references")
            amendments = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT vcf.primary_domain::text,
                       COUNT(*) FILTER (WHERE vi.interpretation_status = 'interpreted') AS interpreted,
                       COUNT(*) FILTER (WHERE vi.support_position IS NULL AND vi.oppose_position IS NULL) AS non_counting
                FROM vote_interpretations vi
                JOIN vote_classifications vcf ON vcf.roll_call_id = vi.roll_call_id
                WHERE vi.roll_call_id = ANY(%s)
                GROUP BY vcf.primary_domain::text
                ORDER BY vcf.primary_domain::text
                """,
                (target_ids,),
            )
            by_domain = [dict(zip(["domain", "interpreted", "non_counting"], row)) for row in cursor.fetchall()]
    finally:
        connection.close()
    return {
        "target_interpretations": target_interpretations,
        "support_position_non_null": support_non_null,
        "oppose_position_non_null": oppose_non_null,
        "vote_classifications": classifications,
        "bills": bills,
        "roll_calls": roll_calls,
        "votes_cast": votes_cast,
        "vote_contexts": vote_contexts,
        "senate_amendment_references": amendments,
        "target_by_domain": by_domain,
    }


def _fetch_priority_rows() -> list[dict[str, Any]]:
    query = """
        WITH vcx AS (
            SELECT DISTINCT ON (roll_call_id) roll_call_id, vote_type, final_result
            FROM vote_contexts
            ORDER BY roll_call_id
        )
        SELECT
            rc.id AS roll_call_id,
            rc.rollcall_number,
            rc.vote_date::date::text AS vote_date,
            rc.question,
            rc.description,
            rc.source_url,
            vcx.vote_type,
            vcx.final_result,
            b.bill_type,
            b.bill_number,
            b.title AS bill_title,
            b.summary AS bill_summary,
            b.subjects AS bill_subjects,
            sar.amendment_number,
            sar.amendment_type,
            sar.amendment_to_amendment_number,
            sar.parent_bill_display,
            sar.amendment_purpose,
            sar.source_url AS amendment_source_url,
            vcf.is_eligible AS existing_is_eligible,
            vcf.eligibility_reason AS existing_eligibility_reason,
            vcf.primary_domain::text AS existing_primary_domain,
            vcf.score_breakdown AS existing_score_breakdown,
            vcf.classification_version AS existing_classification_version,
            vi.interpretation_status AS existing_interpretation_status
        FROM roll_calls rc
        LEFT JOIN vcx ON vcx.roll_call_id = rc.id
        LEFT JOIN bills b ON b.id = rc.bill_id
        LEFT JOIN senate_amendment_references sar ON sar.roll_call_id = rc.id
        LEFT JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE rc.chamber = 'senate'
          AND rc.congress = 119
          AND rc.vote_date >= '2025-01-01'
          AND rc.vote_date < '2026-01-01'
          AND (b.bill_type, b.bill_number) IN (('hr',1),('sconres',7),('hconres',14),('hr',5371),('sjres',55))
        ORDER BY b.bill_type, b.bill_number, rc.rollcall_number
    """
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [column.name for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


def _manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    evidence_type = "senate_amendment_fact" if row.get("amendment_number") else "roll_call_vote"
    classification, defer_reason = _classify(row, evidence_type=evidence_type)
    existing = _existing_classification(row)
    eligible = classification is not None and existing is None
    return {
        "roll_call_id": int(row["roll_call_id"]),
        "senate_roll_number": int(row["rollcall_number"]),
        "date": row["vote_date"],
        "evidence_type": evidence_type,
        "source_family": PRIORITY_FAMILIES.get((row.get("bill_type"), row.get("bill_number")), "Other"),
        "vote_type": row.get("vote_type"),
        "bill_identity": _bill_identity(row),
        "amendment_number": row.get("amendment_number"),
        "amendment_to_amendment_number": row.get("amendment_to_amendment_number"),
        "amendment_purpose": row.get("amendment_purpose"),
        "question": row.get("question"),
        "description": row.get("description"),
        "source_url": row.get("amendment_source_url") or row.get("source_url"),
        "proposed_classification": classification,
        "existing_classification": existing,
        "eligible_for_write": eligible,
        "operation": "insert" if eligible else "skip_existing" if existing is not None else "defer",
        "defer_or_reject_reason": None if eligible else "Existing classification left unchanged." if existing else defer_reason,
        "support_oppose_positions_inferred": False,
    }


def _classify(row: dict[str, Any], *, evidence_type: str) -> tuple[dict[str, Any] | None, str | None]:
    text = " ".join(
        str(value or "")
        for value in (
            row.get("amendment_purpose") if evidence_type == "senate_amendment_fact" else "",
            row.get("description"),
            row.get("question"),
            row.get("bill_title"),
            row.get("bill_summary"),
            " ".join(row.get("bill_subjects") or []),
        )
    )
    if evidence_type == "senate_amendment_fact":
        purpose = str(row.get("amendment_purpose") or "")
        if _purpose_is_generic(purpose):
            return None, "amendment_purpose_missing_or_generic"
        if row.get("vote_type") != "amendment":
            return None, "amendment_related_procedural_motion_deferred"
    elif row.get("vote_type") not in {"final_passage", "concurrence"}:
        return None, "bill_centered_row_not_substantive_or_final"

    lowered = text.lower()
    for domain, facet, signals in DOMAIN_RULES:
        if any(signal in lowered for signal in signals):
            return (
                {
                    "is_eligible": True,
                    "eligibility_reason": "policy_vote",
                    "primary_domain": domain,
                    "proposed_facet": facet,
                    "score_breakdown": {domain: {"phase21_keyword_match": 4}},
                    "classification_basis": [
                        "Amendment purpose and identity are primary." if evidence_type == "senate_amendment_fact" else "Bill identity and roll-call question are primary.",
                        "Parent measure context is supporting only.",
                    ],
                    "classification_version": CLASSIFICATION_VERSION,
                    "confidence": "contextual",
                    "support_oppose_positions_inferred": False,
                    "vote_interpretation_included": False,
                },
                None,
            )
    return None, "deterministic_issue_signals_below_threshold"


def _purpose_is_generic(purpose: str) -> bool:
    lowered = purpose.strip().lower()
    return not lowered or any(marker in lowered for marker in GENERIC_PURPOSE_MARKERS)


def _existing_classification(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("existing_classification_version") is None:
        return None
    return {
        "is_eligible": bool(row.get("existing_is_eligible")),
        "eligibility_reason": row.get("existing_eligibility_reason"),
        "primary_domain": row.get("existing_primary_domain"),
        "score_breakdown": row.get("existing_score_breakdown") or {},
        "classification_version": row.get("existing_classification_version"),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [row for row in rows if row["eligible_for_write"]]
    by_domain: dict[str, int] = {}
    by_facet: dict[str, int] = {}
    for row in eligible:
        classification = row["proposed_classification"]
        by_domain[classification["primary_domain"]] = by_domain.get(classification["primary_domain"], 0) + 1
        by_facet[classification["proposed_facet"]] = by_facet.get(classification["proposed_facet"], 0) + 1
    return {
        "considered": len(rows),
        "eligible_for_write": len(eligible),
        "skipped_existing": sum(1 for row in rows if row["operation"] == "skip_existing"),
        "deferred": sum(1 for row in rows if row["operation"] == "defer"),
        "by_domain": dict(sorted(by_domain.items())),
        "by_facet": dict(sorted(by_facet.items())),
        "planned_vote_interpretation_writes": 0,
    }


def _build_substantive_candidates(manifest: dict[str, Any]) -> dict[str, Any]:
    existing_by_id = _existing_interpretation_rows(
        [int(row["roll_call_id"]) for row in manifest["considered_roll_calls"]]
    )
    rows = [
        row
        for row in manifest["considered_roll_calls"]
        if row.get("proposed_classification")
        and (row.get("existing_classification") is None or row["existing_classification"].get("is_eligible") is True)
        and row.get("vote_type") in {"amendment", "final_passage"}
        and _substantive_source_safe(row)
        and (
            int(row["roll_call_id"]) not in existing_by_id
            or existing_by_id[int(row["roll_call_id"])].get("reviewed_by") == "phase_21_approved"
        )
    ]
    # Prefer newly classified amendment rows, then already-classified uninterpreted rows from the same families.
    rows = sorted(rows, key=lambda row: (row["operation"] != "insert", row["senate_roll_number"]))[:50]
    interpretations = [_substantive_candidate(row) for row in rows]
    return {
        "schema_version": "manual_interpretation_v1",
        "batch_id": "batch_017_senate_substantive_enrichment_candidates",
        "batch_type": "supervised_enrichment_review_only",
        "created_at": "2026-06-14",
        "candidate_type_counts": {
            "substantive_interpretation": len(interpretations),
            "procedural_context": 0,
            "still_insufficient": 0,
        },
        "interpretations": interpretations,
    }


def _substantive_candidate(row: dict[str, Any]) -> dict[str, Any]:
    classification = row["proposed_classification"]
    roll = row["senate_roll_number"]
    source_url = row["source_url"]
    if row["vote_type"] == "final_passage":
        summary = f"The Senate voted on final passage of {row['bill_identity']}."
        happened = f"The vote was on final passage of {row['bill_identity']}."
        mattered = "The vote directly concerned whether the bill would pass the Senate."
        not_infer = "Do not infer motive, ideology, character, a voting recommendation, or support for every provision beyond the final-passage vote."
        yea = f"A Yea vote supported final passage of {row['bill_identity']}."
        nay = f"A Nay vote opposed final passage of {row['bill_identity']}."
        effect = f"If passed, {row['bill_identity']} would advance as the measure identified by the official Senate roll call."
        basis = [f"Official Senate Roll {roll} XML", f"Production bill identity for {row['bill_identity']}"]
        confidence = "medium"
    elif row["vote_type"] == "concurrence":
        summary = f"The Senate voted on {row['bill_identity']} as amended."
        happened = f"The vote concerned Senate action on {row['bill_identity']} as amended."
        mattered = "The vote directly concerned Senate action on the amended measure."
        not_infer = "Do not infer motive, ideology, character, a voting recommendation, or support for every provision beyond this roll-call action."
        yea = f"A Yea vote supported the Senate action on {row['bill_identity']} as amended."
        nay = f"A Nay vote opposed the Senate action on {row['bill_identity']} as amended."
        effect = "If agreed to, the action would advance the amended measure."
        basis = [f"Official Senate Roll {roll} XML", f"Production bill identity for {row['bill_identity']}"]
        confidence = "medium"
    else:
        amendment = row["amendment_number"]
        purpose = str(row["amendment_purpose"])
        summary = f"The Senate voted on {amendment}, which the Senate XML describes as: {purpose}"
        happened = f"The vote was on agreeing to {amendment} during consideration of {row['bill_identity']}."
        mattered = "The amendment purpose identifies the practical subject of the vote."
        not_infer = "Do not infer motive, ideology, character, a voting recommendation, or a broad issue position beyond this amendment vote."
        yea = f"A Yea vote supported agreeing to {amendment}."
        nay = f"A Nay vote opposed agreeing to {amendment}."
        effect = f"If agreed to, the amendment would have added or changed language related to: {purpose}"
        basis = [f"Official Senate Roll {roll} XML", f"{amendment} purpose in Senate XML", "Phase 21 senate_amendment_references row"]
        confidence = "high"
    return {
        "roll_call_id": row["roll_call_id"],
        "roll_number": roll,
        "chamber": "senate",
        "issue_domain": classification["primary_domain"],
        "issue_facet": classification["proposed_facet"],
        "source_family": row["source_family"],
        "bill_or_amendment_identity": row["amendment_number"] or row["bill_identity"],
        "amendment_purpose": row.get("amendment_purpose"),
        "candidate_type": "substantive_interpretation",
        "interpretation_status": "interpreted",
        "support_position": "yea",
        "oppose_position": "nay",
        "interpretation_version": "interpretation_v1",
        "classification_version": CLASSIFICATION_VERSION,
        "confidence": confidence,
        "would_count_if_approved": True,
        "vote_type": row["vote_type"],
        "source_url": source_url,
        "source_basis": basis,
        "plain_english_summary": summary,
        "what_happened": happened,
        "why_it_mattered": mattered,
        "member_vote_context": "A Yea vote supported the described action. A Nay vote opposed the described action.",
        "what_not_to_infer": not_infer,
        "yea_meaning": yea,
        "nay_meaning": nay,
        "policy_effect": effect,
        "uncertainty_note": "Source-grounded substantive interpretation from official Senate roll-call and stored bill/amendment facts.",
        "interpretation_reason": "Official Senate source identifies the vote action and target.",
    }


def _build_procedural_candidates() -> dict[str, Any]:
    if BATCH_015_PATH.exists():
        payload = _load_json(BATCH_015_PATH)
        interpretations = payload.get("interpretations", [])
    else:
        interpretations = []
    for row in interpretations:
        row["candidate_type"] = "procedural_context"
        row["support_position"] = None
        row["oppose_position"] = None
        row["would_count_if_approved"] = False
    return {
        "schema_version": "manual_interpretation_v1",
        "batch_id": "batch_018_senate_procedural_context_candidates",
        "batch_type": "supervised_enrichment_review_only",
        "created_at": "2026-06-14",
        "candidate_type_counts": {
            "substantive_interpretation": 0,
            "procedural_context": len(interpretations),
            "still_insufficient": 0,
        },
        "interpretations": interpretations[:25],
    }


def _substantive_source_safe(row: dict[str, Any]) -> bool:
    text = f"{row.get('amendment_purpose') or ''} {row.get('question') or ''} {row.get('description') or ''}".lower()
    procedural_markers = (
        "major rules without congressional approval",
        "article 1 law-making powers",
        "administrative state",
    )
    return not any(marker in text for marker in procedural_markers)


def _preflight_batch(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    records = payload["interpretations"]
    ids = [int(row["roll_call_id"]) for row in records]
    existing = _existing_interpretation_rows(ids)
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT vc.roll_call_id,
                       COUNT(*) FILTER (WHERE lower(vc.position::text) = 'yea') AS yea_rows,
                       COUNT(*) FILTER (WHERE lower(vc.position::text) = 'nay') AS nay_rows,
                       COUNT(*) FILTER (WHERE lower(vc.position::text) = 'not_voting') AS not_voting_rows
                FROM votes_cast vc
                WHERE vc.roll_call_id = ANY(%s)
                GROUP BY vc.roll_call_id
                """,
                (ids,),
            )
            vote_counts = {int(row[0]): {"yea": int(row[1]), "nay": int(row[2]), "not_voting": int(row[3])} for row in cursor.fetchall()}
    finally:
        connection.close()
    support_rows = 0
    oppose_rows = 0
    for record in records:
        counts = vote_counts[int(record["roll_call_id"])]
        if record.get("support_position") == "yea":
            support_rows += counts["yea"]
        if record.get("oppose_position") == "nay":
            oppose_rows += counts["nay"]
    return {
        "roll_call_ids": ids,
        "inserts": len([roll_call_id for roll_call_id in ids if roll_call_id not in existing]),
        "updates": len([roll_call_id for roll_call_id in ids if roll_call_id in existing]),
        "support_rows": support_rows,
        "oppose_rows": oppose_rows,
        "not_voting_rows": sum(vote_counts[roll_call_id]["not_voting"] for roll_call_id in ids),
        "planned_classification_writes": 0,
        "planned_fact_table_writes": 0,
    }


def _idempotency_batch(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    records = payload["interpretations"]
    ids = [int(row["roll_call_id"]) for row in records]
    existing = _existing_interpretation_rows(ids)
    fields = (
        "interpretation_status",
        "support_position",
        "oppose_position",
        "plain_english_summary",
        "yea_meaning",
        "nay_meaning",
        "policy_effect",
        "issue_facet",
        "confidence",
        "what_happened",
        "why_it_mattered",
        "member_vote_context",
        "what_not_to_infer",
    )
    mismatches: list[dict[str, Any]] = []
    for record in records:
        roll_call_id = int(record["roll_call_id"])
        row = existing.get(roll_call_id)
        if row is None:
            mismatches.append({"roll_call_id": roll_call_id, "field": "missing_existing_row"})
            continue
        for field in fields:
            if _normalize_value(row.get(field)) != _normalize_value(record.get(field)):
                mismatches.append({"roll_call_id": roll_call_id, "field": field})
    return {
        "target_rows": len(records),
        "existing_rows": len(existing),
        "additional_inserts_needed": len([record for record in records if int(record["roll_call_id"]) not in existing]),
        "content_mismatches": mismatches,
        "content_already_matches": not mismatches,
    }


def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    return str(value)


def _existing_interpretation_rows(ids: list[int]) -> dict[int, dict[str, Any]]:
    if not ids:
        return {}
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM vote_interpretations WHERE roll_call_id = ANY(%s)", (ids,))
            columns = [column.name for column in cursor.description]
            return {int(row[columns.index("roll_call_id")]): dict(zip(columns, row)) for row in cursor.fetchall()}
    finally:
        connection.close()


def _target_interpretation_ids(ids: list[int]) -> set[int]:
    return set(_existing_interpretation_rows(ids))


def _restore_interpretation_sql(roll_call_id: int, row: dict[str, Any]) -> list[str]:
    def value(name: str) -> str:
        item = row.get(name)
        if item is None:
            return "NULL"
        if isinstance(item, (dict, list)):
            return "'" + json.dumps(item, sort_keys=True).replace("'", "''") + "'::jsonb"
        return "'" + str(item).replace("'", "''") + "'"

    fields = [
        "interpretation_status",
        "support_position",
        "oppose_position",
        "interpretation_reason",
        "source_url",
        "interpretation_version",
        "classification_version",
        "plain_english_summary",
        "yea_meaning",
        "nay_meaning",
        "policy_effect",
        "issue_facet",
        "confidence",
        "source_basis",
        "uncertainty_note",
        "what_happened",
        "why_it_mattered",
        "member_vote_context",
        "what_not_to_infer",
        "reviewed_by",
        "reviewed_at",
    ]
    lines = ["UPDATE vote_interpretations", "SET " + ",\n    ".join(f"{field} = {value(field)}" for field in fields), f"WHERE roll_call_id = {roll_call_id};", ""]
    return lines


def _bill_identity(row: dict[str, Any]) -> str:
    bill_type = str(row.get("bill_type") or "").upper().replace("HCONRES", "H.Con.Res.").replace("SCONRES", "S.Con.Res.").replace("SJRES", "S.J.Res.").replace("HJRES", "H.J.Res.")
    if bill_type == "HR":
        bill_type = "H.R."
    elif bill_type == "S":
        bill_type = "S."
    elif bill_type == "SCONRES":
        bill_type = "S.Con.Res."
    return f"{bill_type} {row.get('bill_number')}"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 21 Senate enrichment workflow.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-manifest")
    sub.add_parser("validate-manifest")
    sub.add_parser("dry-run")
    sub.add_parser("write-classification-rollback")
    write_classifications_parser = sub.add_parser("write-classifications")
    write_classifications_parser.add_argument("--approval-phrase", required=True)
    sub.add_parser("build-batches")
    validate_batch_parser = sub.add_parser("validate-batch")
    validate_batch_parser.add_argument("--input", type=Path, required=True)
    sub.add_parser("preflight-interpretations")
    sub.add_parser("idempotency-check")
    sub.add_parser("write-interpretation-rollback")
    import_parser = sub.add_parser("import-batch")
    import_parser.add_argument("--input", type=Path, required=True)
    import_parser.add_argument("--approval-phrase", required=True)
    sub.add_parser("post-validate")
    args = parser.parse_args()

    if args.command == "build-manifest":
        result = write_manifest()
    elif args.command == "validate-manifest":
        result = validate_manifest(_load_json(MANIFEST_PATH))
    elif args.command == "dry-run":
        result = dry_run().to_dict()
    elif args.command == "write-classification-rollback":
        result = write_classification_rollback()
    elif args.command == "write-classifications":
        result = write_classifications(approval_phrase=args.approval_phrase)
    elif args.command == "build-batches":
        result = build_batches()
    elif args.command == "validate-batch":
        result = validate_batch(args.input)
    elif args.command == "preflight-interpretations":
        result = interpretation_preflight()
    elif args.command == "idempotency-check":
        result = idempotency_check()
    elif args.command == "write-interpretation-rollback":
        result = write_interpretation_rollback()
    elif args.command == "import-batch":
        result = import_batch(args.input, args.approval_phrase)
    else:
        result = post_validate()
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
