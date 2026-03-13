from dataclasses import dataclass


@dataclass(frozen=True)
class IngestResult:
    source: str
    records_loaded: int


def run_ingest(*, source: str = "fixtures") -> IngestResult:
    return IngestResult(
        source=source,
        records_loaded=0,
    )
