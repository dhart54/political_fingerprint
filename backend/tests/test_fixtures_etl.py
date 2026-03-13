from datetime import date
from app.etl.classify import run_classification
from app.etl.compute import run_etl
from app.etl.ingest import FIXTURES_DIR, load_fixture_bundle, run_ingest


def test_fixture_files_exist() -> None:
    expected_files = {
        "legislators.json",
        "bills.json",
        "roll_calls.json",
        "votes_cast.json",
        "vote_subject_tags.json",
        "zip_district_map.json",
    }

    assert expected_files.issubset({path.name for path in FIXTURES_DIR.iterdir() if path.is_file()})


def test_fixture_counts_match_prioritized_roll_call_plan() -> None:
    fixtures = load_fixture_bundle()

    assert len(fixtures.legislators) == 3
    assert len(fixtures.bills) == 12
    assert len(fixtures.roll_calls) == 14
    assert len(fixtures.zip_district_map) == 2


def test_fixture_classification_marks_procedural_and_low_confidence_roll_calls_ineligible() -> None:
    ingest_result = run_ingest()
    classification_result = run_classification(ingest_result)
    classified_roll_calls = {item.roll_call_id: item for item in classification_result.classified_roll_calls}

    assert classified_roll_calls["rc_senate_006"].is_eligible is False
    assert classified_roll_calls["rc_senate_006"].eligibility_reason == "procedural_vote"
    assert classified_roll_calls["rc_house_006"].is_eligible is False
    assert classified_roll_calls["rc_house_006"].eligibility_reason == "procedural_vote"
    assert classified_roll_calls["rc_house_007"].is_eligible is False
    assert classified_roll_calls["rc_house_007"].eligibility_reason == "low_classification_confidence"
    assert classified_roll_calls["rc_senate_007"].is_eligible is False
    assert classified_roll_calls["rc_senate_007"].eligibility_reason == "low_classification_confidence"


def test_fixture_classification_prioritizes_ten_policy_roll_calls_with_all_domains_covered() -> None:
    ingest_result = run_ingest()
    classification_result = run_classification(ingest_result)

    eligible_roll_calls = [
        item
        for item in classification_result.classified_roll_calls
        if item.is_eligible and item.primary_domain is not None
    ]

    assert len(eligible_roll_calls) == 10
    assert {item.primary_domain for item in eligible_roll_calls} == {
        "ECONOMY_TAXES",
        "HEALTH_SOCIAL",
        "EDUCATION_WORKFORCE",
        "ENVIRONMENT_ENERGY",
        "NATIONAL_SECURITY_FOREIGN",
        "IMMIGRATION_BORDER",
        "JUSTICE_PUBLIC_SAFETY",
        "INFRASTRUCTURE_TECH_TRANSPORT",
    }


def test_fixture_etl_computes_expected_outputs_under_ten_policy_roll_calls() -> None:
    result = run_etl(as_of=date(2026, 3, 12))

    assert result.records_loaded == 52
    assert result.records_classified == 14
    assert result.fingerprints_computed == 24
    assert result.chamber_medians_computed == 48
    assert result.drift_scores_computed == 3

    alex_records = [record for record in result.fingerprint_records if record.legislator_id == "leg_alex_morgan"]
    alex_by_domain = {record.domain: record for record in alex_records}
    assert alex_by_domain["HEALTH_SOCIAL"].vote_count == 0
    assert alex_by_domain["HEALTH_SOCIAL"].vote_share == 0.0
    assert alex_by_domain["ENVIRONMENT_ENERGY"].vote_count == 0
    assert alex_by_domain["ENVIRONMENT_ENERGY"].vote_share == 0.0

    drift_by_legislator = {record.legislator_id: record for record in result.drift_results}
    assert drift_by_legislator["leg_alex_morgan"].insufficient_data is True
    assert drift_by_legislator["leg_jordan_lee"].insufficient_data is True
    assert drift_by_legislator["leg_taylor_nguyen"].insufficient_data is True
