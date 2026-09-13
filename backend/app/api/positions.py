import os

from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import (
    get_governed_position_evidence_rows,
    get_legislator_profile,
    get_position_evidence_response,
    get_position_response,
)
from app.api.editorial_presentations import (
    M11M_CANDIDATE_PATH,
    M12M_CANDIDATE_PATH,
    M13M_CANDIDATE_PATH,
    _load_publication_rows,
)
from app.editorial_presentations.integration_candidate import (
    M11M_ARTIFACT_ID,
    M11M_PREVIEW_TOKEN,
    load_site_integration_candidate,
    merge_site_integration_preview_evidence,
    merge_site_integration_preview_positions,
    governed_position_summary,
)
from app.editorial_presentations.environment_integration_candidate import (
    M12M_ARTIFACT_ID,
    M12M_PREVIEW_TOKEN,
    load_environment_site_integration_candidate,
    merge_environment_preview_evidence,
    merge_environment_preview_positions,
)
from app.editorial_presentations.education_workforce_integration_candidate import (
    M13M_ARTIFACT_ID,
    M13M_PREVIEW_TOKEN,
    load_education_workforce_site_integration_candidate,
    merge_education_workforce_preview_evidence,
    merge_education_workforce_preview_positions,
)
from app.editorial_presentations.reviewed_record import index_actions, union_database_actions, GovernedReceiptProjectionError
from app.api.public_data import PublicDataUnavailable
from app.editorial_presentations.receipt_projection import (
    attach_governed_receipt_projections,
)
from app.editorial_presentations.review_state_catalog import (
    public_review_state_entries,
)
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_presentations.site_publication import (
    active_site_integration_candidate,
)


router = APIRouter()


def _m11m_preview(candidate: str | None) -> dict[str, object] | None:
    if not (
        candidate == M11M_PREVIEW_TOKEN
        and os.getenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW") == "1"
    ):
        return None
    try:
        return load_site_integration_candidate(M11M_CANDIDATE_PATH)
    except (OSError, KeyError, TypeError, ValueError):
        return None


def _m12m_preview(candidate: str | None) -> dict[str, object] | None:
    if not (
        candidate == M12M_PREVIEW_TOKEN
        and os.getenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW") == "1"
    ):
        return None
    try:
        return load_environment_site_integration_candidate(M12M_CANDIDATE_PATH)
    except (OSError, KeyError, TypeError, ValueError):
        return None


def _m13m_preview(candidate: str | None) -> dict[str, object] | None:
    if not (
        candidate == M13M_PREVIEW_TOKEN
        and os.getenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW") == "1"
    ):
        return None
    try:
        return load_education_workforce_site_integration_candidate(M13M_CANDIDATE_PATH)
    except (OSError, KeyError, TypeError, ValueError):
        return None


def _active_site_integration_publication(
    *,
    member_bioguide_id: str,
    issue_id: str,
    publication_rows: list[dict[str, object]] | None = None,
) -> dict[str, object] | None:
    rows = _load_publication_rows() if publication_rows is None else publication_rows
    return active_site_integration_candidate(
        rows, member_bioguide_id=member_bioguide_id, issue_id=issue_id
    )


def _merge_site_integration_evidence(
    base_response: dict[str, object],
    candidate: dict[str, object],
    *,
    domain: str,
    scope: str,
) -> dict[str, object]:
    artifact_id = candidate.get("artifact_id")
    if artifact_id == M11M_ARTIFACT_ID:
        return merge_site_integration_preview_evidence(
            base_response, candidate, domain=domain, scope=scope
        )
    if artifact_id == M12M_ARTIFACT_ID:
        return merge_environment_preview_evidence(
            base_response, candidate, domain=domain, scope=scope
        )
    if artifact_id == M13M_ARTIFACT_ID:
        return merge_education_workforce_preview_evidence(
            base_response, candidate, domain=domain, scope=scope
        )
    raise ValueError("unknown active site-integration candidate identity")


def _merge_site_integration_positions(
    base_response: dict[str, object],
    candidate: dict[str, object],
    *,
    governed_evidence: list[dict[str, object]],
) -> dict[str, object]:
    artifact_id = candidate.get("artifact_id")
    if artifact_id == M11M_ARTIFACT_ID:
        return merge_site_integration_preview_positions(
            base_response, governed_evidence=governed_evidence
        )
    if artifact_id == M12M_ARTIFACT_ID:
        return merge_environment_preview_positions(
            base_response, governed_evidence=governed_evidence
        )
    if artifact_id == M13M_ARTIFACT_ID:
        return merge_education_workforce_preview_positions(
            base_response, governed_evidence=governed_evidence
        )
    raise ValueError("unknown active site-integration candidate identity")


def _has_governed_presentation_candidate(
    *,
    member_bioguide_id: str,
    issue_id: str,
    scope: str,
) -> bool:
    requested_scope = scope.strip().lower()
    return any(
        entry["member_id"] == member_bioguide_id
        and entry["issue_id"] == issue_id
        and (
            requested_scope == "all"
            or (
                requested_scope.isdigit()
                and int(requested_scope) in entry["congress_scope"]
            )
        )
        for entry in public_review_state_entries()
    )


