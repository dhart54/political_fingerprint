from fastapi import APIRouter

from app.api.precomputed import search_legislators


router = APIRouter()


@router.get("/legislators/search")
def search_for_legislators(q: str = "") -> dict[str, object]:
    results = search_legislators(query=q)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
