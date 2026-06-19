from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.precomputed import get_alignment_response


router = APIRouter()


class AlignmentRequest(BaseModel):
    preferences: dict[str, str] = Field(default_factory=dict)


@router.post("/legislators/{legislator_id}/alignment")
def get_legislator_alignment(
    legislator_id: str,
    request: AlignmentRequest,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
) -> dict[str, object]:
    response = get_alignment_response(
        legislator_id=legislator_id,
        preferences=request.preferences,
        scope=scope,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return response
