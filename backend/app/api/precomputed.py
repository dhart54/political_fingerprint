from dataclasses import dataclass
from datetime import date

from app.etl.compute import run_etl


FIXTURE_AS_OF_DATE = date(2026, 3, 12)
PRECOMPUTED_DATA = run_etl(as_of=FIXTURE_AS_OF_DATE)
LEGISLATOR_CHAMBERS = {
    "leg_alex_morgan": "house",
    "leg_jordan_lee": "senate",
    "leg_taylor_nguyen": "senate",
}


@dataclass(frozen=True)
class FingerprintResponseRow:
    domain: str
    vote_count: int
    total_votes: int
    vote_share: float
    median_share: float


def has_legislator(*, legislator_id: str) -> bool:
    return legislator_id in LEGISLATOR_CHAMBERS


def get_fingerprint_response(*, legislator_id: str, comparison_party: str = "ALL") -> dict[str, object] | None:
    if not has_legislator(legislator_id=legislator_id):
        return None

    fingerprint_rows = [
        row
        for row in PRECOMPUTED_DATA.fingerprint_records
        if row.legislator_id == legislator_id
    ]
    if not fingerprint_rows:
        return None

    chamber = _infer_legislator_chamber(legislator_id)
    median_map = {
        median_record.domain: median_record
        for median_record in PRECOMPUTED_DATA.chamber_medians
        if median_record.chamber == chamber and median_record.party == comparison_party
    }

    first_row = fingerprint_rows[0]
    return {
        "legislator_id": legislator_id,
        "window_start": first_row.window_start.isoformat(),
        "window_end": first_row.window_end.isoformat(),
        "classification_version": first_row.classification_version,
        "comparison_party": comparison_party,
        "fingerprint": [
            FingerprintResponseRow(
                domain=row.domain,
                vote_count=row.vote_count,
                total_votes=row.total_votes,
                vote_share=row.vote_share,
                median_share=median_map[row.domain].median_share if row.domain in median_map else 0.0,
            ).__dict__
            for row in fingerprint_rows
        ],
    }


def get_drift_response(*, legislator_id: str) -> dict[str, object] | None:
    if not has_legislator(legislator_id=legislator_id):
        return None

    drift_row = next(
        (row for row in PRECOMPUTED_DATA.drift_results if row.legislator_id == legislator_id),
        None,
    )
    if drift_row is None:
        return None

    return {
        "legislator_id": legislator_id,
        "window_start": drift_row.window_start.isoformat(),
        "window_end": drift_row.window_end.isoformat(),
        "early_window_start": drift_row.early_window_start.isoformat(),
        "early_window_end": drift_row.early_window_end.isoformat(),
        "recent_window_start": drift_row.recent_window_start.isoformat(),
        "recent_window_end": drift_row.recent_window_end.isoformat(),
        "classification_version": drift_row.classification_version,
        "total_votes": drift_row.total_votes,
        "early_total_votes": drift_row.early_total_votes,
        "recent_total_votes": drift_row.recent_total_votes,
        "insufficient_data": drift_row.insufficient_data,
        "drift_value": drift_row.drift_value,
    }


def _infer_legislator_chamber(legislator_id: str) -> str:
    if legislator_id not in LEGISLATOR_CHAMBERS:
        raise KeyError(f"Unknown legislator_id: {legislator_id}")
    return LEGISLATOR_CHAMBERS[legislator_id]
