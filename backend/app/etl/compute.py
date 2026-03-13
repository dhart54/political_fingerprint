from dataclasses import dataclass

from app.etl.classify import ClassificationStepResult, run_classification
from app.etl.ingest import IngestResult, run_ingest


@dataclass(frozen=True)
class ComputeStepResult:
    source: str
    records_loaded: int
    records_classified: int
    fingerprints_computed: int
    chamber_medians_computed: int
    drift_scores_computed: int


def run_compute(classification_result: ClassificationStepResult) -> ComputeStepResult:
    return ComputeStepResult(
        source=classification_result.source,
        records_loaded=classification_result.records_loaded,
        records_classified=classification_result.records_classified,
        fingerprints_computed=0,
        chamber_medians_computed=0,
        drift_scores_computed=0,
    )


def run_etl(*, source: str = "fixtures") -> ComputeStepResult:
    ingest_result: IngestResult = run_ingest(source=source)
    classification_result = run_classification(ingest_result)
    return run_compute(classification_result)


if __name__ == "__main__":
    result = run_etl()
    print(result)
