import os

from fastapi import APIRouter, HTTPException

from app.api.precomputed import get_legislator_profile, search_legislators


router = APIRouter()


@router.get("/legislators/{legislator_id}/profile")
def legislator_profile(legislator_id: str) -> dict[str, object]:
    profile = get_legislator_profile(legislator_id=legislator_id)
    if (
        profile is None
        and os.getenv("EDITORIAL_PRESENTATION_PREVIEW") == "1"
        and legislator_id == "leg_valerie_p_foushee"
    ):
        profile = {
            "id": "leg_valerie_p_foushee",
            "bioguide_id": "F000477",
            "name_display": "Valerie P. Foushee",
            "chamber": "house",
            "state": "NC",
            "district": "04",
            "party": "D",
        }
    if profile is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return profile


@router.get("/legislators/search")
def search_for_legislators(q: str = "") -> dict[str, object]:
    results = search_legislators(query=q)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
