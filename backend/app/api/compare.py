from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import (
    get_drift_response,
    get_fingerprint_response,
    get_legislator_profile,
)
from app.summaries.cache import get_or_create_summary


router = APIRouter()


@router.get("/compare/legislators")
def compare_legislators(
    left_legislator_id: str = Query(...),
    right_legislator_id: str = Query(...),
    comparison_party: str = Query(default="ALL", pattern="^(ALL|D|R)$"),
) -> dict[str, object]:
    left = _build_comparison_side(
        legislator_id=left_legislator_id,
        comparison_party=comparison_party,
    )
    if left is None:
        raise HTTPException(status_code=404, detail="Left legislator not found")

    right = _build_comparison_side(
        legislator_id=right_legislator_id,
        comparison_party=comparison_party,
    )
    if right is None:
        raise HTTPException(status_code=404, detail="Right legislator not found")

    return {
        "comparison_party": comparison_party,
        "left": left,
        "right": right,
    }


def _build_comparison_side(*, legislator_id: str, comparison_party: str) -> dict[str, object] | None:
    profile = get_legislator_profile(legislator_id=legislator_id)
    fingerprint = get_fingerprint_response(
        legislator_id=legislator_id,
        comparison_party=comparison_party,
    )
    drift = get_drift_response(legislator_id=legislator_id)
    summary = get_or_create_summary(legislator_id=legislator_id)

    if profile is None or fingerprint is None or drift is None or summary is None:
        return None

    return {
        "legislator": profile,
        "fingerprint": fingerprint,
        "drift": drift,
        "summary": {
            "legislator_id": summary.legislator_id,
            "window_end": summary.window_end,
            "classification_version": summary.classification_version,
            "summary_text": summary.summary_text,
            "generation_method": summary.generation_method,
            "created_at": summary.created_at,
        },
    }
