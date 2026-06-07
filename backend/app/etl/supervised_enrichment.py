import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUBSTANTIVE_INTERPRETATION = "substantive_interpretation"
PROCEDURAL_CONTEXT = "procedural_context"
STILL_INSUFFICIENT = "still_insufficient"

CANDIDATE_TYPES = {
    SUBSTANTIVE_INTERPRETATION,
    PROCEDURAL_CONTEXT,
    STILL_INSUFFICIENT,
}

SUBSTANTIVE_ALIASES = {
    "substantive",
    "substantive_candidate",
    "substantive_interpretation",
    "substantive interpretation candidate",
}
PROCEDURAL_ALIASES = {
    "procedural",
    "procedural-context",
    "procedural_context",
    "procedural context candidate",
}
INSUFFICIENT_ALIASES = {
    "insufficient",
    "still_insufficient",
    "still insufficient",
    "still limited",
}
NON_COUNTING_STATUSES = {"ambiguous", "insufficient_evidence"}
VALID_VOTE_POSITIONS = {"yea", "nay", "present", "not_voting"}
PROCEDURAL_VOTE_TYPES = {
    "rule",
    "motion",
    "procedural",
    "previous_question",
    "concurrence",
    "motion_to_commit",
}
PROCEDURAL_TEXT_MARKERS = (
    "previous question",
    "providing for consideration",
    "agreeing to the resolution",
    "house resolution",
    "rule",
    "motion to commit",
)


@dataclass(frozen=True)
class CandidateClassification:
    candidate_type: str
    errors: list[str]
    warnings: list[str]


def classify_enrichment_candidate(record: dict[str, Any]) -> CandidateClassification:
    """Classify a review candidate without deciding whether it should be imported."""
    candidate_type = _declared_candidate_type(record) or _infer_candidate_type(record)
    errors: list[str] = []
    warnings: list[str] = []

    roll_call_id = record.get("roll_call_id")
    if not roll_call_id:
        errors.append("roll_call_id is required")

    status = _clean(record.get("interpretation_status"))
    support_position = _clean(record.get("support_position"))
    oppose_position = _clean(record.get("oppose_position"))

    if candidate_type == SUBSTANTIVE_INTERPRETATION:
        if status != "interpreted":
            errors.append("substantive candidates must use interpretation_status interpreted")
        if support_position not in VALID_VOTE_POSITIONS or oppose_position not in VALID_VOTE_POSITIONS:
            errors.append("substantive candidates require support_position and oppose_position")
        elif support_position == oppose_position:
            errors.append("support_position and oppose_position must differ")
        if _has_procedural_source_signal(record):
            errors.append("procedural or floor-rule-only rows cannot be substantive candidates")
        if not _source_basis(record):
            errors.append("substantive candidates require source_basis")

    elif candidate_type == PROCEDURAL_CONTEXT:
        if status not in NON_COUNTING_STATUSES:
            errors.append("procedural-context candidates must remain non-interpreted")
        if support_position is not None or oppose_position is not None:
            errors.append("procedural-context candidates must leave support_position and oppose_position null")
        if not _has_procedural_source_signal(record):
            errors.append("procedural-context candidates require an explicit procedural source signal")
        if not _source_basis(record):
            warnings.append("procedural-context candidates should include source_basis before import review")

    elif candidate_type == STILL_INSUFFICIENT:
        if status not in NON_COUNTING_STATUSES:
            errors.append("still-insufficient candidates must remain ambiguous or insufficient_evidence")
        if support_position is not None or oppose_position is not None:
            errors.append("still-insufficient candidates must leave support_position and oppose_position null")
        if _issue_facet_only_signal(record):
            warnings.append("issue_facet alone is not source meaning; keep this row insufficient without closer context")

    else:
        errors.append(f"unknown candidate type {candidate_type}")

    return CandidateClassification(candidate_type=candidate_type, errors=errors, warnings=warnings)


