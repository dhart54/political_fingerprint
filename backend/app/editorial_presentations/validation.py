"""Fail-closed validation for IR-native public presentation artifacts."""

from __future__ import annotations

from typing import Any

from .compiler import (
    ANALYTICAL_TIERS,
    BENCHMARK_STATUSES,
    PUBLIC_TIERS,
    IMMUTABLE_PROVENANCE_FIELDS,
    EditorialPresentationError,
    _copy_display_wording,
    approval_subject_for_artifact,
    fallback_display,
    publication_gates_pass,
    mapping_set_digest,
    limitations_digest,
    reviewed_wording_digest,
    semantic_tier_for_artifact,
    source_constraint_boundaries,
    validate_editorial_wording,
)


def validate_public_issue_presentation(
    artifact: dict[str, Any],
) -> dict[str, int]:
    required = {
        "schema_version",
        "artifact_identity",
        "compiled_semantic_meaning",
        "editorial_wording",
        "frontend_display",
        "evidence_metadata",
        "provenance",
        "controls",
    }
    if set(artifact) != required:
        raise EditorialPresentationError(
            "public presentation has unexpected top-level fields"
        )
    if artifact["schema_version"] != "editorial_public_issue_presentation_v1":
        raise EditorialPresentationError("unsupported public presentation schema")

    identity = artifact["artifact_identity"]
    identity_required = {
        "artifact_id",
        "artifact_version",
        "member_id",
        "issue_id",
        "congress",
        "scope",
        "source_case_id",
    }
    if (
        set(identity) != identity_required
        or not isinstance(identity["artifact_id"], str)
        or not identity["artifact_id"]
        or not isinstance(identity["artifact_version"], int)
        or identity["artifact_version"] <= 0
        or not isinstance(identity["member_id"], str)
        or not identity["member_id"]
        or not isinstance(identity["issue_id"], str)
        or not identity["issue_id"]
        or not isinstance(identity["congress"], int)
        or identity["congress"] <= 0
        or identity["scope"] != str(identity["congress"])
    ):
        raise EditorialPresentationError(
            "the immutable artifact identity and reviewed Congress scope are invalid"
        )

    meaning = artifact["compiled_semantic_meaning"]
    proposition_ids = {
        proposition["proposition_id"] for proposition in meaning["propositions"]
    }
    if len(proposition_ids) != len(meaning["propositions"]):
        raise EditorialPresentationError(
            "artifact proposition identities are not unique"
        )
    planned = set(meaning["primary_proposition_ids"]) | set(
        meaning["limiting_proposition_ids"]
    )
    if proposition_ids != planned:
        raise EditorialPresentationError(
            "artifact meaning must contain exactly the conclusion-plan propositions"
        )

    evidence = artifact["evidence_metadata"]
    proposition_action_ids = {
        action_id
        for proposition in meaning["propositions"]
        for action_id in proposition["evidence_action_ids"]
    }
    proposition_episode_ids = {
        episode_id
        for proposition in meaning["propositions"]
        for episode_id in proposition["evidence_episode_ids"]
    }
    if proposition_action_ids != set(evidence["action_ids"]):
        raise EditorialPresentationError(
            "artifact action IDs do not match compiled proposition evidence"
        )
    if proposition_episode_ids != set(evidence["episode_ids"]):
        raise EditorialPresentationError(
            "artifact episode IDs do not match compiled proposition evidence"
        )
    try:
        evidence_congresses = {
            int(action_id.split(":")[1]) for action_id in evidence["action_ids"]
        }
    except (AttributeError, IndexError, ValueError) as exc:
        raise EditorialPresentationError(
            "artifact evidence contains an invalid canonical action ID"
        ) from exc
    if evidence_congresses and evidence_congresses != {identity["congress"]}:
        evidence_scope = ", ".join(
            f"{congress}th Congress" for congress in sorted(evidence_congresses)
        )
        raise EditorialPresentationError(
            f"compiled evidence belongs to the {evidence_scope}"
        )

    propositions = {
        item["proposition_id"]: item for item in meaning["propositions"]
    }
    validate_editorial_wording(
        artifact["editorial_wording"],
        primary_ids=meaning["primary_proposition_ids"],
        limiting_ids=meaning["limiting_proposition_ids"],
        propositions=propositions,
        boundaries=[
            *meaning["presentation_boundaries"],
            *source_constraint_boundaries(
                meaning["source_render_constraints"]
            ),
        ],
        provenance=artifact["provenance"],
    )
    provenance = artifact["provenance"]
    expected_provenance_fields = {
        *IMMUTABLE_PROVENANCE_FIELDS,
        "compiled_ir_sha256",
        "reviewed_wording_sha256",
        "mapping_set_sha256",
        "evidence_provenance_sha256",
        "presentation_content_sha256",
        "limitations_sha256",
        "approval_subject_sha256",
        "compiler_receipt",
    }
    if set(provenance) != expected_provenance_fields:
        raise EditorialPresentationError(
            "provenance must contain exactly the permitted immutable and computed fields"
        )
    if provenance["reviewed_wording_sha256"] != reviewed_wording_digest(
        artifact["editorial_wording"]
    ):
        raise EditorialPresentationError("reviewed wording digest mismatch")
    expected_subject = approval_subject_for_artifact(artifact)
    if provenance["mapping_set_sha256"] != mapping_set_digest(
        artifact["editorial_wording"]
    ):
        raise EditorialPresentationError("mapping-set digest mismatch")
    for field in (
        "evidence_provenance_sha256",
        "presentation_content_sha256",
        "limitations_sha256",
        "approval_subject_sha256",
    ):
        if provenance[field] != expected_subject[field]:
            raise EditorialPresentationError(
                f"{field.replace('_', ' ')} mismatch"
            )
    if provenance["limitations_sha256"] != limitations_digest(
        provenance["review_limitations"]
    ):
        raise EditorialPresentationError("limitations digest mismatch")
    if provenance["compiler_receipt"] != expected_subject:
        raise EditorialPresentationError(
            "compiler receipt identity or digest mismatch"
        )

    controls = artifact["controls"]
    if controls["benchmark"]["status"] not in BENCHMARK_STATUSES:
        raise EditorialPresentationError("unknown benchmark status")
    if controls.get("approval_mode") != "detached_receipt_required":
        raise EditorialPresentationError(
            "public presentation requires detached approval receipts"
        )
    semantic_tier = semantic_tier_for_artifact(artifact)
    gates_pass = publication_gates_pass(
        controls,
        expected_subject=expected_subject,
    )
    effective_tier = (
        semantic_tier
        if semantic_tier in ANALYTICAL_TIERS and gates_pass
        else "receipts_only"
    )
    if controls["derived_semantic_tier"] != semantic_tier:
        raise EditorialPresentationError(
            "stored semantic tier differs from recomputed semantic tier"
        )
    if controls["publication_gates_passed"] is not gates_pass:
        raise EditorialPresentationError(
            "stored publication gate result differs from recomputed controls"
        )
    if controls["effective_public_tier"] != effective_tier:
        raise EditorialPresentationError(
            "stored public tier differs from recomputed public eligibility"
        )

    display = artifact["frontend_display"]
    if display["tier"] not in PUBLIC_TIERS:
        raise EditorialPresentationError("unknown public presentation tier")
    expected_display = (
        _copy_display_wording(
            artifact["editorial_wording"],
            semantic_tier=semantic_tier,
        )
        if effective_tier != "receipts_only"
        else fallback_display()
    )
    if display != expected_display:
        raise EditorialPresentationError(
            "frontend display differs from recomputed gated wording"
        )
    return {
        "proposition_count": len(proposition_ids),
        "action_count": len(evidence["action_ids"]),
        "episode_count": len(evidence["episode_ids"]),
    }
