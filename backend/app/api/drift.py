from fastapi import APIRouter, HTTPException

from app.api.precomputed import get_drift_response


router = APIRouter()


@router.get("/legislators/{legislator_id}/drift")
def get_legislator_drift(legislator_id: str) -> dict[str, object]:
    response = get_drift_response(legislator_id=legislator_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return response
