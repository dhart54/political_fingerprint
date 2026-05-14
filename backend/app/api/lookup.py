from fastapi import APIRouter, HTTPException

from app.api.precomputed import get_supported_zip_responses, get_zip_lookup_response


router = APIRouter()


@router.get("/lookup/zip/{zip_code}")
def lookup_zip(zip_code: str) -> dict[str, object]:
    response = get_zip_lookup_response(zip_code=zip_code)
    if response is None:
        raise HTTPException(status_code=404, detail="ZIP code not found")
    return response


@router.get("/lookup/zips")
def list_supported_zips() -> dict[str, object]:
    return get_supported_zip_responses()
