from datetime import date

from app.etl.compute import run_etl
from app.etl.congress_adapter import load_congress_sample_bundle
from app.etl.seed import build_seed_bundle


def test_load_congress_sample_bundle_normalizes_official_style_records() -> None:
    bundle = load_congress_sample_bundle()

    assert len(bundle.legislators) == 3
    assert bundle.legislators[0]["id"] == "leg_alex_morgan"
    assert len(bundle.bills) == 12
    assert bundle.roll_calls[0]["bill_ref"] == "bill_118_hr_101"
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_house_001"


def test_run_etl_supports_congress_sample_source() -> None:
    result = run_etl(source="congress_sample", as_of=date(2026, 3, 12))

    assert result.records_loaded == 48
    assert result.records_classified == 12
    assert result.fingerprints_computed == 24
    assert result.drift_scores_computed == 3


def test_build_seed_bundle_supports_congress_sample_source() -> None:
    bundle = build_seed_bundle(source="congress_sample", as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 3
    assert len(bundle.vote_classifications) == 12
    assert len(bundle.summaries) == 3
