"""Public selector and serializer for eligible active presentation artifacts."""

from __future__ import annotations

import copy
import hmac
import json
from typing import Any, Iterable

from .compiler import (
    EditorialPresentationError,
    _copy_display_wording,
    approval_subject_for_artifact,
    artifact_digest,
    publication_gates_pass,
    semantic_tier_for_artifact,
)
from .validation import validate_public_issue_presentation
from .review_state_catalog import (
    PublicReviewStateCatalogError,
    public_review_state_entries,
    select_public_review_state,
)


RECEIPTS_ONLY_BADGE = "Vote receipts"
RECEIPTS_ONLY_TEASER = (
    "Reviewed analytical wording is not published for this record scope."
)
SUPPORTED_ISSUES = (
    "ECONOMY_TAXES",
    "HEALTH_SOCIAL",
    "EDUCATION_WORKFORCE",
    "ENVIRONMENT_ENERGY",
    "NATIONAL_SECURITY_FOREIGN",
    "IMMIGRATION_BORDER",
    "JUSTICE_PUBLIC_SAFETY",
    "INFRASTRUCTURE_TECH_TRANSPORT",
)


def _fallback(issue_id: str, scope: str) -> dict[str, Any]:
    return {
        "issue_id": issue_id,
        "requested_scope": scope,
        "reviewed_scope": None,
        "tier": "receipts_only",
        "tier_badge": RECEIPTS_ONLY_BADGE,
        "teaser": RECEIPTS_ONLY_TEASER,
        "coverage_text": None,
        "scope_boundary": None,
        "conclusion": None,
        "repeated_patterns": [],
        "policy_trajectories": [],
        "limitations": [],
        "policy_episodes": [],
        "public_status_label": "Vote receipts available",
        "review_state": None,
        "evidence_metadata": None,
        "provenance": None,
    }


def _payload(row: dict[str, Any]) -> dict[str, Any] | None:
    payload = row.get("payload_jsonb", row.get("payload"))
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None
    return payload if isinstance(payload, dict) else None


def _detached_receipt(row: dict[str, Any]) -> dict[str, Any] | None:
    receipt = row.get("approval_receipt")
    metadata = row.get("publication_metadata_jsonb")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            return None
    if receipt is None and isinstance(metadata, dict):
        receipt = metadata.get("approval_receipt")
    if isinstance(receipt, str):
        try:
            receipt = json.loads(receipt)
        except json.JSONDecodeError:
            return None
    return receipt if isinstance(receipt, dict) else None


def _eligible_row(
    row: dict[str, Any],
    *,
    member_bioguide_id: str,
    scope: str,
) -> dict[str, Any] | None:
    if (
        row.get("member_bioguide_id") != member_bioguide_id
        or row.get("publicly_active") is not True
        or row.get("deactivated_at") is not None
        or row.get("editorial_status") != "human_approved"
        or row.get("benchmark_status") != "gold_benchmark"
        or row.get("production_eligible") is not True
    ):
        return None
    payload = _payload(row)
    if payload is None:
        return None
    try:
        validate_public_issue_presentation(payload)
    except (KeyError, TypeError, EditorialPresentationError):
        return None
    identity = payload["artifact_identity"]
    controls = payload["controls"]
    detached_receipt = _detached_receipt(row)
    if (
        controls["publication"]["active"] is not True
        or row.get("issue_id") != identity["issue_id"]
        or identity["issue_id"] not in SUPPORTED_ISSUES
        or identity["member_id"] != member_bioguide_id
        or row.get("natural_key") != identity["artifact_id"]
        or row.get("artifact_version") != identity["artifact_version"]
        or row.get("schema_version") != payload["schema_version"]
    ):
        return None
    stored_digest = row.get("content_sha256")
    if not isinstance(stored_digest, str) or not hmac.compare_digest(
        stored_digest,
        artifact_digest(payload),
    ):
        return None
    reviewed_scope = identity["scope"]
    if scope == "118" or reviewed_scope != "119":
        return None
    if not publication_gates_pass(
        controls,
        expected_subject=approval_subject_for_artifact(payload),
        detached_receipt=detached_receipt,
    ):
        return None
    payload = copy.deepcopy(payload)
    payload["frontend_display"] = _copy_display_wording(
        payload["editorial_wording"],
        semantic_tier=semantic_tier_for_artifact(payload),
    )
    payload["_detached_approval_receipt_id"] = detached_receipt["receipt_id"]
    return payload


def _display_action_ids(display: dict[str, Any]) -> set[str]:
    return {
        action_id
        for field in ("repeated_patterns", "policy_trajectories")
        for item in display.get(field, [])
        for action_id in item.get("action_ids", [])
    }


