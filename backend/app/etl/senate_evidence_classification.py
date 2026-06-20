import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.classification.classifier import (
    CLASSIFICATION_THRESHOLD,
    DOMAIN_SIGNALS,
    ISSUE_DOMAINS,
    ClassificationResult,
    classify_vote,
)
from app.classification.eligibility import evaluate_eligibility
from app.db import get_connection
from app.etl.amendment_evidence import WritePrecondition, require_write_precondition


PHASE_20B_APPROVAL_PHRASE = (
    "Approve bounded production write of Phase 20B deterministic Senate vote classifications for 119th Congress / 2025 "
    "bill-centered and amendment facts, with no vote_interpretations writes, no support/opposition changes, no alignment "
    "changes, no PN nominations, no treaty/executive votes, and rollback generated before write."
)

CLASSIFICATION_VERSION = "v1"
LEGACY_PHASE20B_CLASSIFICATION_VERSION = "senate_evidence_classification_phase_20b"
MANIFEST_SCHEMA_VERSION = "senate_evidence_classification_manifest_v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "docs" / "review_packets" / "senate_evidence_classification_manifest_phase_20b.json"
DEFAULT_ROLLBACK_PATH = REPO_ROOT / "docs" / "review_packets" / "senate_evidence_classification_rollback_phase_20b.sql"

GENERIC_OR_UNUSABLE_PURPOSE_MARKERS = (
    "no statement of purpose",
    "no purpose",
    "to make a technical",
)

FACET_SIGNALS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "ECONOMY_TAXES": (
        ("tax_policy", ("tax", "taxes", "irs")),
        ("budget_reconciliation", ("reconciliation", "deficit", "budgetary", "spending", "reserve fund")),
        ("housing_costs", ("housing", "rent")),
        ("consumer_finance", ("bank", "financial", "overdraft", "consumer")),
    ),
    "HEALTH_SOCIAL": (
        ("prescription_drugs", ("prescription drug", "drug prices", "drugs")),
        ("medicaid_and_medicare", ("medicaid", "medicare", "health coverage", "health care", "nursing home")),
        ("nutrition_and_food_assistance", ("food assistance", "school lunch", "school breakfast", "nutrition")),
        ("veterans_health_and_benefits", ("veterans", "department of veterans affairs", "pact act")),
        ("reproductive_and_family_health", ("fertility", "in vitro fertilization", "maternal", "pediatric")),
    ),
    "EDUCATION_WORKFORCE": (
        ("school_meals_and_education_support", ("school", "student", "teacher", "education")),
        ("federal_workforce", ("federal employees", "workforce", "forest service", "national park service")),
    ),
    "ENVIRONMENT_ENERGY": (
        ("energy_costs_and_regulation", ("energy costs", "electricity", "major rules", "regulations", "administrative state")),
        ("public_lands_and_wildfire", ("forest service", "wildland firefighter", "public lands", "wildfire")),
        ("emissions_and_climate", ("emissions", "climate", "clean energy")),
    ),
    "NATIONAL_SECURITY_FOREIGN": (
        ("ukraine_and_foreign_security", ("ukraine", "russia", "foreign", "aggression")),
        ("defense_funding", ("defense", "military", "armed services")),
    ),
    "IMMIGRATION_BORDER": (
        ("immigration_detention_and_enforcement", ("inadmissible alien", "aliens", "immigration", "detention", "border")),
    ),
    "JUSTICE_PUBLIC_SAFETY": (
        ("criminal_detention_and_public_safety", ("criminal offenses", "crime", "law enforcement", "police", "mandatory detention")),
        ("fentanyl_and_drug_enforcement", ("fentanyl", "controlled substance")),
    ),
    "INFRASTRUCTURE_TECH_TRANSPORT": (
        ("transportation_safety_regulation", ("vehicle", "transportation", "highway", "motor vehicles")),
        ("technology_and_cyber", ("technology", "cyber", "broadband")),
    ),
}
NON_AMENDMENT_PROCEDURAL_MARKERS = (
    "motion to discharge",
)


