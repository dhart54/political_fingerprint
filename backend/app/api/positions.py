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
from app.editorial_presentations.selector import select_public_presentations


router = APIRouter()


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
    response = get_position_evidence_response(
        legislator_id=legislator_id,
        domain=domain,
        scope=scope,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    profile = get_legislator_profile(legislator_id=legislator_id)
    if profile is not None:
        presentation_payload = select_public_presentations(
            _load_publication_rows(),
            legislator_id=legislator_id,
            member_bioguide_id=str(profile["bioguide_id"]),
            scope=scope,
        )
        presentation = next(
            (
                item
                for item in presentation_payload["presentations"]
                if item["issue_id"] == domain.strip().upper()
            ),
            None,
        )
        if presentation is not None and presentation["tier"] != "receipts_only":
            response = attach_governed_receipt_projections(
                response,
                presentation,
            )
    return response
