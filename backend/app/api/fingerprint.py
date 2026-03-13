from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import get_fingerprint_response


router = APIRouter()


@router.get("/legislators/{legislator_id}/fingerprint")
def get_legislator_fingerprint(
    legislator_id: str,
    comparison_party: str = Query(default="ALL", pattern="^(ALL|D|R)$"),
) -> dict[str, object]:
    response = get_fingerprint_response(
        legislator_id=legislator_id,
        comparison_party=comparison_party,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return response