@dataclass(frozen=True)
class SenateClassificationDryRunResult:
    manifest_path: str
    considered_count: int
    existing_classifications: int
    planned_inserts: int
    planned_updates: int
    skipped_existing: int
    deferred_count: int
    eligible_by_domain: dict[str, int]
    eligible_by_fact_type: dict[str, int]
    planned_vote_interpretation_inserts: int
    planned_vote_interpretation_updates: int
    planned_vote_interpretation_deletes: int
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_path": self.manifest_path,
            "considered_count": self.considered_count,
            "existing_classifications": self.existing_classifications,
            "planned_inserts": self.planned_inserts,
            "planned_updates": self.planned_updates,
            "skipped_existing": self.skipped_existing,
            "deferred_count": self.deferred_count,
            "eligible_by_domain": self.eligible_by_domain,
            "eligible_by_fact_type": self.eligible_by_fact_type,
            "planned_vote_interpretation_inserts": self.planned_vote_interpretation_inserts,
            "planned_vote_interpretation_updates": self.planned_vote_interpretation_updates,
            "planned_vote_interpretation_deletes": self.planned_vote_interpretation_deletes,
            "errors": self.errors,
            "safe_to_write_classifications": not self.errors,
        }


@dataclass(frozen=True)
class SenateClassificationWriteResult:
    dry_run: SenateClassificationDryRunResult
    inserted_classifications: int
    updated_classifications: int
    skipped_existing: int
    inserted_roll_call_ids: list[int]
    updated_roll_call_ids: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run.to_dict(),
            "actual_counts": {
                "inserted_classifications": self.inserted_classifications,
                "updated_classifications": self.updated_classifications,
                "skipped_existing": self.skipped_existing,
                "vote_interpretations_inserted": 0,
                "vote_interpretations_updated": 0,
                "vote_interpretations_deleted": 0,
            },
            "inserted_roll_call_ids": self.inserted_roll_call_ids,
            "updated_roll_call_ids": self.updated_roll_call_ids,
        }


def build_senate_evidence_classification_manifest() -> dict[str, Any]:
    rows = _fetch_loaded_senate_fact_rows()
    considered = [_build_manifest_row(row) for row in rows]
    summary = _summarize_manifest_rows(considered)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classification_version": CLASSIFICATION_VERSION,
        "scope": {
            "congress": 119,
            "calendar_year": 2025,
            "chamber": "senate",
            "fact_types": ["bill_centered", "senate_amendment_fact"],
            "excluded": ["PN nominations", "treaty/executive votes", "prior Congresses"],
        },
        "guardrails": [
            "No vote_interpretations are inserted, updated, or deleted.",
            "No support_position or oppose_position values are inferred.",
            "Amendment classifications use amendment purpose/identity first; parent bill context is supporting context only.",
            "Rows with ambiguous or generic source text remain deferred.",
        ],
        "summary": summary,
        "considered_roll_calls": considered,
    }


def write_senate_evidence_classification_manifest(*, output_path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = build_senate_evidence_classification_manifest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "output_path": str(output_path),
        "summary": manifest["summary"],
    }


