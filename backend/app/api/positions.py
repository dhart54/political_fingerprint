import os

from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import (
    get_governed_position_evidence_rows,
    get_legislator_profile,
    get_position_evidence_response,
    get_position_response,
)
from app.api.editorial_presentations import M11M_CANDIDATE_PATH, _load_publication_rows
from app.editorial_presentations.integration_candidate import (
    M11M_PREVIEW_TOKEN,
    load_site_integration_candidate,
    merge_site_integration_preview_evidence,
    merge_site_integration_preview_positions,
)
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


def _active_m11m_publication(
    *, member_bioguide_id: str, issue_id: str
) -> dict[str, object] | None:
    try:
        rows = _load_publication_rows()
    except Exception:  # pragma: no cover - database availability stays fail-closed
        return None
    return active_site_integration_candidate(
        rows, member_bioguide_id=member_bioguide_id, issue_id=issue_id
    )


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
    candidate: str | None = Query(default=None, pattern="^m11m-national-security$"),
) -> dict[str, object]:
    response = get_position_response(legislator_id=legislator_id, scope=scope)
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    profile = get_legislator_profile(legislator_id=legislator_id)
    preview = _m11m_preview(candidate)
    if preview is None and profile is not None:
        preview = _active_m11m_publication(
            member_bioguide_id=str(profile["bioguide_id"]),
            issue_id="NATIONAL_SECURITY_FOREIGN",
        )
    if (
        preview is not None
        and profile is not None
        and str(profile["bioguide_id"]) == "F000477"
        and scope in {"119", "all"}
    ):
        raw_evidence = get_position_evidence_response(
            legislator_id=legislator_id,
            domain="NATIONAL_SECURITY_FOREIGN",
            scope=scope,
        ) or {"domain": "NATIONAL_SECURITY_FOREIGN", "evidence": []}
        governed = merge_site_integration_preview_evidence(
            raw_evidence,
            preview,
            domain="NATIONAL_SECURITY_FOREIGN",
            scope=scope,
        )
        return merge_site_integration_preview_positions(
            response,
            governed_evidence=governed["evidence"],
        )
    return response


@router.get("/legislators/{legislator_id}/positions/{domain}/evidence")
def get_legislator_position_evidence(
    legislator_id: str,
    domain: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
    candidate: str | None = Query(default=None, pattern="^m11m-national-security$"),
) -> dict[str, object]:
    normalized_scope = scope if isinstance(scope, str) else "all"
    response = get_position_evidence_response(
        legislator_id=legislator_id,
        domain=domain,
        scope=normalized_scope,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    profile = get_legislator_profile(legislator_id=legislator_id)
    normalized_domain = domain.strip().upper()
    active_site_candidate = (
        _active_m11m_publication(
            member_bioguide_id=str(profile["bioguide_id"]),
            issue_id=normalized_domain,
        )
        if profile is not None
        else None
    )
    if profile is not None and _has_governed_presentation_candidate(
        member_bioguide_id=str(profile["bioguide_id"]),
        issue_id=normalized_domain,
        scope=normalized_scope,
    ):
        presentation_payload = select_public_presentations(
            _load_publication_rows(),
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
                raise RuntimeError("governed raw evidence query failed")
            response = attach_governed_receipt_projections(
                response,
                presentation,
                governed_evidence=governed_rows,
            )
    preview = _m11m_preview(candidate) or active_site_candidate
    if (
        preview is not None
        and profile is not None
        and str(profile["bioguide_id"]) == "F000477"
    ):
        response = merge_site_integration_preview_evidence(
            response,
            preview,
            domain=normalized_domain,
            scope=normalized_scope,
        )
    return response
