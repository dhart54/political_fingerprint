from datetime import date

from app.etl.compute import run_etl
from app.etl.seed import build_seed_bundle
from app.etl.senate_xml_adapter import load_senate_xml_sample_bundle


def test_load_senate_xml_sample_bundle_normalizes_senate_xml() -> None:
    bundle = load_senate_xml_sample_bundle()

    assert len(bundle.legislators) == 2
    assert bundle.legislators[0]["id"] == "leg_jordan_lee"
    assert len(bundle.bills) == 4
    assert bundle.roll_calls[0]["bill_ref"] == "bill_119_s_210"
    assert bundle.bills[0]["committee"] == "Homeland Security and Governmental Affairs"
    assert bundle.vote_subject_tags["bill_119_s_210"] == ["immigration", "border security", "visas"]
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_senate_001"
    assert bundle.votes_cast[1]["position"] == "nay"


def test_run_etl_supports_senate_xml_sample_source() -> None:
    result = run_etl(source="senate_xml_sample", as_of=date(2026, 3, 12))

    assert result.records_loaded == 20
    assert result.records_classified == 4
    assert result.fingerprints_computed == 16
    assert result.drift_scores_computed == 2


def test_build_seed_bundle_supports_senate_xml_sample_source() -> None:
    bundle = build_seed_bundle(source="senate_xml_sample", as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 2
    assert len(bundle.vote_classifications) == 4
    assert len(bundle.summaries) == 2
