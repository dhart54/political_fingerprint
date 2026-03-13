from datetime import date

from app.etl.classify import ClassificationStepResult, run_classification
from app.etl.compute import ComputeStepResult, run_compute, run_etl
from app.etl.ingest import FixtureBundle, IngestResult, run_ingest


def test_run_ingest_returns_fixture_bundle() -> None:
    ingest_result = run_ingest()

    assert isinstance(ingest_result, IngestResult)
    assert ingest_result.source == "fixtures"
    assert ingest_result.records_loaded == 52
    assert isinstance(ingest_result.fixtures, FixtureBundle)


def test_run_classification_uses_ingest_result() -> None:
    ingest_result = run_ingest()
    result = run_classification(ingest_result)

    assert isinstance(result, ClassificationStepResult)
    assert result.source == "fixtures"
    assert result.records_loaded == 52
    assert result.records_classified == 14
    assert len(result.classified_roll_calls) == 14


def test_run_compute_uses_classification_result() -> None:
    ingest_result = run_ingest()
    classification_result = run_classification(ingest_result)
    result = run_compute(classification_result, ingest_result, as_of=date(2026, 3, 12))

    assert isinstance(result, ComputeStepResult)
    assert result.records_loaded == 52
    assert result.records_classified == 14
    assert result.fingerprints_computed == 24
    assert result.chamber_medians_computed == 48
    assert result.drift_scores_computed == 3


def test_run_etl_executes_without_errors() -> None:
    result = run_etl(source="fixtures", as_of=date(2026, 3, 12))

    assert isinstance(result, ComputeStepResult)
    assert result.records_loaded == 52
    assert result.records_classified == 14


def test_run_ingest_supports_congress_sample_source() -> None:
    ingest_result = run_ingest(source="congress_sample")

    assert isinstance(ingest_result, IngestResult)
    assert ingest_result.source == "congress_sample"
    assert ingest_result.records_loaded == 48
    assert isinstance(ingest_result.fixtures, FixtureBundle)


def test_run_ingest_supports_house_clerk_sample_source() -> None:
    ingest_result = run_ingest(source="house_clerk_sample")

    assert isinstance(ingest_result, IngestResult)
    assert ingest_result.source == "house_clerk_sample"
    assert ingest_result.records_loaded == 26
    assert isinstance(ingest_result.fixtures, FixtureBundle)


def test_run_ingest_supports_senate_xml_sample_source() -> None:
    ingest_result = run_ingest(source="senate_xml_sample")

    assert isinstance(ingest_result, IngestResult)
    assert ingest_result.source == "senate_xml_sample"
    assert ingest_result.records_loaded == 20
    assert isinstance(ingest_result.fixtures, FixtureBundle)
