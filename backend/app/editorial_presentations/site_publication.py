"""Fail-closed publication adapter for an accepted site-integration artifact."""

from __future__ import annotations

import hmac
import json
from typing import Any, Iterable

from .compiler import canonical_digest

AUTHORITY_SCHEMA_VERSION = (
    "site_integration_production_eligibility_publication_authority_v1"
)
M11M_ARTIFACT_ID = "site-integration-candidate:f000477:national_security_foreign:119:v1"
M11M_SCHEMA_VERSION = "editorial_site_integration_candidate_v1"
M11M_FILE_SHA256 = "d2a7a65eb56f4be68b0d0477eeb8f75f793be5bbb458c86db13560b8eae35cc4"
M11M_SUBJECT_SHA256 = "c0fa5282f061c4d27c259968dd08b5f7a804fdbe60c4b8794714e0c9ad04c5df"


def _object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def validate_publication_authority(
    authority: dict[str, Any], *, candidate: dict[str, Any]
) -> None:
    subject = authority.get("subject")
    if (
        authority.get("schema_version") != AUTHORITY_SCHEMA_VERSION
        or authority.get("artifact_id")
        != "production-eligibility-publication-authority:f000477:national_security_foreign:119:v1"
        or authority.get("immutable") is not True
        or authority.get("accepted") is not True
        or not isinstance(subject, dict)
        or authority.get("authority_subject_sha256") != canonical_digest(subject)
    ):
        raise ValueError("M11N publication authority identity differs")
    binding = subject.get("accepted_m11m_binding")
    authorizations = subject.get("authorizations")
    if binding != {
        "artifact_id": M11M_ARTIFACT_ID,
        "subject_sha256": M11M_SUBJECT_SHA256,
        "file_sha256": M11M_FILE_SHA256,
        "content_sha256": canonical_digest(candidate),
    }:
        raise ValueError("M11N authority does not bind the accepted M11M artifact")
    if (
        subject.get("member_bioguide_id") != "F000477"
        or subject.get("issue_id") != "NATIONAL_SECURITY_FOREIGN"
        or subject.get("congress") != 119
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
        raise ValueError("M11N authority boundary differs")


def eligible_site_integration_candidate(
    row: dict[str, Any], *, member_bioguide_id: str
) -> dict[str, Any] | None:
    """Return the exact accepted candidate only when every registry gate binds."""

    payload = _object(row.get("payload_jsonb", row.get("payload")))
    metadata = _object(row.get("publication_metadata_jsonb"))
    if payload is None or metadata is None:
        return None
    if payload.get("schema_version") != M11M_SCHEMA_VERSION:
        return None
    try:
        from .integration_candidate import validate_site_integration_candidate

        validate_site_integration_candidate(payload)
        authority = _object(
            metadata.get("production_eligibility_publication_authority")
        )
        if authority is None:
            return None
        validate_publication_authority(authority, candidate=payload)
    except (KeyError, TypeError, ValueError):
        return None
    subject = payload["subject"]
    content_sha256 = canonical_digest(payload)
    if (
        row.get("member_bioguide_id") != member_bioguide_id
        or subject["member_bioguide_id"] != member_bioguide_id
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
        != authority["authority_subject_sha256"]
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