def validate_supervised_batch(payload: dict[str, Any]) -> dict[str, Any]:
    records = _candidate_records(payload)
    counts = {candidate_type: 0 for candidate_type in CANDIDATE_TYPES}
    errors: list[str] = []
    warnings: list[str] = []

    for index, record in enumerate(records):
        classification = classify_enrichment_candidate(record)
        counts[classification.candidate_type] = counts.get(classification.candidate_type, 0) + 1
        errors.extend(f"candidates[{index}]: {error}" for error in classification.errors)
        warnings.extend(f"candidates[{index}]: {warning}" for warning in classification.warnings)

    return {
        "candidate_count": len(records),
        "candidate_type_counts": {
            SUBSTANTIVE_INTERPRETATION: counts.get(SUBSTANTIVE_INTERPRETATION, 0),
            PROCEDURAL_CONTEXT: counts.get(PROCEDURAL_CONTEXT, 0),
            STILL_INSUFFICIENT: counts.get(STILL_INSUFFICIENT, 0),
        },
        "errors": errors,
        "warnings": warnings,
        "workflow_boundary": [
            "Production reads may inform this artifact.",
            "This validation does not import or write production data.",
            "Procedural-context rows must stay non-counting with null support/opposition positions.",
            "A separate explicit approval gate is required before any production write.",
        ],
    }


def build_approval_gate_checklist(payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_supervised_batch(payload)
    records = _candidate_records(payload)
    roll_call_ids = [record.get("roll_call_id") for record in records if record.get("roll_call_id")]
    return {
        "roll_call_ids": roll_call_ids,
        "candidate_type_counts": validation["candidate_type_counts"],
        "validation_errors": validation["errors"],
        "required_confirmations": [
            "Exact roll_call_id list has been reviewed.",
            "Insert/update behavior has been checked against production before import.",
            "Rollback artifact exists and targets only the approved rows.",
            "Support/opposition count impact has been checked.",
            "Alignment impact has been checked.",
            "No production write occurs until the exact approval phrase is provided.",
        ],
        "approval_phrases": {
            SUBSTANTIVE_INTERPRETATION: (
                "Approve production import of the named substantive interpretation batch, "
                "with reviewed support_position and oppose_position values and confirmed support/opposition and alignment impact."
            ),
            PROCEDURAL_CONTEXT: (
                "Approve production import of the named procedural-context batch, "
                "with support_position and oppose_position null and no support/opposition or alignment counting changes."
            ),
        },
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("candidates", "candidate_interpretations", "interpretations"):
        records = payload.get(key)
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
    return []


def _declared_candidate_type(record: dict[str, Any]) -> str | None:
    raw_value = _clean(record.get("candidate_type") or record.get("candidate_category"))
    if raw_value is None:
        return None
    normalized = raw_value.replace("_", " ").replace("-", " ")
    if raw_value in SUBSTANTIVE_ALIASES or normalized in SUBSTANTIVE_ALIASES:
        return SUBSTANTIVE_INTERPRETATION
    if raw_value in PROCEDURAL_ALIASES or normalized in PROCEDURAL_ALIASES:
        return PROCEDURAL_CONTEXT
    if raw_value in INSUFFICIENT_ALIASES or normalized in INSUFFICIENT_ALIASES:
        return STILL_INSUFFICIENT
    return raw_value


def _infer_candidate_type(record: dict[str, Any]) -> str:
    if bool(record.get("procedural_context")) or _has_procedural_source_signal(record):
        return PROCEDURAL_CONTEXT
    if _clean(record.get("interpretation_status")) == "interpreted" and record.get("support_position") and record.get("oppose_position"):
        return SUBSTANTIVE_INTERPRETATION
    return STILL_INSUFFICIENT


def _has_procedural_source_signal(record: dict[str, Any]) -> bool:
    if bool(record.get("procedural_context")):
        return True
    vote_type = _clean(record.get("vote_type"))
    if vote_type in PROCEDURAL_VOTE_TYPES:
        return True
    haystack = " ".join(
        str(value or "")
        for value in (
            record.get("vote_type"),
            record.get("roll_call_question"),
            record.get("question"),
            record.get("vote_question"),
            record.get("what_happened"),
            record.get("plain_english_summary"),
        )
    ).lower()
    return any(marker in haystack for marker in PROCEDURAL_TEXT_MARKERS)


def _issue_facet_only_signal(record: dict[str, Any]) -> bool:
    return bool(record.get("issue_facet")) and not _has_procedural_source_signal(record) and not _source_basis(record)


def _source_basis(record: dict[str, Any]) -> list[Any]:
    source_basis = record.get("source_basis")
    return source_basis if isinstance(source_basis, list) else []


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate supervised enrichment review artifacts. "
            "This command is offline/review-only and never writes production data."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-batch")
    validate_parser.add_argument("--input", required=True)

    checklist_parser = subparsers.add_parser("approval-checklist")
    checklist_parser.add_argument("--input", required=True)

    args = parser.parse_args()
    payload = load_json(Path(args.input))
    if args.command == "validate-batch":
        result = validate_supervised_batch(payload)
    else:
        result = build_approval_gate_checklist(payload)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
