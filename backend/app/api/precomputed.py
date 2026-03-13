from dataclasses import dataclass
from datetime import date

from app.etl.compute import ChamberMedianRecord, ComputeStepResult, run_etl
from app.metrics.fingerprint import FingerprintRecord


FIXTURE_AS_OF_DATE = date(2026, 3, 12)
PRECOMPUTED_DATA = run_etl(as_of=FIXTURE_AS_OF_DATE)


@dataclass(frozen=True)
class FingerprintResponseRow:
    domain: str
    vote_count: int
    total_votes: int
    vote_share: float
    median_share: float


def get_fingerprint_response(*, legislator_id: str, comparison_party: str = "ALL") -> dict[str, object] | None:
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


def _infer_legislator_chamber(legislator_id: str) -> str:
    if legislator_id == "leg_alex_morgan":
        return "house"
    if legislator_id in {"leg_jordan_lee", "leg_taylor_nguyen"}:
        return "senate"
    raise KeyError(f"Unknown legislator_id: {legislator_id}")
