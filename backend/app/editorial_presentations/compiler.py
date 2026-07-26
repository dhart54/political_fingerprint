"""Deterministic compiler from compiled Semantic IR to a gated public artifact."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

PUBLIC_TIERS = {
    "reviewed_conclusion",
    "developing_read",
    "non_directional_or_limited_evidence",
    "receipts_only",
}
REQUIRED_RECEIPT_APPROVALS = {
    "bounded_issue_conclusion",
    "repeated_pattern_statements",
    "fentanyl_limitation",
    "claim_source_mappings",
    "benchmark_promotion",
    "production_eligibility",
}
ANALYTICAL_TIERS = PUBLIC_TIERS - {"receipts_only"}
BENCHMARK_STATUSES = {"not_promoted", "gold_benchmark"}


class EditorialPresentationError(ValueError):
    """Raised when wording or controls do not preserve compiled meaning."""


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def artifact_bytes(artifact: dict[str, Any]) -> bytes:
    """Return canonical UTF-8 bytes for an immutable artifact."""

    return json.dumps(
        artifact,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def artifact_digest(artifact: dict[str, Any]) -> str:
    return hashlib.sha256(artifact_bytes(artifact)).hexdigest()


def reviewed_wording_digest(wording: dict[str, Any]) -> str:
    return canonical_digest(wording)


def _member(compiled_ir: dict[str, Any], member_id: str) -> dict[str, Any]:
    matches = [
        member
        for member in compiled_ir.get("members", [])
        if member.get("member_id") == member_id
    ]
    if len(matches) != 1:
        raise EditorialPresentationError(
            "compiled IR must contain exactly one requested member"
        )
    return matches[0]


def _proposition_index(member: dict[str, Any]) -> dict[str, dict[str, Any]]:
    propositions = member["proposition_graph"]["propositions"]
    result = {item["proposition_id"]: item for item in propositions}
    if len(result) != len(propositions):
        raise EditorialPresentationError(
            "compiled proposition identities are not unique"
        )
    return result


def _semantic_tier_from_parts(
    *,
    coverage: dict[str, Any],
    primary_propositions: list[dict[str, Any]],
    review_route: str,
    source_constraints: list[dict[str, Any]],
    coverage_boundaries: list[dict[str, Any]],
) -> str:
    if (
        review_route == "blocked"
        or coverage["missing_evidence_actions"]
        or coverage["unresolved_service_actions"]
        or any(
            item.get("semantic_effect") == "blocks_behavioral_propositions"
            for item in source_constraints
        )
    ):
        return "receipts_only"

    if not primary_propositions:
        if (
            coverage["present_actions"]
            or coverage["not_voting_actions"]
            or coverage["directional_yes_no_positions"] == 0
            or coverage_boundaries
        ):
            return "non_directional_or_limited_evidence"
        return "receipts_only"

    has_repeated_pattern = any(
        item["semantic_role"] == "behavioral"
        and item["proposition_type"] == "repeated_pattern"
        for item in primary_propositions
    )
    has_conclusion_synthesis = any(
        item["semantic_role"] == "synthesis"
        and item["proposition_type"]
        in {"mechanism_divide", "uniform_direction", "no_common_throughline"}
        for item in primary_propositions
    )
    if has_repeated_pattern and has_conclusion_synthesis:
        return "reviewed_conclusion"
    return "developing_read"


def semantic_tier_for_artifact(artifact: dict[str, Any]) -> str:
    meaning = artifact["compiled_semantic_meaning"]
    propositions = {
        item["proposition_id"]: item for item in meaning["propositions"]
    }
    return _semantic_tier_from_parts(
        coverage=artifact["evidence_metadata"]["coverage"],
        primary_propositions=[
            propositions[item] for item in meaning["primary_proposition_ids"]
        ],
        review_route=meaning["review_route"],
        source_constraints=meaning["source_render_constraints"],
        coverage_boundaries=meaning["coverage_boundaries"],
    )


def _presentation_boundaries(
    identity: dict[str, Any],
    member: dict[str, Any],
    propositions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    action_ids = sorted(
        {
            action_id
            for proposition in propositions
            for action_id in proposition["evidence_action_ids"]
        }
    )
    episode_ids = sorted(
        {
            episode_id
            for proposition in propositions
            for episode_id in proposition["evidence_episode_ids"]
        }
    )
    suffix = (
        f"{identity['member_id']}:{identity['issue_id']}:{identity['scope']}"
    ).lower()
    boundaries = [
        {
            "boundary_id": f"boundary:coverage:{suffix}",
            "boundary_type": "reviewed_evidence_coverage",
            "presentation_target": "coverage_note",
            "action_ids": action_ids,
            "episode_ids": episode_ids,
        },
        {
            "boundary_id": f"boundary:scope:{suffix}",
            "boundary_type": "reviewed_congress_scope",
            "presentation_target": "scope_note",
            "action_ids": action_ids,
            "episode_ids": episode_ids,
        },
    ]
    boundaries.extend(copy.deepcopy(member["composition"]["coverage_boundaries"]))
    boundaries.extend(copy.deepcopy(member["composition"]["method_boundaries"]))
    return boundaries


def source_constraint_boundaries(
    constraints: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "boundary_id": item["constraint_id"],
            "boundary_type": item["constraint_type"],
            "presentation_target": item["presentation_target"],
            "action_ids": copy.deepcopy(item.get("action_ids", [])),
            "episode_ids": copy.deepcopy(item.get("episode_ids", [])),
        }
        for item in constraints
    ]


def _mapping_ids(wording: dict[str, Any]) -> list[str]:
    result: list[str] = []

    def collect(record: Any) -> None:
        if isinstance(record, dict):
            mapping = record.get("mapping")
            if isinstance(mapping, dict) and isinstance(
                mapping.get("mapping_id"), str
            ):
                result.append(mapping["mapping_id"])
            for value in record.values():
                collect(value)
        elif isinstance(record, list):
            for value in record:
                collect(value)

    collect(wording)
    return sorted(result)


def _validate_analytical_text(
    record: dict[str, Any],
    *,
    allowed_targets: set[str],
    propositions: dict[str, dict[str, Any]],
    boundaries: dict[str, dict[str, Any]],
    source_refs: set[str],
    receipt_refs: set[str],
) -> None:
    if set(record) != {"text", "mapping"} or not isinstance(
        record["text"], str
    ) or not record["text"].strip():
        raise EditorialPresentationError(
            "analytical wording must contain text and an explicit mapping"
        )
    mapping = record["mapping"]
    required = {
        "mapping_id",
        "proposition_ids",
        "boundary_ids",
        "presentation_target",
        "action_ids",
        "episode_ids",
        "source_refs",
        "receipt_refs",
    }
    if set(mapping) != required or not mapping["mapping_id"]:
        raise EditorialPresentationError(
            "analytical wording mapping is incomplete"
        )
    proposition_ids = set(mapping["proposition_ids"])
    boundary_ids = set(mapping["boundary_ids"])
    if bool(proposition_ids) == bool(boundary_ids):
        raise EditorialPresentationError(
            "analytical wording must map to propositions or typed boundaries"
        )
    unknown_propositions = proposition_ids - set(propositions)
    unknown_boundaries = boundary_ids - set(boundaries)
    if unknown_propositions or unknown_boundaries:
        raise EditorialPresentationError(
            "analytical wording references an unknown proposition or boundary"
        )
    referenced = [
        *(propositions[item] for item in proposition_ids),
        *(boundaries[item] for item in boundary_ids),
    ]
    targets = {item["presentation_target"] for item in referenced}
    if (
        mapping["presentation_target"] not in allowed_targets
        or targets != {mapping["presentation_target"]}
    ):
        raise EditorialPresentationError(
            "analytical wording is mapped to the wrong presentation section"
        )
    expected_actions = {
        action_id
        for item in referenced
        for action_id in item.get("evidence_action_ids", item.get("action_ids", []))
    }
    expected_episodes = {
        episode_id
        for item in referenced
        for episode_id in item.get(
            "evidence_episode_ids", item.get("episode_ids", [])
        )
    }
    if set(mapping["action_ids"]) != expected_actions:
        raise EditorialPresentationError(
            "wording action IDs must exactly match compiled semantic evidence"
        )
    if set(mapping["episode_ids"]) != expected_episodes:
        raise EditorialPresentationError(
            "wording episode IDs must exactly match compiled semantic evidence"
        )
    if (
        not mapping["source_refs"]
        or not set(mapping["source_refs"]) <= source_refs
        or not mapping["receipt_refs"]
        or not set(mapping["receipt_refs"]) <= receipt_refs
    ):
        raise EditorialPresentationError(
            "analytical wording lacks valid source and receipt references"
        )


def validate_editorial_wording(
    wording: dict[str, Any],
    *,
    primary_ids: list[str],
    limiting_ids: list[str],
    propositions: dict[str, dict[str, Any]],
    boundaries: list[dict[str, Any]],
    provenance: dict[str, Any],
) -> list[str]:
    boundary_index = {item["boundary_id"]: item for item in boundaries}
    if len(boundary_index) != len(boundaries):
        raise EditorialPresentationError("typed boundary identities are not unique")
    source_refs = set(provenance["source_refs"])
    receipt_refs = set(provenance["receipt_refs"])

    def validate(record: dict[str, Any], targets: set[str]) -> None:
        _validate_analytical_text(
            record,
            allowed_targets=targets,
            propositions=propositions,
            boundaries=boundary_index,
            source_refs=source_refs,
            receipt_refs=receipt_refs,
        )

    for tier_wording in wording["tier_display"].values():
        if set(tier_wording) != {"badge", "teaser"} or not isinstance(
            tier_wording["badge"], str
        ):
            raise EditorialPresentationError(
                "tier display must separate a neutral badge from mapped teaser copy"
            )
        validate(
            tier_wording["teaser"],
            {
                "conclusion_only",
                "repeated_patterns",
                "policy_trajectories",
                "other_notable_choices",
                "coverage_note",
            },
        )
    validate(wording["coverage_text"], {"coverage_note"})
    validate(wording["scope_boundary"], {"scope_note"})

    conclusion_ids = {
        proposition_id
        for proposition_id in primary_ids
        if propositions[proposition_id]["presentation_target"] == "conclusion_only"
    }
    conclusion = wording.get("conclusion")
    if conclusion_ids:
        if not conclusion:
            raise EditorialPresentationError(
                "conclusion-only propositions require mapped conclusion wording"
            )
        validate(conclusion["headline"], {"conclusion_only"})
        validate(conclusion["body"], {"conclusion_only"})
        for field in ("headline", "body"):
            if set(conclusion[field]["mapping"]["proposition_ids"]) != conclusion_ids:
                raise EditorialPresentationError(
                    "conclusion wording must map to every conclusion-only proposition"
                )
    elif conclusion is not None:
        raise EditorialPresentationError(
            "conclusion wording is not allowed without a conclusion-only proposition"
        )

    expected_sections = {
        "repeated_patterns": {
            proposition_id
            for proposition_id in [*primary_ids, *limiting_ids]
            if propositions[proposition_id]["presentation_target"]
            == "repeated_patterns"
        },
        "policy_trajectories": {
            proposition_id
            for proposition_id in [*primary_ids, *limiting_ids]
            if propositions[proposition_id]["presentation_target"]
            == "policy_trajectories"
        },
    }
    for section, expected_ids in expected_sections.items():
        records = wording.get(section, [])
        actual_ids: list[str] = []
        for item in records:
            proposition_id = item["proposition_id"]
            actual_ids.append(proposition_id)
            for field in ("heading", "body"):
                validate(item[field], {section})
                if item[field]["mapping"]["proposition_ids"] != [proposition_id]:
                    raise EditorialPresentationError(
                        "section wording must map only its declared proposition"
                    )
        if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != expected_ids:
            raise EditorialPresentationError(
                f"{section} wording must map every proposition in its section"
            )

    for limitation in wording.get("limitations", []):
        for field in ("heading", "body"):
            validate(
                limitation[field],
                {"meaningful_limitations", "source_note", "scope_note"},
            )

    mapping_ids = _mapping_ids(wording)
    if len(mapping_ids) != len(set(mapping_ids)):
        raise EditorialPresentationError(
            "every analytical display field requires a unique mapping identity"
        )
    return mapping_ids


def expected_review_binding(
    *,
    identity: dict[str, Any],
    compiled_ir_sha256: str,
    wording: dict[str, Any],
    mapping_ids: list[str],
) -> dict[str, Any]:
    return {
        "artifact_id": identity["artifact_id"],
        "artifact_version": identity["artifact_version"],
        "compiled_ir_sha256": compiled_ir_sha256,
        "reviewed_wording_sha256": reviewed_wording_digest(wording),
        "mapping_ids": sorted(mapping_ids),
        "approved_scope": identity["scope"],
    }


def publication_gates_pass(
    controls: dict[str, Any],
    *,
    expected_binding: dict[str, Any],
) -> bool:
    receipt = controls["review_receipt"]
    approvals = receipt.get("approvals", {})
    reviewer = receipt.get("reviewer", {})
    if controls["benchmark"]["status"] not in BENCHMARK_STATUSES:
        return False
    return bool(
        controls["semantic"]["status"] == "accepted_semantic_reference"
        and controls["semantic"]["validation_status"] == "passed"
        and controls["editorial"]["human_approval_status"] == "human_approved"
        and receipt.get("status") == "approved"
        and receipt.get("binding") == expected_binding
        and reviewer.get("reviewer_id")
        and reviewer.get("authority")
        and reviewer.get("reviewer_id") != "not_supplied"
        and reviewer.get("authority") != "not_supplied"
        and REQUIRED_RECEIPT_APPROVALS
        <= {key for key, value in approvals.items() if value is True}
        and controls["benchmark"]["status"] == "gold_benchmark"
        and controls["production"]["eligible"] is True
        and controls["publication"]["active"] is True
    )


def build_review_binding(
    compiled_ir: dict[str, Any],
    editorial_input: dict[str, Any],
) -> dict[str, Any]:
    snapshot = copy.deepcopy(compiled_ir)
    identity = editorial_input["artifact_identity"]
    member = _member(snapshot, identity["member_id"])
    propositions = _proposition_index(member)
    plan = member["composition"]["conclusion_plan"]
    all_plan_ids = [
        *plan["primary_proposition_ids"],
        *plan["limiting_proposition_ids"],
    ]
    planned = [copy.deepcopy(propositions[item]) for item in all_plan_ids]
    boundaries = _presentation_boundaries(identity, member, planned)
    mapping_boundaries = [
        *boundaries,
        *source_constraint_boundaries(
            snapshot.get("source_render_constraints", [])
        ),
    ]
    mapping_ids = validate_editorial_wording(
        editorial_input["editorial_wording"],
        primary_ids=plan["primary_proposition_ids"],
        limiting_ids=plan["limiting_proposition_ids"],
        propositions=propositions,
        boundaries=mapping_boundaries,
        provenance=editorial_input["provenance"],
    )
    return expected_review_binding(
        identity=identity,
        compiled_ir_sha256=canonical_digest(snapshot),
        wording=editorial_input["editorial_wording"],
        mapping_ids=mapping_ids,
    )


def _unwrap(record: dict[str, Any]) -> str:
    return record["text"]


def _copy_display_wording(
    wording: dict[str, Any],
    *,
    semantic_tier: str,
) -> dict[str, Any]:
    tier_wording = wording["tier_display"][semantic_tier]

    def section_item(item: dict[str, Any]) -> dict[str, Any]:
        mapping = item["body"]["mapping"]
        result = {
            "heading": _unwrap(item["heading"]),
            "body": _unwrap(item["body"]),
            "action_ids": copy.deepcopy(mapping["action_ids"]),
        }
        if item.get("proposition_id"):
            result["proposition_id"] = item["proposition_id"]
        if item.get("boundary_id"):
            result["boundary_id"] = item["boundary_id"]
        return result

    conclusion = wording.get("conclusion")
    return {
        "tier": semantic_tier,
        "tier_badge": tier_wording["badge"],
        "teaser": _unwrap(tier_wording["teaser"]),
        "coverage_text": _unwrap(wording["coverage_text"]),
        "scope_boundary": _unwrap(wording["scope_boundary"]),
        "conclusion": (
            {
                "headline": _unwrap(conclusion["headline"]),
                "body": _unwrap(conclusion["body"]),
            }
            if conclusion
            else None
        ),
        "repeated_patterns": [
            section_item(item) for item in wording.get("repeated_patterns", [])
        ],
        "policy_trajectories": [
            section_item(item) for item in wording.get("policy_trajectories", [])
        ],
        "limitations": [
            section_item(item) for item in wording.get("limitations", [])
        ],
    }


def fallback_display() -> dict[str, Any]:
    return {
        "tier": "receipts_only",
        "tier_badge": "Vote receipts",
        "teaser": (
            "Reviewed analytical wording is not published for this record scope."
        ),
        "coverage_text": None,
        "scope_boundary": None,
        "conclusion": None,
        "repeated_patterns": [],
        "policy_trajectories": [],
        "limitations": [],
    }


def compile_public_issue_presentation(
    compiled_ir: dict[str, Any],
    editorial_input: dict[str, Any],
) -> dict[str, Any]:
    """Compile reviewed wording without deriving or rewriting analytical prose."""

    snapshot = copy.deepcopy(compiled_ir)
    identity = editorial_input["artifact_identity"]
    member = _member(snapshot, identity["member_id"])
    propositions = _proposition_index(member)
    plan = member["composition"]["conclusion_plan"]
    all_plan_ids = [
        *plan["primary_proposition_ids"],
        *plan["limiting_proposition_ids"],
    ]
    if not set(all_plan_ids) <= set(propositions):
        raise EditorialPresentationError("compiled conclusion plan is unresolved")

    planned_propositions = [
        copy.deepcopy(propositions[proposition_id])
        for proposition_id in all_plan_ids
    ]
    boundaries = _presentation_boundaries(identity, member, planned_propositions)
    mapping_boundaries = [
        *boundaries,
        *source_constraint_boundaries(
            snapshot.get("source_render_constraints", [])
        ),
    ]
    wording = editorial_input["editorial_wording"]
    provenance_input = editorial_input["provenance"]
    mapping_ids = validate_editorial_wording(
        wording,
        primary_ids=plan["primary_proposition_ids"],
        limiting_ids=plan["limiting_proposition_ids"],
        propositions=propositions,
        boundaries=mapping_boundaries,
        provenance=provenance_input,
    )
    compiled_digest = canonical_digest(snapshot)
    binding = expected_review_binding(
        identity=identity,
        compiled_ir_sha256=compiled_digest,
        wording=wording,
        mapping_ids=mapping_ids,
    )
    controls = copy.deepcopy(editorial_input["controls"])
    semantic_tier = _semantic_tier_from_parts(
        coverage=member["coverage"],
        primary_propositions=[
            propositions[item] for item in plan["primary_proposition_ids"]
        ],
        review_route=member["review_route"],
        source_constraints=snapshot.get("source_render_constraints", []),
        coverage_boundaries=member["composition"]["coverage_boundaries"],
    )
    gates_pass = publication_gates_pass(
        controls,
        expected_binding=binding,
    )
    public_tier = (
        semantic_tier
        if semantic_tier in ANALYTICAL_TIERS and gates_pass
        else "receipts_only"
    )

    action_ids = sorted(
        {
            action_id
            for proposition in planned_propositions
            for action_id in proposition["evidence_action_ids"]
        }
    )
    episode_ids = sorted(
        {
            episode_id
            for proposition in planned_propositions
            for episode_id in proposition["evidence_episode_ids"]
        }
    )
    provenance = copy.deepcopy(provenance_input)
    provenance["compiled_ir_sha256"] = compiled_digest
    provenance["reviewed_wording_sha256"] = reviewed_wording_digest(wording)
    provenance["review_receipt"] = copy.deepcopy(controls["review_receipt"])
    provenance["compiler_receipt"] = copy.deepcopy(binding)

    artifact = {
        "schema_version": "editorial_public_issue_presentation_v1",
        "artifact_identity": copy.deepcopy(identity),
        "compiled_semantic_meaning": {
            "primary_proposition_ids": copy.deepcopy(
                plan["primary_proposition_ids"]
            ),
            "limiting_proposition_ids": copy.deepcopy(
                plan["limiting_proposition_ids"]
            ),
            "propositions": planned_propositions,
            "source_render_constraints": copy.deepcopy(
                snapshot.get("source_render_constraints", [])
            ),
            "coverage_boundaries": copy.deepcopy(
                member["composition"]["coverage_boundaries"]
            ),
            "presentation_boundaries": boundaries,
            "review_route": member["review_route"],
        },
        "editorial_wording": copy.deepcopy(wording),
        "frontend_display": (
            _copy_display_wording(wording, semantic_tier=semantic_tier)
            if public_tier != "receipts_only"
            else fallback_display()
        ),
        "evidence_metadata": {
            "coverage": copy.deepcopy(member["coverage"]),
            "action_ids": action_ids,
            "episode_ids": episode_ids,
            "action_accounting": copy.deepcopy(member["action_accounting"]),
        },
        "provenance": provenance,
        "controls": {
            **controls,
            "derived_semantic_tier": semantic_tier,
            "effective_public_tier": public_tier,
            "publication_gates_passed": gates_pass,
        },
    }
    if canonical_digest(snapshot) != compiled_digest:
        raise RuntimeError("presentation compilation mutated compiled Semantic IR")
    return artifact
