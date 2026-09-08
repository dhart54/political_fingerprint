"""Apply publication-gated governed receipt projections without erasing raw evidence."""

from __future__ import annotations

import copy
from typing import Any

from .reviewed_record import (
    GovernedReceiptProjectionError,
    index_actions,
    overlay_reviewed_actions,
    union_database_actions,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GovernedReceiptProjectionError(message)


def _normalized_member_action(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def attach_governed_receipt_projections(
    evidence_response: dict[str, Any],
    presentation: dict[str, Any],
    *,
    governed_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a copied payload whose public display fields come from the projection."""

    receipts = presentation.get("exact_action_receipts")
    _require(
        presentation.get("tier") != "receipts_only"
        and isinstance(receipts, list)
        and receipts,
        "analytical presentation lacks governed receipt projections",
    )
    _require(
        evidence_response.get("domain") == presentation.get("issue_id"),
        "evidence issue does not match governed receipt projection",
    )
    projections = {
        receipt["canonical_action_id"]: receipt for receipt in receipts
    }
    _require(
        len(projections) == len(receipts),
        "governed receipt projection repeats an action identity",
    )
    reviewed_action_ids = presentation.get("reviewed_action_ids")
    controls = presentation.get("noncounting_controls")
    _require(
        isinstance(reviewed_action_ids, list)
        and reviewed_action_ids
        and len(set(reviewed_action_ids)) == len(reviewed_action_ids),
        "analytical presentation lacks an exact reviewed action universe",
    )
    _require(
        isinstance(controls, list)
        and all(isinstance(control, dict) for control in controls),
        "analytical presentation lacks governed non-counting controls",
    )
    controls_by_action = {
        control.get("canonical_action_id"): control for control in controls
    }
    _require(
        len(controls_by_action) == len(controls)
        and set(reviewed_action_ids) == set(projections) | set(controls_by_action),
        "governed receipts and controls do not close the reviewed action universe",
    )
    result = copy.deepcopy(evidence_response)
    if governed_evidence is not None:
        result["evidence"] = union_database_actions(result.get("evidence", []), governed_evidence)
    raw_response = copy.deepcopy(result)
    rows_by_action = index_actions(result.get("evidence", []))

    for action_id in reviewed_action_ids:
        _require(
            action_id in rows_by_action,
            f"{action_id}: governed reviewed action is missing",
        )

    for action_id, projection in projections.items():
        row = rows_by_action.get(action_id)
        _require(row is not None, f"{action_id}: governed public receipt is missing")
        _require(
            _normalized_member_action(row.get("position"))
            == _normalized_member_action(projection["member_action"]),
            f"{action_id}: raw member action conflicts with governed receipt",
        )
        _require(
            int(row.get("congress") or 0) in projection["congress_scope"],
            f"{action_id}: raw evidence is outside the governed Congress scope",
        )
        raw_evidence = copy.deepcopy(row)
        row.update(
            {
                "canonical_action_id": action_id,
                "position": _normalized_member_action(
                    projection["member_action"]
                ),
                "interpretation_status": projection["interpretation_status"],
                "plain_english_summary": projection["exact_action_meaning"],
                "source_url": projection["vote_sources"][0]["url"],
                "source_basis": copy.deepcopy(
                    projection["action_meaning_sources"]
                ),
                "governed_receipt_projection": copy.deepcopy(projection),
                "raw_evidence": raw_evidence,
            }
        )
    for action_id, control in controls_by_action.items():
        row = rows_by_action[action_id]
        row["canonical_action_id"] = action_id
        row["governed_receipt_control"] = {
            "status": "noncounting_control",
            "boundary_type": control["boundary_type"],
            "detail": control.get("detail"),
            "published_artifact_identity": presentation["provenance"]["artifact_id"],
        }
    reviewed_rows = [rows_by_action[action_id] for action_id in reviewed_action_ids]
    result = overlay_reviewed_actions(raw_response, reviewed_rows, domain=presentation["issue_id"])
    result["governed_receipt_projection"] = {
        "published_artifact_identity": presentation["provenance"]["artifact_id"],
        "review_receipt_id": presentation["provenance"]["review_receipt_id"],
        "projected_action_count": len(projections),
        "reviewed_action_count": len(reviewed_action_ids),
        "noncounting_control_count": len(controls_by_action),
        "projection_keys": sorted(
            projection["projection_key"] for projection in projections.values()
        ),
    }
    return result
