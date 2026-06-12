import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from app.etl.fetch_sources import SENATE_XML_CACHE_DIR
from app.etl.senate_xml_adapter import _build_senate_source_url, _normalize_senate_vote_date


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
    parser = argparse.ArgumentParser(description="Build or validate a local Senate amendment fact-model manifest.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--senate-xml-dir", type=Path, default=SENATE_XML_CACHE_DIR)
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args()

    if args.validate:
        manifest = json.loads(args.validate.read_text(encoding="utf-8"))
        result = validate_senate_amendment_fact_manifest(manifest)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        if result.errors:
            raise SystemExit(1)
        return

    if args.output is None:
        raise SystemExit("--output is required unless --validate is used.")

    result = write_senate_amendment_fact_manifest(
        output_path=args.output,
        senate_xml_dir=args.senate_xml_dir,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
