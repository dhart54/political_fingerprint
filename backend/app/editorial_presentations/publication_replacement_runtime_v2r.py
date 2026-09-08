"""Additive normal-runtime adapter for a sealed M14G V2R replacement.

Installation is explicit from ``app.main``.  It leaves the accepted historical
M13 runtime files byte-identical while extending their dispatch tables only for
the new content-addressed M14G identity.
"""

from __future__ import annotations

import hmac
from typing import Any, Iterable

from . import selector, site_publication
from .compiler import canonical_digest
from .education_workforce_m14g_integration_candidate import (
    M14G_ARTIFACT_ID,
    M14G_SCHEMA_VERSION,
    merge_m14g_preview_evidence,
    merge_m14g_preview_positions,
    select_m14g_preview,
    validate_m14g_candidate,
)
from .publication_replacement_governance_v2 import (
    POSITIVE_AUTHORIZATIONS_V2R,
    REPLACEMENT_AUTHORITY_SCHEMA_V2,
    REVIEWER_AUTHORITY_V2R,
    TARGET,
)

M14G_CANDIDATE_SUBJECT_SHA256 = (
    "92d491a97ff675d60896d64fe3cb9e5d9e87ffc684f19f151a13f01b99ab05d0"
)
M14G_ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256 = (
    "854c184469dc9338820cb3274418c8b16b2289497b3fd551aebccd46531c070b"
)
M14G_CANDIDATE_COMPLETE_FILE_SHA256 = (
    "7022fff0cbd8e54acab095401c2810b93359c3a55d8a5a03eba86e4e6d14d2c6"
)
M14G_HUMAN_SITE_INTEGRATION_AUTHORITY_SHA256 = (
    "7042fd16cc707ffc2bef57d7eff4925d01ffe551cf3d09e0aabc05e52b51e35e"
)
PUBLIC_SCOPE_BOUNDARY = (
    "This interpretation covers Valerie Foushee's reviewed 119th-Congress "
    "Education & Workforce record."
)
BOUNDED_ANALYSIS_BOUNDARY = (
    "The analytical summary remains bounded to the 119th-Congress record."
)
_INSTALLED = False
_ORIGINAL_ELIGIBLE = site_publication.eligible_site_integration_candidate
_ORIGINAL_SELECT = site_publication.select_site_integration_public


