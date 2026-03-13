from fastapi import APIRouter, HTTPException

from app.summaries.cache import get_or_create_summary


router = APIRouter()


@router.get("/legislators/{legislator_id}/summary")
def get_legislator_summary(legislator_id: str) -> dict[str, object]:
    summary = get_or_create_summary(legislator_id=legislator_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Legislator not found")

    return {
        "legislator_id": summary.legislator_id,
        "window_end": summary.window_end,
        "classification_version": summary.classification_version,
        "summary_text": summary.summary_text,
        "generation_method": summary.generation_method,
        "created_at": summary.created_at,
    }
