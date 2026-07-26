"""Public selector and serializer for eligible active presentation artifacts."""

from __future__ import annotations

import copy
import hmac
import json
from typing import Any, Iterable

from .compiler import EditorialPresentationError, artifact_digest
from .validation import validate_public_issue_presentation


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
    if (
        controls["publication"]["active"] is not True
        or payload["frontend_display"]["tier"] == "receipts_only"
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
    return payload


def select_public_presentations(
    rows: Iterable[dict[str, Any]],
    *,
    legislator_id: str,
    member_bioguide_id: str,
    scope: str,
) -> dict[str, Any]:
    """Return only active eligible display fields, with supplied fallbacks."""

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
        display = copy.deepcopy(artifact["frontend_display"])
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
                "review_receipt_id": artifact["controls"]["review_receipt"][
                    "receipt_id"
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