def _object(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def eligible_m14g_replacement(
    row: dict[str, Any], *, member_bioguide_id: str,
    allow_test_authority: bool = False,
) -> dict[str, Any] | None:
    payload = _object(row.get("payload_jsonb", row.get("payload")))
    metadata = _object(row.get("publication_metadata_jsonb"))
    if payload is None or metadata is None or payload.get("artifact_id") != M14G_ARTIFACT_ID:
        return None
    authority = _object(metadata.get("publication_replacement_activation_authority"))
    subject = _object(authority.get("subject")) if authority else None
    if authority is None or subject is None:
        return None
    try:
        validate_m14g_candidate(payload)
    except (KeyError, TypeError, ValueError):
        return None
    content_sha256 = canonical_digest(payload)
    if (
        authority.get("schema_version") != REPLACEMENT_AUTHORITY_SCHEMA_V2
        or authority.get("sealed") is not True
        or authority.get("accepted") is not True
        or (authority.get("test_only_synthetic") is True and not allow_test_authority)
        or authority.get("activation_authority_subject_sha256") != canonical_digest(subject)
        or subject.get("decision") != "approve_exact_publication_replacement_v2"
        or subject.get("reviewer_authority") != REVIEWER_AUTHORITY_V2R
        or subject.get("replacement_registry_target") != TARGET
        or subject.get("accepted_site_integration_subject_sha256")
        != M14G_ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256
        or subject.get("reviewed_candidate_subject_sha256")
        != M14G_CANDIDATE_SUBJECT_SHA256
        or subject.get("reviewed_candidate_complete_file_sha256")
        != M14G_CANDIDATE_COMPLETE_FILE_SHA256
        or subject.get("semantic_human_authority_lineage") != [
            M14G_HUMAN_SITE_INTEGRATION_AUTHORITY_SHA256,
            M14G_ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256,
        ]
        or subject.get("authorizations") != POSITIVE_AUTHORIZATIONS_V2R
        or subject.get("exact_write_set_subject_sha256")
        != metadata.get("v2r_write_set_subject_sha256")
        or metadata.get("activation_authority_subject_sha256")
        != authority.get("activation_authority_subject_sha256")
        or row.get("member_bioguide_id") != member_bioguide_id
        or payload.get("subject", {}).get("member_bioguide_id") != member_bioguide_id
        or payload.get("subject", {}).get("congress") != 119
        or row.get("issue_id") != "EDUCATION_WORKFORCE"
        or row.get("publicly_active") is not True
        or row.get("deactivated_at") is not None
        or row.get("editorial_status") != "human_approved"
        or row.get("benchmark_status") != "gold_benchmark"
        or row.get("production_eligible") is not True
        or row.get("natural_key") != M14G_ARTIFACT_ID
        or row.get("schema_version") != M14G_SCHEMA_VERSION
        or row.get("artifact_version") != 1
        or not isinstance(row.get("content_sha256"), str)
        or not hmac.compare_digest(row["content_sha256"], content_sha256)
        or metadata.get("presentation_natural_key") != M14G_ARTIFACT_ID
        or metadata.get("presentation_artifact_version") != 1
        or metadata.get("m14g_accepted_site_integration_subject_sha256")
        != M14G_ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256
        or metadata.get("m14g_reviewed_candidate_subject_sha256")
        != M14G_CANDIDATE_SUBJECT_SHA256
        or metadata.get("m14g_reviewed_candidate_complete_file_sha256")
        != M14G_CANDIDATE_COMPLETE_FILE_SHA256
        or metadata.get("active_artifact_sha256") != content_sha256
    ):
        return None
    return payload


def eligible_site_integration_candidate_v2r(
    row: dict[str, Any], *, member_bioguide_id: str,
    allow_test_authority: bool = False,
) -> dict[str, Any] | None:
    historical = _ORIGINAL_ELIGIBLE(
        row,
        member_bioguide_id=member_bioguide_id,
        allow_test_authority=allow_test_authority,
    )
    return historical or eligible_m14g_replacement(
        row,
        member_bioguide_id=member_bioguide_id,
        allow_test_authority=allow_test_authority,
    )


def select_site_integration_public_v2r(
    candidate: dict[str, Any], *, legislator_id: str,
    member_bioguide_id: str, scope: str,
) -> dict[str, Any]:
    if candidate.get("artifact_id") != M14G_ARTIFACT_ID:
        return _ORIGINAL_SELECT(
            candidate,
            legislator_id=legislator_id,
            member_bioguide_id=member_bioguide_id,
            scope=scope,
        )
    result = select_m14g_preview(
        candidate,
        legislator_id=legislator_id,
        member_bioguide_id=member_bioguide_id,
        scope=scope,
    )
    for presentation in result["presentations"]:
        if presentation["issue_id"] == "EDUCATION_WORKFORCE" and presentation["tier"] != "receipts_only":
            presentation["public_status_label"] = "Full issue interpretation available"
            presentation.get("review_state", {}).pop("candidate_preview", None)
            presentation["scope_boundary"] = PUBLIC_SCOPE_BOUNDARY
            if scope == "all":
                presentation["scope_boundary"] += f" {BOUNDED_ANALYSIS_BOUNDARY}"
    return result


def install_publication_replacement_runtime_v2r() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    site_publication.eligible_site_integration_candidate = eligible_site_integration_candidate_v2r
    site_publication.select_site_integration_public = select_site_integration_public_v2r
    selector.eligible_site_integration_candidate = eligible_site_integration_candidate_v2r
    selector.select_site_integration_public = select_site_integration_public_v2r

    from app.api import positions

    original_evidence = positions._merge_site_integration_evidence
    original_positions = positions._merge_site_integration_positions

    def merge_evidence(base_response, candidate, *, domain, scope):
        if candidate.get("artifact_id") == M14G_ARTIFACT_ID:
            return merge_m14g_preview_evidence(
                base_response, candidate, domain=domain, scope=scope
            )
        return original_evidence(base_response, candidate, domain=domain, scope=scope)

    def merge_positions(base_response, candidate, *, governed_evidence):
        if candidate.get("artifact_id") == M14G_ARTIFACT_ID:
            return merge_m14g_preview_positions(
                base_response, governed_evidence=governed_evidence
            )
        return original_positions(
            base_response, candidate, governed_evidence=governed_evidence
        )

    positions._merge_site_integration_evidence = merge_evidence
    positions._merge_site_integration_positions = merge_positions
    _INSTALLED = True


def select_public_presentations_v2r(
    rows: Iterable[dict[str, Any]], **kwargs: Any
) -> dict[str, Any]:
    install_publication_replacement_runtime_v2r()
    return selector.select_public_presentations(rows, **kwargs)
