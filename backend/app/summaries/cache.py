from dataclasses import dataclass
from datetime import datetime, timezone

from app.api.precomputed import get_drift_response, get_fingerprint_response, has_legislator


@dataclass(frozen=True)
class SummaryRecord:
    legislator_id: str
    window_end: str
    classification_version: str
    summary_text: str
    generation_method: str
    created_at: str


SUMMARY_CACHE: dict[tuple[str, str, str], SummaryRecord] = {}


def get_or_create_summary(*, legislator_id: str) -> SummaryRecord | None:
    if not has_legislator(legislator_id=legislator_id):
        return None

    fingerprint = get_fingerprint_response(legislator_id=legislator_id, comparison_party="ALL")
    drift = get_drift_response(legislator_id=legislator_id)
    if fingerprint is None or drift is None:
        return None

    cache_key = (
        legislator_id,
        str(fingerprint["window_end"]),
        str(fingerprint["classification_version"]),
    )
    cached = SUMMARY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    record = SummaryRecord(
        legislator_id=legislator_id,
        window_end=str(fingerprint["window_end"]),
        classification_version=str(fingerprint["classification_version"]),
        summary_text=build_fallback_summary(fingerprint=fingerprint, drift=drift),
        generation_method="deterministic_fallback",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    SUMMARY_CACHE[cache_key] = record
    return record


def build_fallback_summary(*, fingerprint: dict[str, object], drift: dict[str, object]) -> str:
    fingerprint_rows = list(fingerprint["fingerprint"])
    total_votes = int(fingerprint_rows[0]["total_votes"]) if fingerprint_rows else 0
    top_domains = sorted(
        fingerprint_rows,
        key=lambda row: (-float(row["vote_share"]), str(row["domain"])),
    )[:2]
    emphasis_text = ", ".join(
        f"{row['domain']} ({float(row['vote_share']):.0%})"
        for row in top_domains
        if float(row["vote_share"]) > 0
    )
    if not emphasis_text:
        emphasis_text = "no eligible issue domains"

    if bool(drift["insufficient_data"]):
        drift_text = "Drift is unavailable because the legislator has fewer than 20 eligible votes in the current 730-day window."
    else:
        drift_text = f"Drift for the current window is {float(drift['drift_value']):.2f}."

    return (
        f"This fingerprint is based on {total_votes} eligible votes in the current 730-day window. "
        f"The largest areas of vote emphasis are {emphasis_text}. "
        f"{drift_text}"
    )
