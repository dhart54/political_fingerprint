from datetime import date

from app.etl.compute import run_etl
from app.etl.house_clerk_adapter import load_house_clerk_sample_bundle
from app.etl.seed import build_seed_bundle


def test_load_house_clerk_sample_bundle_normalizes_house_clerk_xml() -> None:
    bundle = load_house_clerk_sample_bundle()

    assert len(bundle.legislators) == 3
    assert bundle.legislators[0]["id"] == "leg_alex_morgan"
    assert len(bundle.bills) == 4
    assert bundle.roll_calls[0]["bill_ref"] == "bill_119_hr_120"
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_house_001"
    assert bundle.votes_cast[1]["position"] == "nay"


def test_run_etl_supports_house_clerk_sample_source() -> None:
    result = run_etl(source="house_clerk_sample", as_of=date(2026, 3, 12))

    assert result.records_loaded == 26
    assert result.records_classified == 4
    assert result.fingerprints_computed == 24
    assert result.drift_scores_computed == 3


def test_build_seed_bundle_supports_house_clerk_sample_source() -> None:
    bundle = build_seed_bundle(source="house_clerk_sample", as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 3
    assert len(bundle.vote_classifications) == 4
    assert len(bundle.summaries) == 3
