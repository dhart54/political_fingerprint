"""Fail-closed validation for IR-native public presentation artifacts."""

from __future__ import annotations

from typing import Any

from .compiler import (
    ANALYTICAL_TIERS,
    PUBLIC_TIERS,
    REQUIRED_RECEIPT_APPROVALS,
    EditorialPresentationError,
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
    if (
        not isinstance(identity["congress"], int)
        or identity["congress"] <= 0
        or identity["scope"] != str(identity["congress"])
    ):
        raise EditorialPresentationError(
            "the reviewed presentation scope must match its Congress"
        )
    meaning = artifact["compiled_semantic_meaning"]
    proposition_ids = {
        proposition["proposition_id"] for proposition in meaning["propositions"]
    }
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
    if proposition_action_ids != set(evidence["action_ids"]):
        raise EditorialPresentationError(
            "artifact action IDs do not match compiled proposition evidence"
        )
    try:
        evidence_congresses = {
            int(action_id.split(":")[1]) for action_id in evidence["action_ids"]
        }
    except (AttributeError, IndexError, ValueError) as exc:
        raise EditorialPresentationError(
            "artifact evidence contains an invalid canonical action ID"
        ) from exc
    if evidence_congresses != {identity["congress"]}:
        evidence_scope = ", ".join(
            f"{congress}th Congress" for congress in sorted(evidence_congresses)
        )
        raise EditorialPresentationError(
            f"compiled evidence belongs to the {evidence_scope}"
        )
    tier = artifact["frontend_display"]["tier"]
    controls = artifact["controls"]
    if tier not in PUBLIC_TIERS:
        raise EditorialPresentationError("unknown public presentation tier")
    if controls["effective_public_tier"] != tier:
        raise EditorialPresentationError(
            "frontend tier differs from compiler-owned public tier"
        )
    if tier in ANALYTICAL_TIERS:
        if not controls["publication_gates_passed"]:
            raise EditorialPresentationError(
                "analytical display crossed a publication gate"
            )
        approved = {
            key
            for key, value in controls["review_receipt"]["approvals"].items()
            if value is True
        }
        if not REQUIRED_RECEIPT_APPROVALS <= approved:
            raise EditorialPresentationError(
                "analytical display lacks required receipt approvals"
            )
    elif any(
        (
            artifact["frontend_display"]["conclusion"],
            artifact["frontend_display"]["repeated_patterns"],
            artifact["frontend_display"]["policy_trajectories"],
            artifact["frontend_display"]["limitations"],
        )
    ):
        raise EditorialPresentationError(
            "receipts-only display exposed analytical copy"
        )
    return {
        "proposition_count": len(proposition_ids),
        "action_count": len(evidence["action_ids"]),
        "episode_count": len(evidence["episode_ids"]),
    }
