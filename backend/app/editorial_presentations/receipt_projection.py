"""Apply publication-gated governed receipt projections without erasing raw evidence."""

from __future__ import annotations

import copy
from datetime import date
from typing import Any


class GovernedReceiptProjectionError(ValueError):
    """Raised when governed receipt meaning cannot be safely bound to evidence."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GovernedReceiptProjectionError(message)


def _canonical_action_id(row: dict[str, Any]) -> str:
    supplied = row.get("canonical_action_id")
    if isinstance(supplied, str) and supplied.count(":") == 3:
        return supplied
    chamber = str(row.get("chamber") or "").strip().lower()
    congress = int(row.get("congress") or 0)
    roll_call = int(row.get("rollcall_number") or 0)
    vote_date = date.fromisoformat(str(row.get("vote_date") or "")[:10])
    congress_start_year = 1789 + ((congress - 1) * 2)
    session = vote_date.year - congress_start_year + 1
    if (
        chamber not in {"house", "senate"}
        or congress <= 0
        or roll_call <= 0
        or session not in {1, 2}
    ):
        raise GovernedReceiptProjectionError(
            "raw evidence cannot be bound to a canonical action identity"
        )
    return f"{chamber}:{congress}:{session}:{roll_call}"


def _normalized_member_action(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def attach_governed_receipt_projections(
    evidence_response: dict[str, Any],
    presentation: dict[str, Any],
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
    result = copy.deepcopy(evidence_response)
    rows_by_action: dict[str, dict[str, Any]] = {}
    for row in result.get("evidence", []):
        action_id = _canonical_action_id(row)
        _require(
            action_id not in rows_by_action,
            f"{action_id}: raw evidence repeats a canonical action",
        )
        rows_by_action[action_id] = row

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
    result["governed_receipt_projection"] = {
        "published_artifact_identity": presentation["provenance"]["artifact_id"],
        "review_receipt_id": presentation["provenance"]["review_receipt_id"],
        "projected_action_count": len(projections),
        "projection_keys": sorted(
            projection["projection_key"] for projection in projections.values()
        ),
    }
    return result
