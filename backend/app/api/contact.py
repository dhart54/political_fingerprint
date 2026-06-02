from fastapi import APIRouter, HTTPException

from app.api.precomputed import get_legislator_contact_response


router = APIRouter()


@router.get("/legislators/{legislator_id}/contact")
def get_legislator_contact(legislator_id: str) -> dict[str, object]:
    response = get_legislator_contact_response(legislator_id=legislator_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator contact not found")
    return response
