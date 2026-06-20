import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CANONICAL_AMENDMENT_EVIDENCE_STEPS = (
    "fetch/cache",
    "normalize identity and relationships",
    "validate direct-source grounding",
    "classify eligibility and issue",
    "build interpretation package",
    "preview writes",
    "capture rollback",
    "perform bounded writes",
    "recompute affected outputs",
    "reconcile and verify",
    "rerun to prove idempotency",
)

NON_COUNTING_INTERPRETATION_STATUSES = {"ambiguous", "insufficient_evidence"}
COUNTING_SUPPORT_POSITIONS = {"yea", "nay"}


@dataclass(frozen=True)
class AmendmentIdentity:
    chamber: str
    congress: int
    amendment_number: str | None
    amendment_type: str | None = None
    parent_bill_type: str | None = None
    parent_bill_number: int | None = None
    amendment_to_amendment_number: str | None = None
    sponsor_text: str | None = None
    label: str | None = None
    source: str | None = None

    @property
    def has_direct_identity(self) -> bool:
        return bool(self.amendment_number)

    @property
    def key(self) -> tuple[Any, ...]:
        return (
            self.chamber.lower(),
            self.congress,
            _clean(self.amendment_type),
            _clean(self.amendment_number),
            _clean(self.parent_bill_type),
            self.parent_bill_number,
            _clean(self.amendment_to_amendment_number),
        )


@dataclass(frozen=True)
class WritePrecondition:
    scope: str
    approval_phrase: str
    provided_approval_phrase: str
    target_row_ids: tuple[int, ...]
    rollback_path: Path | str | None
    preflight_errors: tuple[str, ...] = ()
    planned_vote_interpretation_writes: int = 0
    expected_vote_interpretation_writes: int | None = None


def parse_house_amendment_identity(*, description: str | None, congress: int) -> AmendmentIdentity:
    text = str(description or "").strip()
    match = re.search(
        r"^(?P<sponsor>.+?)\s+Part\s+(?P<part>[A-Z])\s+Amendment\s+No\.\s*(?P<number>\d+)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return AmendmentIdentity(
            chamber="house",
            congress=congress,
            amendment_number=None,
            source="house_roll_description",
        )
    number = match.group("number")
    part = match.group("part").upper()
    sponsor = " ".join(match.group("sponsor").split())
    return AmendmentIdentity(
        chamber="house",
        congress=congress,
        amendment_number=number,
        amendment_type="house_printed_amendment",
        sponsor_text=sponsor,
        label=f"Part {part} Amendment No. {number}",
        source="house_roll_description",
    )


def parse_senate_amendment_identity(reference: dict[str, Any], *, congress: int) -> AmendmentIdentity:
    parent_number = reference.get("parent_bill_number")
    return AmendmentIdentity(
        chamber="senate",
        congress=congress,
        amendment_number=_clean(reference.get("amendment_number")),
        amendment_type=_clean(reference.get("amendment_type")),
        parent_bill_type=_clean(reference.get("parent_bill_type")),
        parent_bill_number=int(parent_number) if parent_number is not None else None,
        amendment_to_amendment_number=_clean(reference.get("amendment_to_amendment_number")),
        label=_clean(reference.get("amendment_number")),
        source="senate_amendment_references",
    )


def interpretation_package_respects_counting_boundary(record: dict[str, Any]) -> bool:
    status = _clean(record.get("interpretation_status"))
    support_position = _clean(record.get("support_position"))
    oppose_position = _clean(record.get("oppose_position"))
    if status in NON_COUNTING_INTERPRETATION_STATUSES:
        return support_position is None and oppose_position is None
    if status == "interpreted":
        return (
            support_position in COUNTING_SUPPORT_POSITIONS
            and oppose_position in COUNTING_SUPPORT_POSITIONS
            and support_position != oppose_position
        )
    return False


def validate_write_precondition(precondition: WritePrecondition) -> dict[str, Any]:
    errors: list[str] = []
    if not precondition.scope.strip():
        errors.append("Production write scope is required.")
    if precondition.provided_approval_phrase != precondition.approval_phrase:
        errors.append("Approval phrase does not exactly match.")
    if not precondition.target_row_ids:
        errors.append("Exact target row ids are required.")
    if len(set(precondition.target_row_ids)) != len(precondition.target_row_ids):
        errors.append("Exact target row ids must not contain duplicates.")
    if precondition.rollback_path is None or not str(precondition.rollback_path).strip():
        errors.append("Rollback artifact path is required before writing.")
    errors.extend(precondition.preflight_errors)
    if precondition.expected_vote_interpretation_writes is not None and (
        precondition.planned_vote_interpretation_writes != precondition.expected_vote_interpretation_writes
    ):
        errors.append(
            "Planned vote_interpretation writes do not match the approved write class."
        )
    return {
        "valid": not errors,
        "errors": errors,
        "scope": precondition.scope,
        "target_row_count": len(precondition.target_row_ids),
        "target_row_ids": list(precondition.target_row_ids),
        "rollback_path": None if precondition.rollback_path is None else str(precondition.rollback_path),
    }


def require_write_precondition(precondition: WritePrecondition) -> dict[str, Any]:
    result = validate_write_precondition(precondition)
    if result["errors"]:
        raise ValueError(f"Production write precondition failed: {result['errors']}")
    return result


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
