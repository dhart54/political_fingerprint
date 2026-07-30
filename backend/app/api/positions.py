from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import (
    get_legislator_profile,
    get_position_evidence_response,
    get_position_response,
)
from app.api.editorial_presentations import _load_publication_rows
from app.editorial_presentations.receipt_projection import (
    attach_governed_receipt_projections,
)
from app.editorial_presentations.review_state_catalog import (
    public_review_state_entries,
)
from app.editorial_presentations.selector import select_public_presentations


router = APIRouter()


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
) -> dict[str, object]:
    response = get_position_response(legislator_id=legislator_id, scope=scope)
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return response


@router.get("/legislators/{legislator_id}/positions/{domain}/evidence")
def get_legislator_position_evidence(
    legislator_id: str,
    domain: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
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
            response = attach_governed_receipt_projections(
                response,
                presentation,
            )
    return response
