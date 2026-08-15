"""Fail-closed publication adapter for an accepted site-integration artifact."""

from __future__ import annotations

import copy
import hmac
import json
import re
from typing import Any, Iterable

from .compiler import canonical_digest

CANDIDATE_AUTHORITY_SCHEMA_VERSION = (
    "site_integration_production_eligibility_publication_authority_v1"
)
ACTIVATION_AUTHORITY_SCHEMA_VERSION = (
    "site_integration_publication_activation_authority_v1"
)
ACTIVATION_AUTHORITY_ID = (
    "publication-activation-authority:f000477:national_security_foreign:119:v1"
)
ACTIVATION_REVIEWER_AUTHORITY = "publication_activation_review_authority_v1"
M11M_ARTIFACT_ID = "site-integration-candidate:f000477:national_security_foreign:119:v1"
M11M_SCHEMA_VERSION = "editorial_site_integration_candidate_v1"
M11M_FILE_SHA256 = "d2a7a65eb56f4be68b0d0477eeb8f75f793be5bbb458c86db13560b8eae35cc4"
M11M_SUBJECT_SHA256 = "c0fa5282f061c4d27c259968dd08b5f7a804fdbe60c4b8794714e0c9ad04c5df"
MEMBER_ID = "F000477"
ISSUE_ID = "NATIONAL_SECURITY_FOREIGN"
CONGRESS = 119

POSITIVE_AUTHORIZATIONS = {
    "production_database_write": True,
    "publication_registry_mutation": True,
    "publication_activation": True,
    "exact_bounded_rollback": True,
    "deploy_exact_reviewed_runtime": True,
}
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")


def _object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def validate_candidate_preparation_authority(
    authority: dict[str, Any], *, candidate: dict[str, Any]
) -> None:
    """Validate non-activating M11N preparation/eligibility provenance."""

    subject = authority.get("subject")
    if (
        authority.get("schema_version") != CANDIDATE_AUTHORITY_SCHEMA_VERSION
        or authority.get("artifact_id")
        != "production-eligibility-publication-authority:f000477:national_security_foreign:119:v1"
        or authority.get("immutable") is not True
        or authority.get("accepted") is not True
        or not isinstance(subject, dict)
        or authority.get("authority_subject_sha256") != canonical_digest(subject)
    ):
        raise ValueError("M11N candidate-preparation authority identity differs")
    binding = subject.get("accepted_m11m_binding")
    authorizations = subject.get("authorizations")
    if binding != {
        "artifact_id": M11M_ARTIFACT_ID,
        "subject_sha256": M11M_SUBJECT_SHA256,
        "file_sha256": M11M_FILE_SHA256,
        "content_sha256": canonical_digest(candidate),
    }:
        raise ValueError("M11N preparation authority does not bind accepted M11M")
    if (
        subject.get("member_bioguide_id") != MEMBER_ID
        or subject.get("issue_id") != ISSUE_ID
        or subject.get("congress") != CONGRESS
        or subject.get("decision")
        != "approve_production_eligibility_and_publication_activation_candidate"
        or not isinstance(authorizations, dict)
        or authorizations.get("record_production_eligibility") is not True
        or authorizations.get("build_publication_activation_candidate") is not True
        or any(
            authorizations.get(key) is not False
            for key in (
                "production_database_write",
                "publication_registry_mutation",
                "publication_activation",
                "deployment",
            )
        )
    ):
        raise ValueError("M11N candidate-preparation authority boundary differs")


# Backwards-compatible name for the accepted candidate-preparation contract.
validate_publication_authority = validate_candidate_preparation_authority


def validate_positive_activation_authority(
    authority: dict[str, Any],
    *,
    candidate: dict[str, Any],
    candidate_authority: dict[str, Any],
    metadata: dict[str, Any],
    allow_test_authority: bool = False,
) -> None:
    """Validate the distinct sealed authority required for live selection."""

    validate_candidate_preparation_authority(candidate_authority, candidate=candidate)
    subject = authority.get("subject")
    synthetic = authority.get("test_only_synthetic") is True
    if synthetic and not allow_test_authority:
        raise ValueError("synthetic activation authority cannot publish")
    if (
        authority.get("schema_version") != ACTIVATION_AUTHORITY_SCHEMA_VERSION
        or authority.get("artifact_id") != ACTIVATION_AUTHORITY_ID
        or authority.get("immutable") is not True
        or authority.get("sealed") is not True
        or authority.get("accepted") is not True
        or not isinstance(subject, dict)
        or authority.get("activation_authority_subject_sha256")
        != canonical_digest(subject)
    ):
        raise ValueError("positive publication-activation authority is not sealed")
    expected_m11m = {
        "artifact_id": M11M_ARTIFACT_ID,
        "subject_sha256": M11M_SUBJECT_SHA256,
        "file_sha256": M11M_FILE_SHA256,
        "content_sha256": canonical_digest(candidate),
    }
    expected_candidate_authority = metadata.get(
        "candidate_preparation_authority_binding"
    )
    expected_write_set = metadata.get("activation_write_set_binding")
    expected_preflight = metadata.get("preflight_binding")
    expected_runtime = _object(metadata.get("reviewed_runtime_binding")) or {}
    expected_rollback = metadata.get("rollback_binding")
    expected_registry = {
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "presentation_natural_key": M11M_ARTIFACT_ID,
        "presentation_artifact_version": 1,
    }
    runtime = subject.get("runtime_binding")
    if (
        subject.get("decision") != "approve_exact_publication_activation"
        or not isinstance(subject.get("decision_recorded_at_utc"), str)
        or not subject["decision_recorded_at_utc"].strip()
        or subject.get("reviewer_authority") != ACTIVATION_REVIEWER_AUTHORITY
        or not isinstance(subject.get("reviewer"), str)
        or not subject["reviewer"].strip()
        or subject.get("product_owner") != "dhart54"
        or subject.get("member_bioguide_id") != MEMBER_ID
        or subject.get("issue_id") != ISSUE_ID
        or subject.get("congress") != CONGRESS
        or subject.get("accepted_m11m_binding") != expected_m11m
        or subject.get("candidate_preparation_authority_binding")
        != expected_candidate_authority
        or subject.get("activation_write_set_binding") != expected_write_set
        or subject.get("publication_registry_target") != expected_registry
        or subject.get("presentation_content_sha256")
        != metadata.get("active_artifact_sha256")
        or subject.get("preflight_binding") != expected_preflight
        or subject.get("rollback_binding") != expected_rollback
        or not isinstance(runtime, dict)
        or runtime.get("reviewed_runtime_manifest_sha256")
        != expected_runtime.get("reviewed_runtime_manifest_sha256")
        or runtime.get("reviewed_commit") != runtime.get("deployed_commit")
        or runtime.get("deployed_commit") != runtime.get("health_commit")
        or not SHA40.fullmatch(runtime.get("deployed_commit", ""))
        or not SHA256.fullmatch(runtime.get("health_proof_subject_sha256", ""))
        or subject.get("production_target_identity_sha256")
        != metadata.get("production_target_identity_sha256")
        or subject.get("authorizations") != POSITIVE_AUTHORIZATIONS
    ):
        raise ValueError("positive publication-activation authority binding differs")


