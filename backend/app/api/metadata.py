from fastapi import APIRouter

from app.api.precomputed import get_coverage_metadata


router = APIRouter()


@router.get("/metadata/coverage")
def get_metadata_coverage() -> dict[str, object]:
    return get_coverage_metadata()


@router.get("/coverage/metadata")
def get_coverage_metadata_alias() -> dict[str, object]:
    return get_coverage_metadata()