def validate_senate_evidence_classification_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    rows = manifest.get("considered_roll_calls")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append("Manifest schema_version is not senate_evidence_classification_manifest_v1.")
    if not isinstance(rows, list) or not rows:
        errors.append("Manifest must include non-empty considered_roll_calls.")
        rows = []

    seen_roll_call_ids: set[int] = set()
    for index, row in enumerate(rows):
        label = f"considered_roll_calls[{index}]"
        roll_call_id = row.get("roll_call_id")
        if not isinstance(roll_call_id, int):
            errors.append(f"{label}: roll_call_id must be an integer.")
            continue
        if roll_call_id in seen_roll_call_ids:
            errors.append(f"{label}: duplicate roll_call_id {roll_call_id}.")
        seen_roll_call_ids.add(roll_call_id)

        if row.get("congress") != 119:
            errors.append(f"{label}: congress must be 119.")
        if not str(row.get("date") or "").startswith("2025-"):
            errors.append(f"{label}: date must be in calendar year 2025.")
        if row.get("chamber") != "senate":
            errors.append(f"{label}: chamber must be senate.")

        classification = row.get("proposed_classification") or {}
        if row.get("eligible_for_write") is True:
            if classification.get("is_eligible") is not True:
                errors.append(f"{label}: eligible_for_write rows must have is_eligible true.")
            if classification.get("primary_domain") not in ISSUE_DOMAINS:
                errors.append(f"{label}: eligible row has invalid primary_domain.")
            if not classification.get("classification_basis"):
                errors.append(f"{label}: eligible row is missing classification_basis.")
            if row.get("fact_type") == "senate_amendment_fact":
                amendment = row.get("amendment_reference") or {}
                purpose = str(amendment.get("amendment_purpose") or "")
                if _purpose_is_unusable(purpose):
                    errors.append(f"{label}: amendment eligible row has unusable purpose.")
                basis = " ".join(classification.get("classification_basis") or []).lower()
                if "amendment purpose" not in basis:
                    errors.append(f"{label}: amendment classification must cite amendment purpose first.")
            if classification.get("support_oppose_positions_inferred") is not False:
                errors.append(f"{label}: classification must not infer support/oppose positions.")
            if classification.get("vote_interpretation_included") is not False:
                errors.append(f"{label}: classification must not include vote interpretation.")

    return {
        "valid": not errors,
        "errors": errors,
        "considered_count": len(rows),
    }


def run_senate_evidence_classification_dry_run(*, manifest_path: Path = DEFAULT_MANIFEST_PATH) -> SenateClassificationDryRunResult:
    manifest = _load_manifest(manifest_path)
    validation = validate_senate_evidence_classification_manifest(manifest)
    errors = list(validation["errors"])
    rows = manifest.get("considered_roll_calls") if isinstance(manifest.get("considered_roll_calls"), list) else []

    write_rows = [row for row in rows if row.get("eligible_for_write") is True]
    existing_to_update = [row for row in write_rows if row.get("existing_classification") and row.get("operation") == "update"]
    inserts = [row for row in write_rows if row.get("operation") == "insert"]
    skipped_existing = [row for row in rows if row.get("operation") == "skip_existing"]
    deferred = [row for row in rows if row.get("eligible_for_write") is not True]

    existing_classifications = sum(1 for row in rows if row.get("existing_classification"))
    eligible_by_domain: dict[str, int] = {}
    eligible_by_fact_type: dict[str, int] = {}
    for row in write_rows:
        classification = row.get("proposed_classification") or {}
        domain = str(classification.get("primary_domain"))
        eligible_by_domain[domain] = eligible_by_domain.get(domain, 0) + 1
        fact_type = str(row.get("fact_type"))
        eligible_by_fact_type[fact_type] = eligible_by_fact_type.get(fact_type, 0) + 1

    target_roll_call_ids = [int(row["roll_call_id"]) for row in write_rows]
    existing_interpretations = _fetch_interpretation_roll_call_ids(target_roll_call_ids)
    if existing_interpretations:
        errors.append(
            "Target classification rows unexpectedly have vote_interpretations; refusing classification write: "
            + ", ".join(str(value) for value in sorted(existing_interpretations))
        )

    return SenateClassificationDryRunResult(
        manifest_path=str(manifest_path),
        considered_count=len(rows),
        existing_classifications=existing_classifications,
        planned_inserts=len(inserts),
        planned_updates=len(existing_to_update),
        skipped_existing=len(skipped_existing),
        deferred_count=len(deferred),
        eligible_by_domain=dict(sorted(eligible_by_domain.items())),
        eligible_by_fact_type=dict(sorted(eligible_by_fact_type.items())),
        planned_vote_interpretation_inserts=0,
        planned_vote_interpretation_updates=0,
        planned_vote_interpretation_deletes=0,
        errors=errors,
    )