def eligible_site_integration_candidate(
    row: dict[str, Any],
    *,
    member_bioguide_id: str,
    allow_test_authority: bool = False,
) -> dict[str, Any] | None:
    """Return the exact candidate only when both authority layers validate."""

    payload = _object(row.get("payload_jsonb", row.get("payload")))
    metadata = _object(row.get("publication_metadata_jsonb"))
    if payload is None or metadata is None:
        return None
    if payload.get("schema_version") != M11M_SCHEMA_VERSION:
        return None
    try:
        from .integration_candidate import validate_site_integration_candidate

        validate_site_integration_candidate(payload)
        preparation = _object(
            metadata.get("production_eligibility_publication_authority")
        )
        activation = _object(metadata.get("publication_activation_authority"))
        if preparation is None or activation is None:
            return None
        validate_candidate_preparation_authority(preparation, candidate=payload)
        validate_positive_activation_authority(
            activation,
            candidate=payload,
            candidate_authority=preparation,
            metadata=metadata,
            allow_test_authority=allow_test_authority,
        )
    except (KeyError, TypeError, ValueError):
        return None
    subject = payload["subject"]
    content_sha256 = canonical_digest(payload)
    if (
        row.get("member_bioguide_id") != member_bioguide_id
        or subject["member_bioguide_id"] != member_bioguide_id
        or subject.get("congress") != CONGRESS
        or row.get("issue_id") != subject["issue_id"]
        or row.get("publicly_active") is not True
        or row.get("deactivated_at") is not None
        or row.get("editorial_status") != "human_approved"
        or row.get("benchmark_status") != "gold_benchmark"
        or row.get("production_eligible") is not True
        or row.get("schema_version") != M11M_SCHEMA_VERSION
        or row.get("artifact_version") != 1
        or row.get("natural_key") != M11M_ARTIFACT_ID
        or not isinstance(row.get("content_sha256"), str)
        or not hmac.compare_digest(row["content_sha256"], content_sha256)
        or metadata.get("presentation_natural_key") != M11M_ARTIFACT_ID
        or metadata.get("presentation_artifact_version") != 1
        or metadata.get("accepted_m11m_subject_sha256") != M11M_SUBJECT_SHA256
        or metadata.get("accepted_m11m_file_sha256") != M11M_FILE_SHA256
        or metadata.get("active_artifact_sha256") != content_sha256
        or metadata.get("authority_subject_sha256")
        != preparation["authority_subject_sha256"]
        or metadata.get("activation_authority_subject_sha256")
        != activation["activation_authority_subject_sha256"]
    ):
        return None
    return payload


def active_site_integration_candidate(
    rows: Iterable[dict[str, Any]], *, member_bioguide_id: str, issue_id: str
) -> dict[str, Any] | None:
    matches = [
        candidate
        for row in rows
        if (
            candidate := eligible_site_integration_candidate(
                row, member_bioguide_id=member_bioguide_id
            )
        )
        is not None
        and candidate["subject"]["issue_id"] == issue_id
    ]
    return matches[0] if len(matches) == 1 else None


def select_site_integration_public(
    candidate: dict[str, Any],
    *,
    legislator_id: str,
    member_bioguide_id: str,
    scope: str,
) -> dict[str, Any]:
    """Project accepted bytes to public output without preview-only state."""

    from .integration_candidate import select_site_integration_preview

    projected = select_site_integration_preview(
        candidate,
        legislator_id=legislator_id,
        member_bioguide_id=member_bioguide_id,
        scope=scope,
    )
    result = copy.deepcopy(projected)
    for presentation in result["presentations"]:
        if (
            presentation["issue_id"] != ISSUE_ID
            or presentation["tier"] == "receipts_only"
        ):
            continue
        presentation["public_status_label"] = "Full issue interpretation available"
        presentation.get("review_state", {}).pop("candidate_preview", None)
    return result
