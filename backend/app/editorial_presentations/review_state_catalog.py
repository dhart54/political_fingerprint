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
    "exact_action_receipts",
}
SOURCE_FIELDS = {"source_id", "source_type", "name", "url"}
PROJECTION_SOURCE_FIELDS = {
    "review_id",
    "source_contract_id",
    "source_manifest_sha256",
}
RECEIPT_FIELDS = {
    "projection_key",
    "member_id",
    "issue_id",
    "congress_scope",
    "published_artifact_identity",
    "canonical_action_id",
    "action_interpretation_id",
    "action_interpretation_sha256",
    "action_meaning_id",
    "member_action",
    "interpretation_disposition",
    "interpretation_status",
    "exact_action_meaning",
    "policy_question",
    "episode_id",
    "vote_sources",
    "action_meaning_sources",
    "interpretation_receipt_refs",
    "review_scope",
    "public_claim_class",
    "caveats",
    "projection_source",
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


def receipt_projection_key(
    *,
    member_id: str,
    issue_id: str,
    congress_scope: Iterable[int],
    published_artifact_identity: str,
    canonical_action_id: str,
    action_interpretation_id: str,
    action_interpretation_sha256: str,
) -> str:
    scope = ",".join(str(item) for item in sorted(congress_scope))
    return (
        f"{member_id}:{issue_id}:{scope}:{published_artifact_identity}:"
        f"{canonical_action_id}:{action_interpretation_id}:"
        f"{action_interpretation_sha256}"
    )


def _validate_source(source: dict[str, Any], *, action_id: str) -> None:
    _require(
        isinstance(source, dict) and set(source) == SOURCE_FIELDS,
        f"{action_id}: receipt source contains missing or non-public fields",
    )
    _require(
        all(isinstance(source[field], str) and source[field].strip() for field in SOURCE_FIELDS),
        f"{action_id}: receipt source fields must be non-empty strings",
    )
    _require(
        source["url"].startswith("https://"),
        f"{action_id}: receipt source URL must use HTTPS",
    )


def _validate_receipt(receipt: dict[str, Any], *, entry: dict[str, Any]) -> None:
    action_id = str(receipt.get("canonical_action_id") or "<unknown>")
    _require(
        isinstance(receipt, dict) and set(receipt) == RECEIPT_FIELDS,
        f"{action_id}: receipt projection contains missing or non-public fields",
    )
    _require(
        receipt["member_id"] == entry["member_id"]
        and receipt["issue_id"] == entry["issue_id"]
        and receipt["congress_scope"] == entry["congress_scope"]
        and receipt["published_artifact_identity"]
        == entry["published_artifact_identity"],
        f"{action_id}: receipt projection identity differs from its catalog entry",
    )
    _require(
        receipt["review_scope"] == entry["review_scope"]
        and receipt["public_claim_class"] == entry["public_claim_class"],
        f"{action_id}: receipt projection broadens the governed claim scope",
    )
    expected_key = receipt_projection_key(
        member_id=receipt["member_id"],
        issue_id=receipt["issue_id"],
        congress_scope=receipt["congress_scope"],
        published_artifact_identity=receipt["published_artifact_identity"],
        canonical_action_id=receipt["canonical_action_id"],
        action_interpretation_id=receipt["action_interpretation_id"],
        action_interpretation_sha256=receipt["action_interpretation_sha256"],
    )
    _require(
        receipt["projection_key"] == expected_key,
        f"{action_id}: receipt projection key does not match its bound identity",
    )
    _require(
        isinstance(receipt["canonical_action_id"], str)
        and receipt["canonical_action_id"].count(":") == 3,
        f"{action_id}: canonical action identity is invalid",
    )
    _require(
        isinstance(receipt["action_interpretation_id"], str)
        and receipt["action_interpretation_id"].strip()
        and isinstance(receipt["action_meaning_id"], str)
        and receipt["action_meaning_id"].strip()
        and isinstance(receipt["action_interpretation_sha256"], str)
        and len(receipt["action_interpretation_sha256"]) == 64,
        f"{action_id}: governed interpretation identity is incomplete",
    )
    _require(
        receipt["member_action"] in {"Yea", "Nay", "Present", "Not Voting"}
        and receipt["interpretation_disposition"]
        in {
            "interpreted_substantive_directional",
            "interpreted_substantive_non_directional",
        }
        and receipt["interpretation_status"] == "interpreted",
        f"{action_id}: receipt projection is not a governed interpreted action",
    )
    _require(
        isinstance(receipt["exact_action_meaning"], str)
        and receipt["exact_action_meaning"].strip()
        and isinstance(receipt["policy_question"], str)
        and receipt["policy_question"].strip()
        and isinstance(receipt["episode_id"], str)
        and receipt["episode_id"].strip(),
        f"{action_id}: receipt projection lacks governed public meaning",
    )
    for field in ("vote_sources", "action_meaning_sources"):
        _require(
            isinstance(receipt[field], list) and receipt[field],
            f"{action_id}: {field} must contain governed official sources",
        )
        for source in receipt[field]:
            _validate_source(source, action_id=action_id)
        source_ids = [source["source_id"] for source in receipt[field]]
        _require(
            len(source_ids) == len(set(source_ids)),
            f"{action_id}: {field} repeats a source identity",
        )
    _require(
        isinstance(receipt["interpretation_receipt_refs"], list)
        and receipt["interpretation_receipt_refs"]
        and all(
            isinstance(reference, str) and reference.strip()
            for reference in receipt["interpretation_receipt_refs"]
        ),
        f"{action_id}: interpretation receipt references are incomplete",
    )
    _require(
        isinstance(receipt["caveats"], list)
        and all(isinstance(caveat, str) and caveat.strip() for caveat in receipt["caveats"]),
        f"{action_id}: caveats must be governed strings",
    )
    source = receipt["projection_source"]
    _require(
        isinstance(source, dict)
        and set(source) == PROJECTION_SOURCE_FIELDS
        and all(isinstance(source[field], str) and source[field].strip() for field in source),
        f"{action_id}: projection source identity is incomplete",
    )


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
        receipts = entry["exact_action_receipts"]
        _require(
            isinstance(receipts, list),
            "exact-action receipt projections must be an array",
        )
        receipt_ids: set[str] = set()
        for receipt in receipts:
            _validate_receipt(receipt, entry=entry)
            action_id = receipt["canonical_action_id"]
            _require(
                action_id not in receipt_ids,
                "duplicate exact-action receipt projection",
            )
            receipt_ids.add(action_id)
        if entry["public_claim_class"] != "vote_record_only":
            _require(
                len(receipts) == entry["interpreted_actions"],
                "analytical review-state receipts must cover every interpreted action",
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