def write_senate_evidence_classifications(
    *,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    approval_phrase: str,
) -> SenateClassificationWriteResult:
    if approval_phrase != PHASE_20B_APPROVAL_PHRASE:
        raise ValueError("Phase 20B approval gate is missing or does not exactly match.")

    dry_run = run_senate_evidence_classification_dry_run(manifest_path=manifest_path)
    if dry_run.errors:
        raise ValueError(f"Classification dry-run failed; refusing production write: {dry_run.errors}")
    if dry_run.planned_vote_interpretation_inserts or dry_run.planned_vote_interpretation_updates or dry_run.planned_vote_interpretation_deletes:
        raise ValueError("Classification dry-run planned vote_interpretations writes; refusing production write.")

    manifest = _load_manifest(manifest_path)
    rows = [
        row
        for row in manifest["considered_roll_calls"]
        if row.get("eligible_for_write") is True and row.get("operation") in {"insert", "update"}
    ]
    require_write_precondition(
        WritePrecondition(
            scope="Phase 20B deterministic Senate evidence classifications",
            approval_phrase=PHASE_20B_APPROVAL_PHRASE,
            provided_approval_phrase=approval_phrase,
            target_row_ids=tuple(int(row["roll_call_id"]) for row in rows),
            rollback_path=DEFAULT_ROLLBACK_PATH,
            preflight_errors=tuple(dry_run.errors),
            planned_vote_interpretation_writes=(
                dry_run.planned_vote_interpretation_inserts
                + dry_run.planned_vote_interpretation_updates
                + dry_run.planned_vote_interpretation_deletes
            ),
            expected_vote_interpretation_writes=0,
        )
    )

    inserted_ids: list[int] = []
    updated_ids: list[int] = []
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for row in rows:
                classification = row["proposed_classification"]
                params = {
                    "roll_call_id": row["roll_call_id"],
                    "is_eligible": classification["is_eligible"],
                    "eligibility_reason": classification["eligibility_reason"],
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
                    if cursor.fetchone() is not None:
                        inserted_ids.append(int(row["roll_call_id"]))
                else:
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
                    if cursor.fetchone() is not None:
                        updated_ids.append(int(row["roll_call_id"]))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return SenateClassificationWriteResult(
        dry_run=dry_run,
        inserted_classifications=len(inserted_ids),
        updated_classifications=len(updated_ids),
        skipped_existing=dry_run.skipped_existing,
        inserted_roll_call_ids=inserted_ids,
        updated_roll_call_ids=updated_ids,
    )


def write_classification_rollback_sql(
    *,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    output_path: Path = DEFAULT_ROLLBACK_PATH,
) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    insert_rows = [
        row
        for row in manifest["considered_roll_calls"]
        if row.get("eligible_for_write") is True and row.get("operation") == "insert"
    ]
    update_rows = [
        row
        for row in manifest["considered_roll_calls"]
        if row.get("eligible_for_write") is True and row.get("operation") == "update"
    ]
    legacy_update_rows = [
        row
        for row in update_rows
        if (row.get("existing_classification") or {}).get("classification_version") == LEGACY_PHASE20B_CLASSIFICATION_VERSION
    ]
    restorative_update_rows = [
        row
        for row in update_rows
        if (row.get("existing_classification") or {}).get("classification_version") != LEGACY_PHASE20B_CLASSIFICATION_VERSION
    ]
    inserted_ids = [int(row["roll_call_id"]) for row in insert_rows + legacy_update_rows]

    lines = [
        "-- Rollback for Phase 20B Senate evidence classification writes.",
        "-- Scope: vote_classifications rows from senate_evidence_classification_manifest_phase_20b.json only.",
        "-- This rollback does not touch roll_calls, votes_cast, vote_contexts, senate_amendment_references, or vote_interpretations.",
        "BEGIN;",
        "",
        "DO $$",
        "BEGIN",
        "  IF EXISTS (",
        "    SELECT 1 FROM vote_interpretations",
        f"    WHERE roll_call_id = ANY(ARRAY[{', '.join(str(value) for value in inserted_ids) or 'NULL'}]::bigint[])",
        "  ) THEN",
        "    RAISE EXCEPTION 'Phase 20B rollback stopped: target roll calls have vote_interpretations rows.';",
        "  END IF;",
        "END $$;",
        "",
    ]
    if inserted_ids:
        lines.extend(
            [
                "DELETE FROM vote_classifications",
                f"WHERE roll_call_id = ANY(ARRAY[{', '.join(str(value) for value in inserted_ids)}]::bigint[])",
                f"  AND classification_version = '{CLASSIFICATION_VERSION}';",
                "",
            ]
        )
    for row in restorative_update_rows:
        existing = row["existing_classification"]
        score_breakdown = json.dumps(existing.get("score_breakdown") or {}, sort_keys=True).replace("'", "''")
        primary_domain = existing.get("primary_domain")
        primary_domain_sql = "NULL" if primary_domain is None else f"'{primary_domain}'"
        lines.extend(
            [
                "UPDATE vote_classifications",
                f"SET is_eligible = {'TRUE' if existing['is_eligible'] else 'FALSE'},",
                f"    eligibility_reason = '{str(existing['eligibility_reason']).replace(chr(39), chr(39) + chr(39))}',",
                f"    primary_domain = {primary_domain_sql},",
                f"    score_breakdown = '{score_breakdown}'::jsonb,",
                f"    classification_version = '{str(existing['classification_version']).replace(chr(39), chr(39) + chr(39))}',",
                "    updated_at = NOW()",
                f"WHERE roll_call_id = {int(row['roll_call_id'])};",
                "",
            ]
        )
    lines.append("COMMIT;")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "output_path": str(output_path),
        "inserted_roll_call_ids": inserted_ids,
        "updated_roll_call_ids": [int(row["roll_call_id"]) for row in restorative_update_rows],
    }