def _receipt_projections_agree(
    artifact: dict[str, Any],
    display: dict[str, Any],
    review_state: dict[str, Any],
) -> bool:
    identity = artifact["artifact_identity"]
    receipts = review_state.get("exact_action_receipts")
    if not isinstance(receipts, list):
        return False
    by_action = {
        receipt.get("canonical_action_id"): receipt
        for receipt in receipts
        if isinstance(receipt, dict)
    }
    sample_action_ids = set(artifact["evidence_metadata"]["action_ids"])
    if (
        len(by_action) != len(receipts)
        or set(by_action) != sample_action_ids
        or not _display_action_ids(display) <= sample_action_ids
    ):
        return False
    for action_id, receipt in by_action.items():
        if (
            receipt.get("member_id") != identity["member_id"]
            or receipt.get("issue_id") != identity["issue_id"]
            or identity["congress"] not in receipt.get("congress_scope", [])
            or receipt.get("published_artifact_identity")
            != identity["artifact_id"]
            or receipt.get("interpretation_status") != "interpreted"
            or receipt.get("canonical_action_id") != action_id
            or not receipt.get("vote_sources")
            or not receipt.get("action_meaning_sources")
        ):
            return False
    return True


def select_public_presentations(
    rows: Iterable[dict[str, Any]],
    *,
    legislator_id: str,
    member_bioguide_id: str,
    scope: str,
    review_states: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return only active eligible display fields, with supplied fallbacks."""

    if review_states is None:
        try:
            review_states = public_review_state_entries()
        except PublicReviewStateCatalogError:
            review_states = []
    review_states = list(review_states)
    result = {
        issue_id: _fallback(issue_id, scope) for issue_id in SUPPORTED_ISSUES
    }
    for row in rows:
        artifact = _eligible_row(
            row,
            member_bioguide_id=member_bioguide_id,
            scope=scope,
        )
        if artifact is None:
            continue
        identity = artifact["artifact_identity"]
        issue_id = identity["issue_id"]
        review_state = select_public_review_state(
            review_states,
            member_id=member_bioguide_id,
            issue_id=issue_id,
            requested_scope=scope,
            published_artifact_identity=identity["artifact_id"],
        )
        if review_state is None:
            continue
        display = copy.deepcopy(artifact["frontend_display"])
        if (
            review_state["semantic_tier"] != display["tier"]
            or review_state["scope_bounded_teaser"] is None
            or review_state["scope_bounded_teaser"]["text"] != display["teaser"]
            or not _receipt_projections_agree(artifact, display, review_state)
        ):
            continue
        exact_action_receipts = copy.deepcopy(
            review_state["exact_action_receipts"]
        )
        public_review_state = copy.deepcopy(review_state)
        public_review_state.pop("exact_action_receipts", None)
        proposition_index = {
            item["proposition_id"]: item
            for item in artifact["compiled_semantic_meaning"]["propositions"]
        }
        findings_are_bound = True
        for field in ("repeated_patterns", "policy_trajectories"):
            enriched = []
            for item in display[field]:
                proposition = proposition_index.get(item.get("proposition_id"))
                if proposition is None:
                    findings_are_bound = False
                    break
                enriched.append(
                    {
                        **item,
                        "semantic_role": proposition["semantic_role"],
                        "direction": proposition["direction"],
                    }
                )
            display[field] = enriched
        if not findings_are_bound:
            continue
        result[issue_id] = {
            "issue_id": issue_id,
            "requested_scope": scope,
            "reviewed_scope": identity["scope"],
            **display,
            "scope_boundary": (
                display["scope_boundary"]
                if scope == "119"
                else f"{display['scope_boundary']} The conclusion remains bounded to the reviewed 119th-Congress record."
            ),
            "policy_episodes": [],
            "public_status_label": review_state["public_status_label"],
            "review_state": public_review_state,
            "exact_action_receipts": exact_action_receipts,
            "evidence_metadata": copy.deepcopy(artifact["evidence_metadata"]),
            "provenance": {
                "artifact_id": identity["artifact_id"],
                "artifact_version": identity["artifact_version"],
                "compiled_ir_sha256": artifact["provenance"][
                    "compiled_ir_sha256"
                ],
                "reviewed_wording_sha256": artifact["provenance"][
                    "reviewed_wording_sha256"
                ],
                "review_receipt_id": artifact[
                    "_detached_approval_receipt_id"
                ],
            },
        }
    return {
        "schema_version": "editorial_public_presentations_api_v1",
        "legislator_id": legislator_id,
        "member_bioguide_id": member_bioguide_id,
        "scope": scope,
        "presentations": [result[issue_id] for issue_id in SUPPORTED_ISSUES],
    }