@router.get("/legislators/{legislator_id}/positions")
def get_legislator_positions(
    legislator_id: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
    candidate: str | None = Query(
        default=None,
        pattern="^(m11m-national-security|m12m-environment-energy|m13m-education-workforce)$",
    ),
) -> dict[str, object]:
    response = get_position_response(legislator_id=legislator_id, scope=scope)
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    profile = get_legislator_profile(legislator_id=legislator_id)
    if profile is None or not any(entry["member_id"] == str(profile["bioguide_id"]) for entry in public_review_state_entries()):
        return response

    publication_rows = _load_publication_rows()
    for row in response["positions"]:
        issue_id = row["domain"]
        if issue_id not in {"JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY_FOREIGN", "ENVIRONMENT_ENERGY", "EDUCATION_WORKFORCE"}:
            continue
        evidence = _compose_position_evidence(
            legislator_id, issue_id, scope, candidate, profile, publication_rows,
        )
        summary = governed_position_summary(evidence["evidence"], domain=issue_id)
        if issue_id == "JUSTICE_PUBLIC_SAFETY" or scope == "118":
            # These paths have no established site exact-choice effect accounting.
            summary = {key: value for key, value in summary.items() if not key.startswith("interpreted_")}
        row.update(summary)
        recorded = summary["recorded_votes"]
        row["yea_share"] = summary["yea_count"] / recorded if recorded else 0.0
        row["nay_share"] = summary["nay_count"] / recorded if recorded else 0.0
    return response


@router.get("/legislators/{legislator_id}/positions/{domain}/evidence")
def get_legislator_position_evidence(
    legislator_id: str,
    domain: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
    candidate: str | None = Query(
        default=None,
        pattern="^(m11m-national-security|m12m-environment-energy|m13m-education-workforce)$",
    ),
) -> dict[str, object]:
    normalized_scope = scope if isinstance(scope, str) else "all"
    profile = get_legislator_profile(legislator_id=legislator_id)
    return _compose_position_evidence(
        legislator_id, domain, normalized_scope, candidate, profile,
        _load_publication_rows() if profile and any(
            entry["member_id"] == str(profile["bioguide_id"]) for entry in public_review_state_entries()
        ) else [],
    )


def _compose_position_evidence(
    legislator_id: str,
    domain: str,
    normalized_scope: str,
    candidate: str | None,
    profile: dict[str, object] | None,
    publication_rows: list[dict[str, object]],
) -> dict[str, object]:
    response = get_position_evidence_response(
        legislator_id=legislator_id,
        domain=domain,
        scope=normalized_scope,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    normalized_domain = domain.strip().upper()
    active_site_candidate = (
        _active_site_integration_publication(
            member_bioguide_id=str(profile["bioguide_id"]),
            issue_id=normalized_domain,
            publication_rows=publication_rows,
        )
        if profile is not None
        else None
    )
    if active_site_candidate is None and profile is not None and _has_governed_presentation_candidate(
        member_bioguide_id=str(profile["bioguide_id"]),
        issue_id=normalized_domain,
        scope=normalized_scope,
    ):
        presentation_payload = select_public_presentations(
            publication_rows,
            legislator_id=legislator_id,
            member_bioguide_id=str(profile["bioguide_id"]),
            scope=normalized_scope,
        )
        presentation = next(
            (
                item
                for item in presentation_payload["presentations"]
                if item["issue_id"] == normalized_domain
            ),
            None,
        )
        if presentation is not None and presentation["tier"] != "receipts_only":
            governed_rows = get_governed_position_evidence_rows(
                legislator_id=legislator_id,
                canonical_action_ids=presentation["reviewed_action_ids"],
            )
            if governed_rows is None:
                raise PublicDataUnavailable()
            response = attach_governed_receipt_projections(
                response,
                presentation,
                governed_evidence=governed_rows,
            )
    preview = next(
        (
            item
            for item in (
                _m11m_preview(candidate),
                _m12m_preview(candidate),
                _m13m_preview(candidate),
            )
            if item is not None
            and item.get("subject", {}).get("issue_id") == normalized_domain
        ),
        None,
    )
    site_candidate = preview or active_site_candidate
    if (
        site_candidate is not None
        and profile is not None
        and str(profile["bioguide_id"]) == site_candidate["subject"]["member_bioguide_id"]
    ):
        if normalized_scope in {"119", "all"}:
            subject = site_candidate["subject"]
            reviewed = subject.get("receipt_projections") or subject["preview_data"]["evidence_119"]
            governed_rows = get_governed_position_evidence_rows(
                legislator_id=legislator_id,
                canonical_action_ids=[row["canonical_action_id"] for row in reviewed],
            )
            if governed_rows is None:
                raise PublicDataUnavailable()
            response["evidence"] = union_database_actions(response["evidence"], governed_rows)
            if not {row["canonical_action_id"] for row in reviewed}.issubset(index_actions(response["evidence"])):
                raise GovernedReceiptProjectionError("governed reviewed action is missing from the database ledger")
        response = _merge_site_integration_evidence(
            response,
            site_candidate,
            domain=normalized_domain,
            scope=normalized_scope,
        )
    return response
