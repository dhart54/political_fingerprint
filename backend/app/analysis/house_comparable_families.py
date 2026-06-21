from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "docs" / "derived" / "house_comparable_policy_question_families_v1.json"
ARTIFACT_VERSION = "house-comparable-policy-question-families-v1"
EXPECTED_TOTALS = {
    "target_interpreted_roll_calls": 306,
    "candidate_families_identified": 15,
    "common_families_identified": 13,
    "directly_comparable_common_families": 4,
    "conditionally_comparable_common_families": 7,
    "related_but_non_comparable_clusters": 4,
    "ungrouped_roll_calls": 225,
    "substantive_vote_rows_in_candidate_families": 33825,
    "substantive_vote_rows_covered_share": 0.2659,
}
COMPARABLE_STATUSES = {"directly_comparable", "conditionally_comparable"}
VALID_STATUSES = COMPARABLE_STATUSES | {"related_but_not_comparable"}
FORBIDDEN_OUTPUT_KEYS = {
    "continuity",
    "change",
    "movement",
    "movement_label",
    "changed_position",
    "ideological_movement",
    "behavioral_movement",
    "causal_claim",
}

ComparabilityStatus = Literal["directly_comparable", "conditionally_comparable", "related_but_not_comparable"]


class ComparableFamilyArtifactError(ValueError):
    """Raised when the comparable-family artifact cannot be loaded or validated."""


@dataclass(frozen=True)
class ComparableFamily:
    family_id: str
    family_name: str
    issue_domain: str
    comparability_status: ComparabilityStatus
    eligible_for_future_limited_record_across_congresses: bool
    governing_question: str
    inclusion_criteria: str
    exclusion_criteria: str
    source_grounded_rationale: str
    caveats_and_limitations: str
    congresses_represented: tuple[int, ...]
    vote_types_represented: tuple[str, ...]
    roll_call_ids_by_congress: dict[int, tuple[int, ...]]
    measures_and_amendments_represented: tuple[dict[str, Any], ...]
    representative_examples: tuple[dict[str, Any], ...]

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "ComparableFamily":
        return cls(
            family_id=str(row["family_id"]),
            family_name=str(row["family_name"]),
            issue_domain=str(row["issue_domain"]),
            comparability_status=row["comparability_status"],
            eligible_for_future_limited_record_across_congresses=bool(row["eligible_for_future_limited_record_across_congresses"]),
            governing_question=str(row["governing_question"]),
            inclusion_criteria=str(row["inclusion_criteria"]),
            exclusion_criteria=str(row["exclusion_criteria"]),
            source_grounded_rationale=str(row["source_grounded_rationale"]),
            caveats_and_limitations=str(row["caveats_and_limitations"]),
            congresses_represented=tuple(int(value) for value in row["congresses_represented"]),
            vote_types_represented=tuple(str(value) for value in row["vote_types_represented"]),
            roll_call_ids_by_congress={
                int(congress): tuple(int(roll_call_id) for roll_call_id in roll_call_ids)
                for congress, roll_call_ids in row["roll_call_ids_by_congress"].items()
            },
            measures_and_amendments_represented=tuple(dict(value) for value in row["measures_and_amendments_represented"]),
            representative_examples=tuple(dict(value) for value in row["representative_examples"]),
        )

    @property
    def is_directly_comparable(self) -> bool:
        return self.comparability_status == "directly_comparable"

    @property
    def is_conditionally_comparable(self) -> bool:
        return self.comparability_status == "conditionally_comparable"

    @property
    def is_related_but_not_comparable(self) -> bool:
        return self.comparability_status == "related_but_not_comparable"


