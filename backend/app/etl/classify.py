from dataclasses import dataclass

from app.etl.ingest import IngestResult


@dataclass(frozen=True)
class ClassificationStepResult:
    source: str
    records_loaded: int
    records_classified: int


def run_classification(ingest_result: IngestResult) -> ClassificationStepResult:
    return ClassificationStepResult(
        source=ingest_result.source,
        records_loaded=ingest_result.records_loaded,
        records_classified=0,
    )
