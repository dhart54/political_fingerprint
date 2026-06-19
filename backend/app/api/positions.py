from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import get_position_evidence_response, get_position_response


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
    return response