@dataclass(frozen=True)
class UngroupedComparableRows:
    comparability_status: str
    eligible_for_future_limited_record_across_congresses: bool
    roll_call_count: int
    roll_call_ids_by_congress: dict[int, tuple[int, ...]]
    exclusion_reason: str

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "UngroupedComparableRows":
        return cls(
            comparability_status=str(row["comparability_status"]),
            eligible_for_future_limited_record_across_congresses=bool(row["eligible_for_future_limited_record_across_congresses"]),
            roll_call_count=int(row["roll_call_count"]),
            roll_call_ids_by_congress={
                int(congress): tuple(int(roll_call_id) for roll_call_id in roll_call_ids)
                for congress, roll_call_ids in row["roll_call_ids_by_congress"].items()
            },
            exclusion_reason=str(row["exclusion_reason"]),
        )


@dataclass(frozen=True)
class ComparableFamilyArtifact:
    artifact_version: str
    generated_at: str
    recommendations: dict[str, Any]
    totals: dict[str, Any]
    explicit_non_authorization: dict[str, Any]
    families: tuple[ComparableFamily, ...]
    ungrouped: UngroupedComparableRows

    def all_families(self) -> tuple[ComparableFamily, ...]:
        return self.families

    def family_by_id(self, family_id: str) -> ComparableFamily:
        for family in self.families:
            if family.family_id == family_id:
                return family
        raise KeyError(f"Unknown comparable family: {family_id}")

    def families_by_domain(self, issue_domain: str) -> tuple[ComparableFamily, ...]:
        return tuple(family for family in self.families if family.issue_domain == issue_domain)

    def families_by_status(self, status: ComparabilityStatus) -> tuple[ComparableFamily, ...]:
        return tuple(family for family in self.families if family.comparability_status == status)

    def eligible_families(self) -> tuple[ComparableFamily, ...]:
        return tuple(family for family in self.families if family.eligible_for_future_limited_record_across_congresses)

    def directly_comparable_eligible_families(self) -> tuple[ComparableFamily, ...]:
        return tuple(family for family in self.eligible_families() if family.is_directly_comparable)

    def conditionally_comparable_eligible_families(self) -> tuple[ComparableFamily, ...]:
        return tuple(family for family in self.eligible_families() if family.is_conditionally_comparable)

    def related_but_not_comparable_families(self) -> tuple[ComparableFamily, ...]:
        return self.families_by_status("related_but_not_comparable")

    def roll_call_ids_by_congress(self, family_id: str) -> dict[int, tuple[int, ...]]:
        return self.family_by_id(family_id).roll_call_ids_by_congress


def load_house_comparable_family_artifact(path: Path | None = None) -> ComparableFamilyArtifact:
    artifact_path = path or DEFAULT_ARTIFACT_PATH
    if not artifact_path.exists():
        raise ComparableFamilyArtifactError(f"House comparable-family artifact not found: {artifact_path}")
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ComparableFamilyArtifactError(f"House comparable-family artifact is not valid JSON: {exc}") from exc
    validate_artifact_payload(payload)
    return ComparableFamilyArtifact(
        artifact_version=str(payload["artifact_version"]),
        generated_at=str(payload["generated_at"]),
        recommendations=dict(payload["recommendations"]),
        totals=dict(payload["totals"]),
        explicit_non_authorization=dict(payload["explicit_non_authorization"]),
        families=tuple(ComparableFamily.from_dict(row) for row in payload["families"]),
        ungrouped=UngroupedComparableRows.from_dict(payload["ungrouped"]),
    )


