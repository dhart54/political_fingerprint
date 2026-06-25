from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.analysis.house_comparable_family_legislator import HouseComparableFamilyLegislatorError
from app.analysis.house_record_across_congresses_transport import (
    build_internal_house_record_across_congresses_response,
)
from app.internal_auth import require_internal_api_token


router = APIRouter(
    prefix="/internal/record-across-congresses",
    tags=["internal"],
    include_in_schema=False,
)


@router.get(
    "/house/{legislator_identifier}",
    include_in_schema=False,
    dependencies=[Depends(require_internal_api_token)],
)
def get_internal_house_record_across_congresses(legislator_identifier: str) -> dict:
    try:
        return build_internal_house_record_across_congresses_response(legislator_identifier)
    except HouseComparableFamilyLegislatorError as exc:
        raise HTTPException(status_code=404, detail="Record unavailable") from exc
