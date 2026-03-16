from fastapi import APIRouter, HTTPException

from app.api.precomputed import get_position_response


router = APIRouter()


@router.get("/legislators/{legislator_id}/positions")
def get_legislator_positions(legislator_id: str) -> dict[str, object]:
    response = get_position_response(legislator_id=legislator_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return response
