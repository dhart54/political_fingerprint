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


class EditorialPresentationError(ValueError):
    """Raised when wording or controls do not preserve compiled meaning."""


def _semantic_digest(compiled: dict[str, Any]) -> str:
    encoded = json.dumps(
        compiled,
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


def _member(compiled_ir: dict[str, Any], member_id: str) -> dict[str, Any]:
    matches = [
        member for member in compiled_ir.get("members", [])
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
        raise EditorialPresentationError("compiled proposition identities are not unique")
    return result


def _semantic_tier(
    member: dict[str, Any],
    propositions: dict[str, dict[str, Any]],
    source_constraints: list[dict[str, Any]],
) -> str:
    coverage = member["coverage"]
    if (
        member["review_route"] == "blocked"
        or coverage["missing_evidence_actions"]
        or coverage["unresolved_service_actions"]
        or any(
            item.get("semantic_effect") == "blocks_behavioral_propositions"
            for item in source_constraints
        )
    ):
        return "receipts_only"

    plan = member["composition"]["conclusion_plan"]
    primary = [
        propositions[proposition_id]
        for proposition_id in plan["primary_proposition_ids"]
    ]
    if not primary:
        if (
            coverage["present_actions"]
            or coverage["not_voting_actions"]
            or coverage["directional_yes_no_positions"] == 0
            or member["composition"]["coverage_boundaries"]
        ):
            return "non_directional_or_limited_evidence"
        return "receipts_only"

    has_repeated_pattern = any(
        item["semantic_role"] == "behavioral"
        and item["proposition_type"] == "repeated_pattern"
        for item in primary
    )
    has_conclusion_synthesis = any(
        item["semantic_role"] == "synthesis"
        and item["proposition_type"] in {
            "mechanism_divide",
            "uniform_direction",
            "no_common_throughline",
        }
        for item in primary
    )
    if has_repeated_pattern and has_conclusion_synthesis:
        return "reviewed_conclusion"
    return "developing_read"


def _publication_gates_pass(controls: dict[str, Any]) -> bool:
    receipt = controls["review_receipt"]
    approvals = receipt.get("approvals", {})
    return bool(
        controls["semantic"]["status"] == "accepted_semantic_reference"
        and controls["semantic"]["validation_status"] == "passed"
        and controls["editorial"]["human_approval_status"] == "human_approved"
        and receipt.get("status") == "approved"
        and REQUIRED_RECEIPT_APPROVALS <= {
            key for key, value in approvals.items() if value is True
        }
        and controls["benchmark"]["status"] == "promoted"
        and controls["production"]["eligible"] is True
        and controls["publication"]["active"] is True
    )


def _copy_display_wording(
    wording: dict[str, Any],
    *,
    semantic_tier: str,
) -> dict[str, Any]:
    tier_wording = wording["tier_display"][semantic_tier]
    return {
        "tier": semantic_tier,
        "tier_badge": tier_wording["badge"],
        "teaser": tier_wording["teaser"],
        "coverage_text": wording["coverage_text"],
        "scope_boundary": wording["scope_boundary"],
        "conclusion": copy.deepcopy(wording.get("conclusion")),
        "repeated_patterns": copy.deepcopy(wording.get("repeated_patterns", [])),
        "policy_trajectories": copy.deepcopy(
            wording.get("policy_trajectories", [])
        ),
        "limitations": copy.deepcopy(wording.get("limitations", [])),
    }


def _fallback_display() -> dict[str, Any]:
    return {
        "tier": "receipts_only",
        "tier_badge": "Vote receipts",
        "teaser": "Reviewed analytical wording is not published for this record scope.",
        "coverage_text": None,
        "scope_boundary": None,
        "conclusion": None,
        "repeated_patterns": [],
        "policy_trajectories": [],
        "limitations": [],
    }


def _validate_wording_matches_plan(
    wording: dict[str, Any],
    member: dict[str, Any],
    propositions: dict[str, dict[str, Any]],
) -> None:
    plan = member["composition"]["conclusion_plan"]
    planned = set(plan["primary_proposition_ids"]) | set(
        plan["limiting_proposition_ids"]
    )
    mapped_records = (
        list(wording.get("repeated_patterns", []))
        + list(wording.get("policy_trajectories", []))
        + [
            item
            for item in wording.get("limitations", [])
            if item.get("proposition_id")
        ]
    )
    mapped_ids = [item["proposition_id"] for item in mapped_records]
    if len(mapped_ids) != len(set(mapped_ids)):
        raise EditorialPresentationError(
            "editorial wording maps a proposition more than once"
        )
    conclusion = wording.get("conclusion")
    conclusion_ids = set(conclusion.get("proposition_ids", [])) if conclusion else set()
    if conclusion_ids != set(plan["primary_proposition_ids"]):
        raise EditorialPresentationError(
            "conclusion wording must map to every primary proposition identity"
        )
    if set(mapped_ids) != planned - {
        proposition_id
        for proposition_id in conclusion_ids
        if propositions[proposition_id]["semantic_role"] == "synthesis"
    }:
        raise EditorialPresentationError(
            "section wording must map every planned behavioral or limiting proposition"
        )
    for item in mapped_records:
        proposition = propositions.get(item["proposition_id"])
        if proposition is None:
            raise EditorialPresentationError("wording references unknown proposition")
        if set(item["action_ids"]) != set(proposition["evidence_action_ids"]):
            raise EditorialPresentationError(
                "wording action IDs must exactly match compiled proposition evidence"
            )


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
    all_plan_ids = (
        list(plan["primary_proposition_ids"])
        + list(plan["limiting_proposition_ids"])
    )
    if not set(all_plan_ids) <= set(propositions):
        raise EditorialPresentationError("compiled conclusion plan is unresolved")

    wording = editorial_input["editorial_wording"]
    _validate_wording_matches_plan(wording, member, propositions)
    controls = copy.deepcopy(editorial_input["controls"])
    semantic_tier = _semantic_tier(
        member,
        propositions,
        snapshot.get("source_render_constraints", []),
    )
    public_tier = (
        semantic_tier
        if semantic_tier in ANALYTICAL_TIERS and _publication_gates_pass(controls)
        else "receipts_only"
    )

    planned_propositions = [
        copy.deepcopy(propositions[proposition_id])
        for proposition_id in all_plan_ids
    ]
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
    provenance = copy.deepcopy(editorial_input["provenance"])
    provenance["compiled_ir_sha256"] = _semantic_digest(snapshot)
    provenance["review_receipt"] = copy.deepcopy(controls["review_receipt"])

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
            "review_route": member["review_route"],
        },
        "editorial_wording": copy.deepcopy(wording),
        "frontend_display": (
            _copy_display_wording(wording, semantic_tier=semantic_tier)
            if public_tier != "receipts_only"
            else _fallback_display()
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
            "publication_gates_passed": _publication_gates_pass(controls),
        },
    }
    if _semantic_digest(snapshot) != provenance["compiled_ir_sha256"]:
        raise RuntimeError("presentation compilation mutated compiled Semantic IR")
    return artifact
