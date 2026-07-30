"""Closed, non-authorizing public review-state catalog helpers."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


CATALOG_SCHEMA_VERSION = "public_review_state_catalog_v1"
CATALOG_PATH = Path(__file__).with_name("public_review_state_catalog_v1.json")
PUBLIC_STATUS_LABELS = {
    "Reviewed benchmark sample",
    "Full review complete",
    "Full issue interpretation available",
    "No common throughline found",
    "No safe synthesis available",
    "Vote receipts available",
}
ENTRY_FIELDS = {
    "catalog_key",
    "member_id",
    "issue_id",
    "congress_scope",
    "published_artifact_identity",
    "semantic_tier",
    "review_scope",
    "review_completion_state",
    "public_claim_class",
    "total_recorded_actions",
    "review_friendly_actions",
    "interpreted_actions",
    "unresolved_actions",
    "procedural_context_actions",
    "present_actions",
    "not_voting_actions",
    "complete_episode_count",
    "partial_episode_count",
    "full_issue_synthesis_eligible",
    "benchmark_sample_available",
    "scope_bounded_teaser",
    "public_status_label",
}
COUNT_FIELDS = {
    "total_recorded_actions",
    "review_friendly_actions",
    "interpreted_actions",
    "unresolved_actions",
    "procedural_context_actions",
    "present_actions",
    "not_voting_actions",
    "complete_episode_count",
    "partial_episode_count",
}


class PublicReviewStateCatalogError(ValueError):
    """Raised when generated public catalog data is not closed and safe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicReviewStateCatalogError(message)


def catalog_key(
    *,
    member_id: str,
    issue_id: str,
    congress_scope: Iterable[int],
    published_artifact_identity: str | None,
) -> str:
    scope = ",".join(str(item) for item in sorted(congress_scope))
    artifact = published_artifact_identity or "none"
    return f"{member_id}:{issue_id}:{scope}:{artifact}"


def validate_public_catalog(catalog: dict[str, Any]) -> None:
    _require(
        set(catalog) == {"schema_version", "entries"},
        "public review-state catalog must contain exactly schema_version and entries",
    )
    _require(
        catalog["schema_version"] == CATALOG_SCHEMA_VERSION,
        "unexpected public review-state catalog schema version",
    )
    _require(isinstance(catalog["entries"], list), "catalog entries must be an array")
    keys: set[str] = set()
    for entry in catalog["entries"]:
        _require(isinstance(entry, dict), "catalog entry must be an object")
        _require(
            set(entry) == ENTRY_FIELDS,
            "public review-state entry contains missing or non-public fields",
        )
        _require(
            isinstance(entry["member_id"], str)
            and isinstance(entry["issue_id"], str),
            "catalog identity must be strings",
        )
        scope = entry["congress_scope"]
        _require(
            isinstance(scope, list)
            and scope
            and all(isinstance(item, int) and item > 0 for item in scope)
            and scope == sorted(set(scope)),
            "catalog Congress scope must be a sorted unique integer array",
        )
        expected_key = catalog_key(
            member_id=entry["member_id"],
            issue_id=entry["issue_id"],
            congress_scope=scope,
            published_artifact_identity=entry["published_artifact_identity"],
        )
        _require(entry["catalog_key"] == expected_key, "catalog key does not match identity")
        _require(expected_key not in keys, "duplicate public review-state identity")
        keys.add(expected_key)
        _require(
            entry["public_status_label"] in PUBLIC_STATUS_LABELS,
            "catalog status label is not in the closed public vocabulary",
        )
        for field in COUNT_FIELDS:
            _require(
                isinstance(entry[field], int)
                and not isinstance(entry[field], bool)
                and entry[field] >= 0,
                f"{field} must be a non-negative integer",
            )
        _require(
            isinstance(entry["full_issue_synthesis_eligible"], bool)
            and isinstance(entry["benchmark_sample_available"], bool),
            "catalog eligibility fields must be booleans",
        )
        teaser = entry["scope_bounded_teaser"]
        _require(
            teaser is None
            or (
                isinstance(teaser, dict)
                and set(teaser) == {"text", "valid_scope"}
                and isinstance(teaser["text"], str)
                and bool(teaser["text"].strip())
                and teaser["valid_scope"] == entry["review_scope"]
            ),
            "catalog teaser must be null or closed and valid for the declared scope",
        )
        if entry["public_claim_class"] == "vote_record_only":
            _require(teaser is None, "vote-record-only state cannot expose a teaser")
        if entry["public_claim_class"] == "reviewed_sample_finding":
            _require(
                entry["review_scope"] in {"benchmark_sample", "bounded_partial_record"}
                and entry["public_status_label"] == "Reviewed benchmark sample"
                and entry["full_issue_synthesis_eligible"] is False,
                "reviewed sample finding cannot acquire a full-record label",
            )
        if entry["public_status_label"] in {
            "Full review complete",
            "Full issue interpretation available",
            "No common throughline found",
            "No safe synthesis available",
        }:
            _require(
                entry["review_scope"] == "full_defined_issue_record"
                and entry["review_completion_state"] == "complete",
                "full-record public labels require a complete full defined issue record",
            )
        if entry["review_scope"] != "full_defined_issue_record":
            _require(
                entry["full_issue_synthesis_eligible"] is False,
                "partial or benchmark state cannot expose full synthesis eligibility",
            )


@lru_cache(maxsize=1)
def load_public_review_state_catalog() -> dict[str, Any]:
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicReviewStateCatalogError(
            "public review-state catalog is unavailable"
        ) from exc
    validate_public_catalog(catalog)
    return catalog


def public_review_state_entries() -> list[dict[str, Any]]:
    """Return a defensive copy; catalog state never authorizes publication."""

    return copy.deepcopy(load_public_review_state_catalog()["entries"])


def select_public_review_state(
    entries: Iterable[dict[str, Any]],
    *,
    member_id: str,
    issue_id: str,
    requested_scope: str,
    published_artifact_identity: str,
) -> dict[str, Any] | None:
    """Select exact identity/scope state without broadening its Congress boundary."""

    if requested_scope not in {"all", "119"}:
        return None
    matches = [
        entry
        for entry in entries
        if entry.get("member_id") == member_id
        and entry.get("issue_id") == issue_id
        and entry.get("published_artifact_identity") == published_artifact_identity
        and (
            requested_scope == "all"
            or int(requested_scope) in entry.get("congress_scope", [])
        )
    ]
    if len(matches) != 1:
        return None
    candidate = {"schema_version": CATALOG_SCHEMA_VERSION, "entries": [matches[0]]}
    try:
        validate_public_catalog(candidate)
    except PublicReviewStateCatalogError:
        return None
    return copy.deepcopy(matches[0])
