from app.etl.classify import ClassificationStepResult, run_classification
from app.etl.compute import ComputeStepResult, run_compute, run_etl
from app.etl.ingest import IngestResult, run_ingest


def test_run_ingest_returns_deterministic_empty_result() -> None:
    assert run_ingest() == IngestResult(
        source="fixtures",
        records_loaded=0,
    )


def test_run_classification_uses_ingest_result() -> None:
    ingest_result = IngestResult(source="fixtures", records_loaded=12)

    assert run_classification(ingest_result) == ClassificationStepResult(
        source="fixtures",
        records_loaded=12,
        records_classified=0,
    )


def test_run_compute_uses_classification_result() -> None:
    classification_result = ClassificationStepResult(
        source="fixtures",
        records_loaded=12,
        records_classified=9,
    )

    assert run_compute(classification_result) == ComputeStepResult(
        source="fixtures",
        records_loaded=12,
        records_classified=9,
        fingerprints_computed=0,
        chamber_medians_computed=0,
        drift_scores_computed=0,
    )


def test_run_etl_executes_without_errors() -> None:
    assert run_etl(source="fixtures") == ComputeStepResult(
        source="fixtures",
        records_loaded=0,
        records_classified=0,
        fingerprints_computed=0,
        chamber_medians_computed=0,
        drift_scores_computed=0,
    )