def validate_post_write_state(*, manifest_path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    target_ids = [
        int(row["roll_call_id"])
        for row in manifest["considered_roll_calls"]
        if row.get("eligible_for_write") is True and row.get("operation") in {"insert", "update"}
    ]
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM vote_classifications
                WHERE roll_call_id = ANY(%s)
                  AND classification_version = %s
                """,
                (target_ids, CLASSIFICATION_VERSION),
            )
            target_classifications = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM vote_interpretations")
            total_interpretations = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM vote_interpretations WHERE support_position IS NOT NULL")
            support_non_null = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM vote_interpretations WHERE oppose_position IS NOT NULL")
            oppose_non_null = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM senate_amendment_references sar
                JOIN vote_classifications vcf ON vcf.roll_call_id = sar.roll_call_id
                WHERE vcf.classification_version = %s
                  AND vcf.roll_call_id = ANY(%s)
                """,
                (CLASSIFICATION_VERSION, target_ids),
            )
            amendment_classifications = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM vote_classifications vcf
                JOIN roll_calls rc ON rc.id = vcf.roll_call_id
                WHERE rc.chamber = 'house'
                  AND vcf.classification_version = %s
                  AND vcf.roll_call_id = ANY(%s)
                """,
                (CLASSIFICATION_VERSION, target_ids),
            )
            house_target_classifications = int(cursor.fetchone()[0])
    finally:
        connection.close()
    return {
        "target_classifications_with_active_version": target_classifications,
        "total_vote_interpretations": total_interpretations,
        "support_position_non_null": support_non_null,
        "oppose_position_non_null": oppose_non_null,
        "target_amendment_classifications_with_active_version": amendment_classifications,
        "house_target_classifications": house_target_classifications,
        "errors": [] if target_classifications == len(target_ids) and house_target_classifications == 0 else ["Post-write target classification count mismatch."],
    }


def _build_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    fact_type = "senate_amendment_fact" if row.get("amendment_number") else "bill_centered"
    existing = _serialize_existing_classification(row)
    classification = _classify_senate_fact(row, fact_type=fact_type)
    legacy_phase20b_row = (
        existing is not None
        and existing.get("classification_version") == LEGACY_PHASE20B_CLASSIFICATION_VERSION
        and bool(classification["is_eligible"])
    )
    eligible_for_write = bool(classification["is_eligible"]) and (existing is None or legacy_phase20b_row)
    operation = (
        "insert"
        if existing is None and eligible_for_write
        else "update"
        if legacy_phase20b_row
        else "skip_existing"
        if existing is not None
        else "defer"
    )
    return {
        "roll_call_id": int(row["roll_call_id"]),
        "senate_roll_number": int(row["rollcall_number"]),
        "congress": int(row["congress"]),
        "session": row.get("session"),
        "chamber": "senate",
        "date": str(row["vote_date"])[:10],
        "question": row["question"],
        "description": row["description"],
        "fact_type": fact_type,
        "bill": {
            "bill_type": row.get("bill_type"),
            "bill_number": row.get("bill_number"),
            "title": row.get("bill_title"),
            "summary": row.get("bill_summary") or "",
            "subjects": row.get("bill_subjects") or [],
        },
        "amendment_reference": _serialize_amendment_reference(row),
        "proposed_classification": classification,
        "existing_classification": existing,
        "eligible_for_write": eligible_for_write,
        "operation": operation,
        "exclusion_or_defer_reason": None if eligible_for_write else _defer_reason(classification, existing),
        "no_interpretation_included": True,
        "support_oppose_positions_inferred": False,
    }


def _classify_senate_fact(row: dict[str, Any], *, fact_type: str) -> dict[str, Any]:
    eligibility = evaluate_eligibility(row.get("question"), row.get("description"))
    source_texts: list[str] = []
    basis: list[str] = []
    status = "deferred"

    if fact_type == "senate_amendment_fact":
        purpose = str(row.get("amendment_purpose") or "")
        if _purpose_is_unusable(purpose):
            return _classification_payload(
                result=ClassificationResult(False, None, {}, CLASSIFICATION_VERSION, "amendment_purpose_missing_or_ambiguous"),
                status="deferred",
                facet=None,
                basis=["Amendment purpose is missing or too generic for deterministic issue classification."],
            )
        source_texts.append(purpose)
        basis.append("Amendment purpose/identity is the primary classification basis.")
        if row.get("description"):
            source_texts.append(str(row["description"]))
            basis.append("Senate roll-call amendment title supports amendment identity.")
        status = "eligible_deterministic" if eligibility.is_eligible else "eligible_deterministic_amendment_motion_context"
        result = classify_vote(
            committee=None,
            title=purpose,
            summary=" ".join(source_texts),
            subject_tags=[],
            classification_version=CLASSIFICATION_VERSION,
        )
    else:
        if not eligibility.is_eligible or _has_non_amendment_procedural_marker(row):
            return _classification_payload(
                result=ClassificationResult(False, None, {}, CLASSIFICATION_VERSION, "procedural_vote"),
                status="deferred",
                facet=None,
                basis=["Bill-centered roll-call question/description is procedural."],
            )
        title = " ".join(
            value
            for value in (
                str(row.get("bill_title") or ""),
                str(row.get("question") or ""),
                str(row.get("description") or ""),
            )
            if value
        )
        source_texts.append(title)
        if row.get("bill_summary"):
            source_texts.append(str(row["bill_summary"]))
        basis.append("Bill-centered classification uses bill title, roll question, roll description, summary, and subjects.")
        result = classify_vote(
            committee=None,
            title=title,
            summary=" ".join(source_texts),
            subject_tags=list(row.get("bill_subjects") or []),
            classification_version=CLASSIFICATION_VERSION,
        )
        status = "eligible_deterministic"

    if not result.is_eligible:
        status = "deferred"
    facet = _facet_for_result(result, " ".join(source_texts))
    return _classification_payload(
        result=result,
        status=status,
        facet=facet,
        basis=basis,
    )


def _classification_payload(
    *,
    result: ClassificationResult,
    status: str,
    facet: str | None,
    basis: list[str],
) -> dict[str, Any]:
    return {
        "status": status,
        "is_eligible": result.is_eligible,
        "eligibility_reason": result.eligibility_reason,
        "primary_domain": result.primary_domain,
        "proposed_facet": facet,
        "score_breakdown": result.score_breakdown,
        "classification_basis": basis,
        "classification_version": CLASSIFICATION_VERSION,
        "support_oppose_positions_inferred": False,
        "vote_interpretation_included": False,
        "confidence": _confidence_from_score(result),
    }


def _fetch_loaded_senate_fact_rows() -> list[dict[str, Any]]:
    query = """
        SELECT
            rc.id AS roll_call_id,
            rc.chamber,
            rc.congress,
            rc.session,
            rc.rollcall_number,
            rc.vote_date::date::text AS vote_date,
            rc.question,
            rc.description,
            rc.source_url,
            b.bill_type,
            b.bill_number,
            b.title AS bill_title,
            b.summary AS bill_summary,
            b.subjects AS bill_subjects,
            sar.amendment_number,
            sar.amendment_type,
            sar.amendment_to_amendment_number,
            sar.parent_bill_type,
            sar.parent_bill_number,
            sar.parent_bill_display,
            sar.amendment_purpose,
            sar.fact_status AS amendment_fact_status,
            sar.source_url AS amendment_source_url,
            vcf.is_eligible AS existing_is_eligible,
            vcf.eligibility_reason AS existing_eligibility_reason,
            vcf.primary_domain::text AS existing_primary_domain,
            vcf.score_breakdown AS existing_score_breakdown,
            vcf.classification_version AS existing_classification_version
        FROM roll_calls rc
        LEFT JOIN bills b ON b.id = rc.bill_id
        LEFT JOIN senate_amendment_references sar ON sar.roll_call_id = rc.id
        LEFT JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        WHERE rc.chamber = 'senate'
          AND rc.congress = 119
          AND rc.vote_date >= '2025-01-01'
          AND rc.vote_date < '2026-01-01'
        ORDER BY rc.rollcall_number
    """
    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(query)
                columns = [column.name for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


def _fetch_interpretation_roll_call_ids(roll_call_ids: list[int]) -> set[int]:
    if not roll_call_ids:
        return set()
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT roll_call_id FROM vote_interpretations WHERE roll_call_id = ANY(%s)",
                (roll_call_ids,),
            )
            return {int(row[0]) for row in cursor.fetchall()}
    finally:
        connection.close()


def _serialize_existing_classification(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("existing_classification_version") is None:
        return None
    return {
        "is_eligible": bool(row["existing_is_eligible"]),
        "eligibility_reason": row["existing_eligibility_reason"],
        "primary_domain": row["existing_primary_domain"],
        "score_breakdown": row.get("existing_score_breakdown") or {},
        "classification_version": row["existing_classification_version"],
    }


def _serialize_amendment_reference(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("amendment_number") is None:
        return None
    return {
        "amendment_number": row.get("amendment_number"),
        "amendment_type": row.get("amendment_type"),
        "amendment_to_amendment_number": row.get("amendment_to_amendment_number"),
        "parent_bill_type": row.get("parent_bill_type"),
        "parent_bill_number": row.get("parent_bill_number"),
        "parent_bill_display": row.get("parent_bill_display"),
        "amendment_purpose": row.get("amendment_purpose"),
        "fact_status": row.get("amendment_fact_status"),
        "source_url": row.get("amendment_source_url"),
        "counts_as_interpretation": False,
    }


def _purpose_is_unusable(purpose: str) -> bool:
    normalized = purpose.strip().lower()
    return not normalized or any(marker in normalized for marker in GENERIC_OR_UNUSABLE_PURPOSE_MARKERS)


def _has_non_amendment_procedural_marker(row: dict[str, Any]) -> bool:
    haystack = f"{row.get('question') or ''} {row.get('description') or ''}".lower()
    return any(marker in haystack for marker in NON_AMENDMENT_PROCEDURAL_MARKERS)


def _confidence_from_score(result: ClassificationResult) -> str:
    if not result.is_eligible:
        return "still_limited"
    score = max((sum(parts.values()) for parts in result.score_breakdown.values()), default=0)
    if score >= CLASSIFICATION_THRESHOLD + 3:
        return "strong"
    return "contextual"


def _facet_for_result(result: ClassificationResult, text: str) -> str | None:
    if result.primary_domain is None:
        return None
    lowered = text.lower()
    for facet, signals in FACET_SIGNALS.get(result.primary_domain, ()):
        if any(signal in lowered for signal in signals):
            return facet
    return result.primary_domain.lower()


def _defer_reason(classification: dict[str, Any], existing: dict[str, Any] | None) -> str:
    if existing is not None:
        return "Existing vote_classifications row left unchanged."
    if classification.get("is_eligible") is not True:
        return str(classification.get("eligibility_reason") or "deterministic classification confidence below threshold")
    return "Not eligible for write."


def _summarize_manifest_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [row for row in rows if row.get("eligible_for_write") is True]
    existing = [row for row in rows if row.get("existing_classification")]
    deferred = [row for row in rows if row.get("eligible_for_write") is not True and not row.get("existing_classification")]
    by_domain: dict[str, int] = {}
    by_fact_type: dict[str, int] = {}
    for row in eligible:
        domain = row["proposed_classification"]["primary_domain"]
        by_domain[domain] = by_domain.get(domain, 0) + 1
        fact_type = row["fact_type"]
        by_fact_type[fact_type] = by_fact_type.get(fact_type, 0) + 1
    return {
        "considered_roll_calls": len(rows),
        "existing_classifications": len(existing),
        "eligible_for_write": len(eligible),
        "planned_inserts": sum(1 for row in eligible if row.get("operation") == "insert"),
        "planned_updates": sum(1 for row in eligible if row.get("operation") == "update"),
        "deferred_without_existing_classification": len(deferred),
        "eligible_by_domain": dict(sorted(by_domain.items())),
        "eligible_by_fact_type": dict(sorted(by_fact_type.items())),
        "vote_interpretations_included": 0,
        "support_oppose_positions_inferred": False,
    }


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build, validate, dry-run, and write bounded Senate evidence classifications for Phase 20B."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build-manifest")
    build_parser.add_argument("--output", type=Path, default=DEFAULT_MANIFEST_PATH)

    validate_parser = subparsers.add_parser("validate-manifest")
    validate_parser.add_argument("--input", type=Path, default=DEFAULT_MANIFEST_PATH)

    dry_run_parser = subparsers.add_parser("dry-run")
    dry_run_parser.add_argument("--input", type=Path, default=DEFAULT_MANIFEST_PATH)

    rollback_parser = subparsers.add_parser("write-rollback")
    rollback_parser.add_argument("--input", type=Path, default=DEFAULT_MANIFEST_PATH)
    rollback_parser.add_argument("--output", type=Path, default=DEFAULT_ROLLBACK_PATH)

    write_parser = subparsers.add_parser("write-production")
    write_parser.add_argument("--input", type=Path, default=DEFAULT_MANIFEST_PATH)
    write_parser.add_argument("--approval-phrase", required=True)

    post_parser = subparsers.add_parser("post-validate")
    post_parser.add_argument("--input", type=Path, default=DEFAULT_MANIFEST_PATH)

    args = parser.parse_args()
    if args.command == "build-manifest":
        result = write_senate_evidence_classification_manifest(output_path=args.output)
    elif args.command == "validate-manifest":
        result = validate_senate_evidence_classification_manifest(_load_manifest(args.input))
    elif args.command == "dry-run":
        result = run_senate_evidence_classification_dry_run(manifest_path=args.input).to_dict()
    elif args.command == "write-rollback":
        result = write_classification_rollback_sql(manifest_path=args.input, output_path=args.output)
    elif args.command == "write-production":
        result = write_senate_evidence_classifications(
            manifest_path=args.input,
            approval_phrase=args.approval_phrase,
        ).to_dict()
    else:
        result = validate_post_write_state(manifest_path=args.input)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
