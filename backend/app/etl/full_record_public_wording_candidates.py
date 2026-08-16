"""Generic detached public-wording candidate contract for accepted semantics."""

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
DIRECTION_DISPLAY = {
    "support": {"label": "Support", "symbol": "+"},
    "opposition": {"label": "Opposition", "symbol": "−"},
    "mixed": {"label": "Mixed", "symbol": "±"},
}
BEHAVIORAL_SURFACES = {
    "repeated_pattern": "repeated_pattern",
    "trajectory": "trajectory",
    "notable_choice": "notable_choice",
}


class PublicWordingCandidateError(ValueError):
    """Raised when wording candidates exceed accepted semantic authority."""


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
        raise PublicWordingCandidateError(f"{label}: {field} differs")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicWordingCandidateError(message)


def _behavioral_sources(implementation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = implementation["subject"]["implementation_records"]
    result = {row["proposition_id"]: row for row in rows}
    _require(len(result) == len(rows), "duplicate behavioral semantic source")
    for row in rows:
        _require(
            row["canonical_internal_behavioral_semantic_ir"] is True
            and row["public"] is False
            and row["production_selectable"] is False,
            "behavioral source is not accepted canonical internal semantics",
        )
    return result


def _synthesis_sources(implementation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = implementation["subject"]["implementation_records"]
    result = {row["synthesis_candidate_id"]: row for row in rows}
    _require(len(result) == len(rows), "duplicate synthesis semantic source")
    for row in rows:
        _require(
            row["canonical_internal_synthesis"] is True
            and row["public"] is False
            and row["production_selectable"] is False,
            "synthesis source is not accepted canonical internal semantics",
        )
    return result


def _source_binding(kind: str, source_id: str, row: dict[str, Any]) -> dict[str, Any]:
    if kind == "behavioral":
        content = row["accepted_candidate_content"]
        return {
            "source_kind": kind,
            "source_id": source_id,
            "implementation_record_id": row["record_id"],
            "implementation_record_subject_sha256": row["record_subject_sha256"],
            "accepted_semantic_content_sha256": row[
                "accepted_candidate_content_sha256"
            ],
            "semantic_role": "behavioral",
            "semantic_type": content["proposition_type"],
            "source_direction": content["direction"],
            "proposition": content["proposition"],
            "evidence_episode_ids": deepcopy(content["evidence_episode_ids"]),
            "evidence_action_ids": deepcopy(content["evidence_action_ids"]),
            "material_limitations": deepcopy(content["material_limitations"]),
            "relationship_roles": None,
        }
    content = row["implemented_synthesis_content"]
    return {
        "source_kind": kind,
        "source_id": source_id,
        "implementation_record_id": row["record_id"],
        "implementation_record_subject_sha256": row["record_subject_sha256"],
        "accepted_semantic_content_sha256": row["implemented_synthesis_content_sha256"],
        "semantic_role": "synthesis",
        "semantic_type": content["synthesis_type"],
        "source_direction": content["direction"],
        "proposition": content["proposition"],
        "evidence_episode_ids": deepcopy(
            row["underlying_evidence"]["unique_episode_ids"]
        ),
        "evidence_action_ids": deepcopy(
            row["underlying_evidence"]["unique_action_ids"]
        ),
        "material_limitations": deepcopy(content["material_limitations"]),
        "relationship_roles": [
            {
                "proposition_id": binding["proposition_id"],
                "relationship_role": binding["relationship_role"],
            }
            for binding in content["input_bindings"]
        ],
    }


def _compile_item(
    definition: dict[str, Any],
    behavioral: dict[str, dict[str, Any]],
    synthesis: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    bindings = []
    for ref in definition["semantic_sources"]:
        source_id = ref["source_id"]
        rows = behavioral if ref["source_kind"] == "behavioral" else synthesis
        _require(source_id in rows, "unknown or unaccepted semantic source")
        bindings.append(_source_binding(ref["source_kind"], source_id, rows[source_id]))

    source_limitations = {
        (binding["source_kind"], binding["source_id"], limitation)
        for binding in bindings
        for limitation in binding["material_limitations"]
    }
    treatments = definition["limitation_treatments"]
    treatment_keys = {
        (row["source_kind"], row["source_id"], row["source_limitation"])
        for row in treatments
    }
    _require(
        len(treatment_keys) == len(treatments) and treatment_keys == source_limitations,
        "source limitation accounting is incomplete or duplicated",
    )
    for treatment in treatments:
        if treatment["treatment"] == "retained_public_copy":
            _require(
                bool(treatment.get("public_copy")), "retained limitation has no copy"
            )
        else:
            _require(
                treatment["treatment"] == "compressed_or_omitted"
                and bool(treatment.get("reason")),
                "compressed limitation has no explicit reason",
            )

    display = definition["direction_display"]
    if display is not None:
        _require(
            display in DIRECTION_DISPLAY.values(), "direction display contract differs"
        )
    guard = definition["semantic_guard"]
    _require(
        guard["statement_basis"] == "accepted_semantic_proposition_content"
        and guard["raw_yea_nay_maps_to_direction"] is False
        and guard["direction_metadata_alone_establishes_public_meaning"] is False,
        "wording semantic guard differs",
    )
    item = {
        **deepcopy(definition),
        "semantic_source_bindings": bindings,
        "candidate_state": "pending_human_substantive_wording_review",
        "accepted": False,
        "canonical_public_copy": False,
        "authorizing": False,
        "production_selectable": False,
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    item.pop("semantic_sources")
    return seal(item, "wording_item_subject_sha256")


def compile_public_wording_candidate_package(
    *,
    behavioral_authority: dict[str, Any],
    behavioral_implementation: dict[str, Any],
    synthesis_authority: dict[str, Any],
    synthesis_implementation: dict[str, Any],
    wording_definitions: list[dict[str, Any]],
    subject: dict[str, Any],
    legacy_binding_names: bool = True,
) -> dict[str, Any]:
    """Compile deterministic wording candidates from accepted internal semantics."""

    behavioral = _behavioral_sources(behavioral_implementation)
    synthesis = _synthesis_sources(synthesis_implementation)
    items = [
        _compile_item(definition, behavioral, synthesis)
        for definition in wording_definitions
    ]
    _require(
        len({row["wording_item_id"] for row in items}) == len(items),
        "duplicate wording item",
    )
    primary_behavioral = [
        binding["source_id"]
        for item in items
        if item["surface"] in BEHAVIORAL_SURFACES
        for binding in item["semantic_source_bindings"]
        if binding["source_kind"] == "behavioral"
    ]
    primary_synthesis = [
        binding["source_id"]
        for item in items
        if item["surface"] == "synthesis"
        for binding in item["semantic_source_bindings"]
        if binding["source_kind"] == "synthesis"
    ]
    _require(
        Counter(primary_behavioral) == Counter({key: 1 for key in behavioral}),
        "behavioral source primary wording accounting differs",
    )
    _require(
        Counter(primary_synthesis) == Counter({key: 1 for key in synthesis}),
        "synthesis source primary wording accounting differs",
    )
    for item in items:
        if item["surface"] in BEHAVIORAL_SURFACES:
            binding = item["semantic_source_bindings"]
            _require(len(binding) == 1, "behavioral wording has multiple sources")
            _require(
                binding[0]["semantic_type"] == BEHAVIORAL_SURFACES[item["surface"]],
                "behavioral semantic role changed on wording surface",
            )

    legacy_blocked_boundary = "blocked_action_boundary" in subject
    generic_blocked_boundaries = "blocked_action_boundaries" in subject
    _require(
        legacy_blocked_boundary != generic_blocked_boundaries,
        "provide exactly one blocked-action boundary vocabulary",
    )
    boundary_rows = (
        [subject["blocked_action_boundary"]]
        if legacy_blocked_boundary
        else subject["blocked_action_boundaries"]
    )
    _require(
        len(boundary_rows)
        == len(behavioral_implementation["subject"]["blocked_actions"])
        and len({row["action_id"] for row in boundary_rows}) == len(boundary_rows)
        and {row["action_id"] for row in boundary_rows}
        == {
            row["action_id"]
            for row in behavioral_implementation["subject"]["blocked_actions"]
        },
        "blocked-action public boundary differs from accepted semantics",
    )
    semantic_bindings = (
        {
            "m11h_authority_binding": {
                "artifact_id": behavioral_authority["artifact_id"],
                "authority_subject_sha256": behavioral_authority[
                    "authority_subject_sha256"
                ],
            },
            "m11h_implementation_binding": {
                "artifact_id": behavioral_implementation["artifact_id"],
                "implementation_subject_sha256": behavioral_implementation[
                    "implementation_subject_sha256"
                ],
            },
            "m11j_authority_binding": {
                "artifact_id": synthesis_authority["artifact_id"],
                "authority_subject_sha256": synthesis_authority[
                    "authority_subject_sha256"
                ],
            },
            "m11j_implementation_binding": {
                "artifact_id": synthesis_implementation["artifact_id"],
                "implementation_subject_sha256": synthesis_implementation[
                    "implementation_subject_sha256"
                ],
            },
        }
        if legacy_binding_names
        else {
            "behavioral_semantic_ir_authority_binding": {
                "artifact_id": behavioral_authority["artifact_id"],
                "authority_subject_sha256": behavioral_authority[
                    "authority_subject_sha256"
                ],
            },
            "behavioral_semantic_ir_implementation_binding": {
                "artifact_id": behavioral_implementation["artifact_id"],
                "implementation_subject_sha256": behavioral_implementation[
                    "implementation_subject_sha256"
                ],
            },
            "synthesis_authority_binding": {
                "artifact_id": synthesis_authority["artifact_id"],
                "authority_subject_sha256": synthesis_authority[
                    "authority_subject_sha256"
                ],
            },
            "synthesis_implementation_binding": {
                "artifact_id": synthesis_implementation["artifact_id"],
                "implementation_subject_sha256": synthesis_implementation[
                    "implementation_subject_sha256"
                ],
            },
        }
    )

    package = {
        "schema_version": "full_record_public_wording_candidates_v1",
        "artifact_id": subject["artifact_id"],
        "subject": {
            **deepcopy(subject),
            **semantic_bindings,
            "wording_definitions": deepcopy(wording_definitions),
            "wording_items": items,
            "wording_item_accounting": dict(Counter(row["surface"] for row in items)),
            "complete_behavioral_synthesis_role_accounting": deepcopy(
                synthesis_authority["subject"]["accepted_proposition_role_accounting"]
            ),
            "blocked_actions": deepcopy(
                behavioral_implementation["subject"]["blocked_actions"]
            ),
            "source_accounting": {
                "behavioral_proposition_count": len(behavioral),
                "synthesis_record_count": len(synthesis),
                "behavioral_primary_wording_count": len(primary_behavioral),
                "synthesis_primary_wording_count": len(primary_synthesis),
            },
            "candidate_state": "complete_pending_human_substantive_wording_review",
            "accepted": False,
            "canonical_public_copy": False,
            "authorizing": False,
            "production_selectable": False,
            "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
        },
        "public": False,
        "production_selectable": False,
    }
    return seal(package, "public_wording_candidate_package_subject_sha256")


def validate_public_wording_candidate_package(
    package: dict[str, Any],
    *,
    behavioral_authority: dict[str, Any],
    behavioral_implementation: dict[str, Any],
    synthesis_authority: dict[str, Any],
    synthesis_implementation: dict[str, Any],
) -> dict[str, Any]:
    """Rebuild and compare the package independently from embedded definitions."""

    verify_seal(
        package,
        "public_wording_candidate_package_subject_sha256",
        "public wording candidate package",
    )
    subject = package["subject"]
    _require(
        package["public"] is False
        and package["production_selectable"] is False
        and subject["accepted"] is False
        and subject["canonical_public_copy"] is False
        and subject["authorizing"] is False
        and not any(subject["downstream_authorizations"].values()),
        "public wording candidate crossed authority boundary",
    )
    excluded = {
        "m11h_authority_binding",
        "m11h_implementation_binding",
        "m11j_authority_binding",
        "m11j_implementation_binding",
        "behavioral_semantic_ir_authority_binding",
        "behavioral_semantic_ir_implementation_binding",
        "synthesis_authority_binding",
        "synthesis_implementation_binding",
        "wording_definitions",
        "wording_items",
        "wording_item_accounting",
        "complete_behavioral_synthesis_role_accounting",
        "blocked_actions",
        "source_accounting",
        "candidate_state",
        "accepted",
        "canonical_public_copy",
        "authorizing",
        "production_selectable",
        "downstream_authorizations",
    }
    rebuilt_subject = {
        key: deepcopy(value) for key, value in subject.items() if key not in excluded
    }
    legacy_binding_names = "m11h_authority_binding" in subject
    generic_binding_names = "behavioral_semantic_ir_authority_binding" in subject
    _require(
        legacy_binding_names != generic_binding_names
        and (
            {
                "m11h_implementation_binding",
                "m11j_authority_binding",
                "m11j_implementation_binding",
            }.issubset(subject)
            if legacy_binding_names
            else {
                "behavioral_semantic_ir_implementation_binding",
                "synthesis_authority_binding",
                "synthesis_implementation_binding",
            }.issubset(subject)
        ),
        "provide exactly one public-wording semantic binding vocabulary",
    )
    expected = compile_public_wording_candidate_package(
        behavioral_authority=behavioral_authority,
        behavioral_implementation=behavioral_implementation,
        synthesis_authority=synthesis_authority,
        synthesis_implementation=synthesis_implementation,
        wording_definitions=subject["wording_definitions"],
        subject=rebuilt_subject,
        legacy_binding_names=legacy_binding_names,
    )
    _require(package == expected, "public wording deterministic rebuild differs")
    return {
        "artifact_id": package["artifact_id"],
        "wording_item_count": len(subject["wording_items"]),
        "wording_item_accounting": subject["wording_item_accounting"],
        "source_accounting": subject["source_accounting"],
        "status": "valid",
    }
