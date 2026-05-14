from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.precomputed import get_alignment_response


router = APIRouter()


class AlignmentRequest(BaseModel):
    preferences: dict[str, str] = Field(default_factory=dict)


@router.post("/legislators/{legislator_id}/alignment")
def get_legislator_alignment(
    legislator_id: str,
    request: AlignmentRequest,
) -> dict[str, object]:
    response = get_alignment_response(
        legislator_id=legislator_id,
        preferences=request.preferences,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return response