def validate_artifact_payload(payload: dict[str, Any]) -> None:
    errors: list[str] = []
    for key in (
        "artifact_version",
        "generated_at",
        "recommendations",
        "totals",
        "explicit_non_authorization",
        "families",
        "ungrouped",
    ):
        if key not in payload:
            errors.append(f"Missing required top-level key: {key}")
    if errors:
        raise ComparableFamilyArtifactError("; ".join(errors))

    if payload["artifact_version"] != ARTIFACT_VERSION:
        errors.append(f"Unexpected artifact version: {payload['artifact_version']}")
    for key, expected in EXPECTED_TOTALS.items():
        actual = payload["totals"].get(key)
        if actual != expected:
            errors.append(f"Unexpected artifact total for {key}: expected {expected}, got {actual}")

    non_authorization = payload["explicit_non_authorization"]
    for key in (
        "does_not_authorize_continuity_change_claims",
        "does_not_authorize_behavioral_movement_claims",
        "does_not_authorize_ideological_movement_claims",
        "does_not_authorize_causal_claims",
        "does_not_authorize_frontend_comparison_copy",
    ):
        if non_authorization.get(key) is not True:
            errors.append(f"Missing required non-authorization flag: {key}")

    seen_family_ids: set[str] = set()
    for row in payload["families"]:
        errors.extend(validate_family_row(row, seen_family_ids))
    errors.extend(validate_ungrouped(payload["ungrouped"]))

    if contains_forbidden_generated_fields(payload):
        errors.append("Artifact contains forbidden generated continuity/change or movement fields.")
    if errors:
        raise ComparableFamilyArtifactError("; ".join(errors))


def validate_family_row(row: dict[str, Any], seen_family_ids: set[str]) -> list[str]:
    errors: list[str] = []
    family_id = row.get("family_id")
    if not family_id:
        errors.append("Family row missing family_id.")
    elif family_id in seen_family_ids:
        errors.append(f"Duplicate family_id: {family_id}")
    else:
        seen_family_ids.add(str(family_id))

    for key in (
        "family_name",
        "issue_domain",
        "comparability_status",
        "eligible_for_future_limited_record_across_congresses",
        "governing_question",
        "inclusion_criteria",
        "exclusion_criteria",
        "source_grounded_rationale",
        "caveats_and_limitations",
        "roll_call_ids_by_congress",
    ):
        if key not in row:
            errors.append(f"Family {family_id} missing required key: {key}")
    if errors:
        return errors

    status = row["comparability_status"]
    if status not in VALID_STATUSES:
        errors.append(f"Family {family_id} has invalid comparability status: {status}")
    eligible = bool(row["eligible_for_future_limited_record_across_congresses"])
    has_118 = bool(row["roll_call_ids_by_congress"].get("118"))
    has_119 = bool(row["roll_call_ids_by_congress"].get("119"))
    if status in COMPARABLE_STATUSES:
        if not eligible:
            errors.append(f"Comparable family {family_id} is not marked future-limited eligible.")
        if not (has_118 and has_119):
            errors.append(f"Comparable family {family_id} does not contain both Congresses.")
    if status == "related_but_not_comparable" and eligible:
        errors.append(f"Related family {family_id} is incorrectly eligible.")

    for congress, roll_call_ids in row["roll_call_ids_by_congress"].items():
        if congress not in {"118", "119"}:
            errors.append(f"Family {family_id} has unsupported Congress key: {congress}")
        if not all(isinstance(roll_call_id, int) for roll_call_id in roll_call_ids):
            errors.append(f"Family {family_id} has non-integer roll-call IDs for Congress {congress}.")
    return errors


def validate_ungrouped(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if row.get("comparability_status") != "ungrouped":
        errors.append("Ungrouped rows missing ungrouped comparability status.")
    if row.get("eligible_for_future_limited_record_across_congresses") is not False:
        errors.append("Ungrouped rows are incorrectly eligible.")
    if row.get("roll_call_count") != EXPECTED_TOTALS["ungrouped_roll_calls"]:
        errors.append("Ungrouped roll-call count no longer reconciles with PR #45 totals.")
    for congress, roll_call_ids in row.get("roll_call_ids_by_congress", {}).items():
        if congress not in {"118", "119"}:
            errors.append(f"Ungrouped rows have unsupported Congress key: {congress}")
        if not all(isinstance(roll_call_id, int) for roll_call_id in roll_call_ids):
            errors.append(f"Ungrouped rows have non-integer roll-call IDs for Congress {congress}.")
    return errors


def contains_forbidden_generated_fields(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                return True
            if contains_forbidden_generated_fields(child):
                return True
    elif isinstance(value, list):
        return any(contains_forbidden_generated_fields(child) for child in value)
    return False
