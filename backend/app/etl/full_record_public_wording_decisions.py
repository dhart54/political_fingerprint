"""Generic fail-closed human public-wording authority and implementation."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from typing import Any


DOWNSTREAM_AUTHORIZATIONS = {
    "publication": False,
    "production_persistence": False,
    "database_writes": False,
    "production_writes": False,
    "deployment": False,
}
ALLOWED_DECISIONS = {"accept_candidate_as_written", "accept_with_bounded_revision"}
ALLOWED_TOP_LEVEL_COPY_FIELDS = {
    "public_title",
    "primary_sentence",
    "secondary_clarification",
    "evidence_count_label",
    "compression_notes",
}
GENERIC_UPSTREAM_BINDINGS = (
    "behavioral_semantic_ir_authority_binding",
    "behavioral_semantic_ir_implementation_binding",
    "synthesis_authority_binding",
    "synthesis_implementation_binding",
)
LEGACY_UPSTREAM_BINDINGS = (
    "m11h_authority_binding",
    "m11h_implementation_binding",
    "m11j_authority_binding",
    "m11j_implementation_binding",
)


class PublicWordingDecisionError(ValueError):
    """Raised when a wording decision exceeds human-reviewed copy authority."""


def digest(value: object) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def seal(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result.pop(field, None)
    result[field] = digest(result)
    return result


def verify_seal(value: dict[str, Any], field: str, label: str) -> None:
    subject = {key: child for key, child in value.items() if key != field}
    if value.get(field) != digest(subject):
        raise PublicWordingDecisionError(f"{label}: {field} differs")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicWordingDecisionError(message)


def _items(package: dict[str, Any]) -> list[dict[str, Any]]:
    return package["subject"]["wording_items"]


def upstream_binding_names(subject: dict[str, Any]) -> tuple[str, ...]:
    """Select the milestone-neutral contract, with explicit frozen-M11 fallback."""

    if all(name in subject for name in GENERIC_UPSTREAM_BINDINGS):
        _require(
            not any(name in subject for name in LEGACY_UPSTREAM_BINDINGS),
            "mixed generic and legacy public-wording bindings",
        )
        return GENERIC_UPSTREAM_BINDINGS
    _require(
        all(name in subject for name in LEGACY_UPSTREAM_BINDINGS)
        and not any(name in subject for name in GENERIC_UPSTREAM_BINDINGS),
        "public-wording upstream binding contract differs",
    )
    return LEGACY_UPSTREAM_BINDINGS


def blocked_action_boundaries(subject: dict[str, Any]) -> list[dict[str, Any]]:
    """Return zero-or-more boundaries while preserving frozen singular M11 input."""

    if "blocked_action_boundaries" in subject:
        _require(
            "blocked_action_boundary" not in subject,
            "mixed singular and plural blocked-action boundaries",
        )
        boundaries = subject["blocked_action_boundaries"]
        _require(
            isinstance(boundaries, list), "blocked-action boundaries must be a list"
        )
        return boundaries
    _require(
        "blocked_action_boundary" in subject,
        "blocked-action boundary accounting is absent",
    )
    return [subject["blocked_action_boundary"]]


def require_blocked_action_parity(
    actual_subject: dict[str, Any], package_subject: dict[str, Any]
) -> None:
    actual = blocked_action_boundaries(actual_subject)
    expected = blocked_action_boundaries(package_subject)
    _require(actual == expected, "blocked-action boundaries differ")

    def action_id(row: dict[str, Any]) -> object:
        return row.get("canonical_action_id", row.get("action_id"))

    blocked_ids = [action_id(row) for row in actual_subject["blocked_actions"]]
    boundary_ids = [action_id(row) for row in actual]
    _require(
        all(value is not None for value in (*blocked_ids, *boundary_ids))
        and len(blocked_ids) == len(set(blocked_ids))
        and len(boundary_ids) == len(set(boundary_ids))
        and set(blocked_ids) == set(boundary_ids),
        "blocked actions and blocked-action boundaries do not reconcile",
    )


def _allowed_path(original: dict[str, Any], path: list[object]) -> bool:
    if len(path) == 1 and path[0] in ALLOWED_TOP_LEVEL_COPY_FIELDS:
        return True
    if (
        len(path) == 3
        and path[0] == "limitation_treatments"
        and isinstance(path[1], int)
        and path[2] in {"public_copy", "reason"}
        and 0 <= path[1] < len(original["limitation_treatments"])
    ):
        return True
    return False


def structural_projection(item: dict[str, Any]) -> dict[str, Any]:
    """Return every wording field that human copy revision cannot change."""

    result = deepcopy(item)
    result.pop("wording_item_subject_sha256", None)
    for field in ALLOWED_TOP_LEVEL_COPY_FIELDS:
        result[field] = "<reviewed-copy-field>"
    for row in result["limitation_treatments"]:
        row["public_copy"] = "<reviewed-copy-field>"
        row["reason"] = "<reviewed-copy-field>"
    return result


def require_structural_invariance(
    original: dict[str, Any], revised: dict[str, Any]
) -> None:
    if structural_projection(original) != structural_projection(revised):
        raise PublicWordingDecisionError(
            "bounded wording revision changed structural or evidence identity"
        )


def _value_at_path(value: object, path: list[object]) -> object:
    cursor = value
    for key in path:
        if isinstance(cursor, list) and isinstance(key, int) and 0 <= key < len(cursor):
            cursor = cursor[key]
        elif isinstance(cursor, dict) and isinstance(key, str) and key in cursor:
            cursor = cursor[key]
        else:
            raise PublicWordingDecisionError("bounded wording revision path differs")
    return cursor


def _replace_path(value: object, path: list[object], replacement: object) -> None:
    cursor = value
    for key in path[:-1]:
        if isinstance(cursor, list) and isinstance(key, int) and 0 <= key < len(cursor):
            cursor = cursor[key]
        elif isinstance(cursor, dict) and isinstance(key, str) and key in cursor:
            cursor = cursor[key]
        else:
            raise PublicWordingDecisionError("bounded wording revision path differs")
    key = path[-1]
    if isinstance(cursor, list) and isinstance(key, int) and 0 <= key < len(cursor):
        cursor[key] = deepcopy(replacement)
    elif isinstance(cursor, dict) and isinstance(key, str) and key in cursor:
        cursor[key] = deepcopy(replacement)
    else:
        raise PublicWordingDecisionError("bounded wording revision target differs")


def apply_bounded_revision(
    original: dict[str, Any], revision: dict[str, Any] | None
) -> dict[str, Any]:
    if revision is None:
        return deepcopy(original)
    result = deepcopy(original)
    replacements = revision["field_replacements"]
    paths = [json.dumps(row["path"], separators=(",", ":")) for row in replacements]
    _require(len(paths) == len(set(paths)), "duplicate bounded wording revision path")
    for row in replacements:
        path = row["path"]
        _require(_allowed_path(original, path), "wording revision path is not allowed")
        current = _value_at_path(original, path)
        _require(
            digest(current) == row["original_value_sha256"],
            "bounded wording original value differs",
        )
        _replace_path(result, path, row["revised_value"])
    result = seal(result, "wording_item_subject_sha256")
    _require(
        digest(result) == revision["revised_wording_item_content_sha256"],
        "bounded wording revision result differs",
    )
    require_structural_invariance(original, result)
    return result


def validate_authority(
    authority: dict[str, Any],
    *,
    package: dict[str, Any],
    decision_template: dict[str, Any],
    parity: dict[str, Any],
) -> dict[str, int]:
    verify_seal(authority, "authority_subject_sha256", "public wording authority")
    _require(
        authority["accepted"] is True
        and authority["immutable"] is True
        and authority["canonical_reviewed_wording_authority"] is True
        and authority["public"] is False
        and authority["production_selectable"] is False,
        "public wording authority state differs",
    )
    subject = authority["subject"]
    _require(
        isinstance(subject.get("reviewer"), str)
        and bool(subject["reviewer"].strip())
        and isinstance(subject.get("reviewer_authority"), str)
        and bool(subject["reviewer_authority"].strip()),
        "public wording reviewer identity or authority is absent",
    )
    _require(
        not any(subject["downstream_authorizations"].values()),
        "downstream authority leakage",
    )
    _require(
        subject["candidate_binding"]["artifact_id"] == package["artifact_id"]
        and subject["candidate_binding"]["package_subject_sha256"]
        == package["public_wording_candidate_package_subject_sha256"]
        and subject["decision_template_binding"]["artifact_id"]
        == decision_template["artifact_id"]
        and subject["decision_template_binding"]["decision_template_subject_sha256"]
        == decision_template["decision_template_subject_sha256"]
        and subject["parity_binding"]["artifact_id"] == parity["artifact_id"]
        and subject["parity_binding"]["parity_subject_sha256"]
        == parity["parity_subject_sha256"],
        "public wording candidate binding differs",
    )
    bindings = upstream_binding_names(package["subject"])
    _require(
        upstream_binding_names(subject) == bindings, "authority binding style differs"
    )
    for binding in bindings:
        expected = package["subject"][binding]
        actual = subject[binding]
        _require(
            all(actual.get(key) == value for key, value in expected.items())
            and isinstance(actual.get("file_sha256"), str)
            and len(actual["file_sha256"]) == 64,
            f"{binding} upstream binding differs",
        )
    candidates = {row["wording_item_id"]: row for row in _items(package)}
    _require(len(candidates) == len(_items(package)), "duplicate wording candidate")
    decisions = subject["wording_decisions"]
    _require(
        len(decisions) == len(candidates)
        and {row["wording_item_id"] for row in decisions} == set(candidates),
        "wording decision set differs",
    )
    for decision in decisions:
        verify_seal(
            decision,
            "decision_subject_sha256",
            f"wording decision {decision['wording_item_id']}",
        )
        original = candidates[decision["wording_item_id"]]
        _require(
            decision["decision"] in ALLOWED_DECISIONS
            and decision.get("reviewer") == subject["reviewer"]
            and decision.get("reviewer_authority") == subject["reviewer_authority"]
            and decision["original_wording_item_subject_sha256"]
            == original["wording_item_subject_sha256"]
            and decision["original_wording_item_content_sha256"] == digest(original),
            "original wording decision binding differs",
        )
        revision = decision["bounded_revision"]
        _require(
            not (
                decision["decision"] == "accept_candidate_as_written"
                and revision is not None
            ),
            "accepted-as-written wording has revision",
        )
        _require(
            not (
                decision["decision"] == "accept_with_bounded_revision"
                and revision is None
            ),
            "bounded wording revision is absent",
        )
        apply_bounded_revision(original, revision)
    counts = Counter(row["decision"] for row in decisions)
    expected = {
        "accept_candidate_as_written": counts["accept_candidate_as_written"],
        "accept_with_bounded_revision": counts["accept_with_bounded_revision"],
        "rejected": 0,
        "unresolved": 0,
    }
    _require(subject["decision_accounting"] == expected, "decision accounting differs")
    _require(
        subject["complete_source_accounting"] == package["subject"]["source_accounting"]
        and subject["complete_synthesis_role_accounting"]
        == package["subject"]["complete_behavioral_synthesis_role_accounting"]
        and subject["blocked_actions"] == package["subject"]["blocked_actions"],
        "complete source or blocked-action accounting differs",
    )
    require_blocked_action_parity(subject, package["subject"])
    return expected


def validate_implementation(
    implementation: dict[str, Any],
    *,
    authority: dict[str, Any],
    package: dict[str, Any],
    decision_template: dict[str, Any],
    parity: dict[str, Any],
) -> dict[str, Any]:
    counts = validate_authority(
        authority,
        package=package,
        decision_template=decision_template,
        parity=parity,
    )
    verify_seal(
        implementation,
        "implementation_subject_sha256",
        "public wording implementation",
    )
    subject = implementation["subject"]
    _require(
        not any(subject["downstream_authorizations"].values())
        and subject["canonical_reviewed_wording_present"] is True
        and subject["production_selectable"] is False
        and subject["public"] is False,
        "wording implementation authority boundary differs",
    )
    _require(
        subject["authority_binding"]["artifact_id"] == authority["artifact_id"]
        and subject["authority_binding"]["authority_subject_sha256"]
        == authority["authority_subject_sha256"],
        "implementation authority binding differs",
    )
    bindings = upstream_binding_names(authority["subject"])
    _require(
        upstream_binding_names(subject) == bindings,
        "implementation binding style differs",
    )
    for binding in ("candidate_binding", *bindings):
        _require(
            subject[binding] == authority["subject"][binding],
            f"implementation {binding} differs",
        )
    candidates = {row["wording_item_id"]: row for row in _items(package)}
    decisions = {
        row["wording_item_id"]: row for row in authority["subject"]["wording_decisions"]
    }
    records = subject["implementation_records"]
    record_ids = [row["wording_item_id"] for row in records]
    _require(
        len(records) == len(candidates)
        and len(record_ids) == len(set(record_ids))
        and set(record_ids) == set(candidates),
        "canonical reviewed wording record set differs",
    )
    for record in records:
        verify_seal(
            record,
            "record_subject_sha256",
            f"wording implementation {record['wording_item_id']}",
        )
        original = candidates[record["wording_item_id"]]
        decision = decisions[record["wording_item_id"]]
        expected = apply_bounded_revision(original, decision["bounded_revision"])
        _require(
            record["original_candidate_content"] == original
            and record["original_candidate_content_sha256"] == digest(original)
            and record["original_candidate_subject_sha256"]
            == original["wording_item_subject_sha256"]
            and record["implemented_reviewed_wording"] == expected
            and record["implemented_reviewed_wording_sha256"] == digest(expected)
            and record["decision"] == decision["decision"]
            and record["bounded_revision"] == decision["bounded_revision"]
            and record["authority_decision_subject_sha256"]
            == decision["decision_subject_sha256"]
            and record["canonical_reviewed_wording"] is True
            and record["public"] is False
            and record["production_selectable"] is False
            and not any(record["downstream_authorizations"].values()),
            "implemented reviewed wording differs from decision",
        )
        require_structural_invariance(original, expected)
        if decision["decision"] == "accept_candidate_as_written":
            _require(expected == original, "accepted-as-written wording changed")
    surfaces = Counter(
        row["implemented_reviewed_wording"]["surface"] for row in records
    )
    expected_surfaces = dict(Counter(row["surface"] for row in candidates.values()))
    _require(
        dict(surfaces) == expected_surfaces,
        "reviewed wording surface accounting differs",
    )
    _require(
        subject["complete_source_accounting"] == package["subject"]["source_accounting"]
        and subject["complete_synthesis_role_accounting"]
        == package["subject"]["complete_behavioral_synthesis_role_accounting"]
        and subject["blocked_actions"] == package["subject"]["blocked_actions"],
        "implementation source or blocked-action accounting differs",
    )
    require_blocked_action_parity(subject, package["subject"])
    final = {
        "canonical_reviewed_wording_count": len(records),
        "surface_accounting": expected_surfaces,
        "decision_accounting": counts,
    }
    _require(subject["final_accounting"] == final, "final wording accounting differs")
    return final
