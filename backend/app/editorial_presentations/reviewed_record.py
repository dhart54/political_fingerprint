"""Exact reviewed overlays on a current database action ledger."""

from __future__ import annotations

import copy
import re
from typing import Any

REVIEWED = "reviewed_interpretation"
UNREVIEWED = "not_yet_in_reviewed_interpretation"
_IDENTITY = re.compile(r"(house|senate):([1-9][0-9]*):([12]):([1-9][0-9]*)\Z")
_RAW_FIELDS = {
    "roll_call_id", "canonical_action_id", "chamber", "congress", "session",
    "rollcall_number", "vote_date", "position", "issue_domain", "vote_context",
    "final_result", "current_status", "raw_evidence",
}


class GovernedReceiptProjectionError(ValueError):
    """The available record cannot safely bind a governed interpretation."""


def canonical_action_id(row: dict[str, Any]) -> str | None:
    supplied = row.get("canonical_action_id")
    fields = [row.get(key) for key in ("chamber", "congress", "session", "rollcall_number")]
    explicit = ":".join(str(value).lower() for value in fields) if all(value is not None for value in fields) else None
    if supplied is not None:
        if not isinstance(supplied, str) or not _IDENTITY.fullmatch(supplied):
            raise GovernedReceiptProjectionError("invalid canonical action identity")
        # Even a partial set of supplied identity fields cannot contradict the ID.
        if any(value is not None and str(value).lower() != part for value, part in zip(fields, supplied.split(":"))):
            raise GovernedReceiptProjectionError("canonical action conflicts with raw identity")
        return supplied
    return explicit if explicit and _IDENTITY.fullmatch(explicit) else None


def index_actions(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed = {}
    for row in rows:
        identity = canonical_action_id(row)
        if identity is None:
            continue
        if identity in indexed:
            raise GovernedReceiptProjectionError(f"{identity}: repeated canonical action")
        indexed[identity] = row
    return indexed


def union_database_actions(raw: list[dict[str, Any]], reviewed_query: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union two DB selections, never deduplicating duplicates within either query."""
    result = copy.deepcopy(raw)
    existing = index_actions(result)
    additional = index_actions(reviewed_query)
    for identity, row in additional.items():
        if identity in existing:
            for key in ("position", "vote_date", "roll_call_id"):
                if str(existing[identity].get(key)).lower() != str(row.get(key)).lower():
                    raise GovernedReceiptProjectionError(f"{identity}: conflicting database {key}")
        else:
            result.append(copy.deepcopy(row))
    return result


def review_accounting(rows: list[dict[str, Any]]) -> dict[str, int]:
    reviewed = sum(row.get("interpretation_review_state") == REVIEWED for row in rows)
    unreviewed = sum(row.get("interpretation_review_state") == UNREVIEWED for row in rows)
    return {"available_action_count": len(rows), "reviewed_action_count": reviewed,
            "not_yet_reviewed_action_count": unreviewed}


def overlay_reviewed_actions(response: dict[str, Any], reviewed_rows: list[dict[str, Any]], *, domain: str) -> dict[str, Any]:
    """Enrich exact matches, preserving every raw row and its accounting identity."""
    result = copy.deepcopy(response)
    rows = result.get("evidence", [])
    index_actions(rows)
    projections = index_actions(reviewed_rows)
    if len(projections) != len(reviewed_rows):
        raise GovernedReceiptProjectionError("reviewed projection lacks exact identity")
    for row in rows:
        if row.get("issue_domain") not in {None, domain}:
            raise GovernedReceiptProjectionError("evidence issue conflicts with reviewed issue")
        row["issue_domain"] = domain
        identity = canonical_action_id(row)
        projection = projections.get(identity)
        row.pop("governed_receipt_projection", None)
        row.pop("governed_receipt_control", None)
        row["interpretation_review_state"] = REVIEWED if projection else UNREVIEWED
        if projection is None:
            continue
        if str(row.get("position", "")).lower().replace(" ", "_") != str(projection.get("position", "")).lower().replace(" ", "_"):
            raise GovernedReceiptProjectionError(f"{identity}: raw member action conflicts with governed receipt")
        raw_evidence = copy.deepcopy(row.get("raw_evidence", row))
        row.update(copy.deepcopy({key: value for key, value in projection.items() if key not in _RAW_FIELDS and key != "interpretation_review_state"}))
        row["canonical_action_id"] = identity
        row["raw_evidence"] = raw_evidence
    result["review_accounting"] = review_accounting(rows)
    return result
